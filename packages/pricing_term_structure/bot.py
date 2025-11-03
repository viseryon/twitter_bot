import asyncio
import json
import os
import re
from collections.abc import Iterable
from datetime import datetime
from io import StringIO
from itertools import product
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import QuantLib as ql
from aiolimiter import AsyncLimiter
from matplotlib import pyplot as plt
from mylogging import setup
from pyacm import NominalACM
from QuantLib import YieldTermStructureHandle
from scipy.optimize import minimize
from twitter_bot_base import TwitterBot

logger = setup(__name__, __file__)

os.chdir(Path(__file__).parent)

plt.style.use("dark_background")


class NSShelper:
    def __init__(self):
        self.calendar = ql.Poland()
        self.day_counter = ql.ActualActual(ql.ActualActual.ISDA)
        self.settlement_days = 2

    def build_zero_curve_from_bonds(
        self,
        bonds: pd.DataFrame,
        eval_date: datetime,
        curve_cls=ql.PiecewiseCubicZero,
    ) -> YieldTermStructureHandle:
        eval_date_ql = ql.Date(eval_date.day, eval_date.month, eval_date.year)

        ql.Settings.instance().evaluationDate = eval_date_ql

        helpers = []
        for _, (price, coupon, maturity, start) in bonds.iterrows():
            start = ql.Date(start.day, start.month, start.year)
            maturity = ql.Date(maturity.day, maturity.month, maturity.year)

            schedule = ql.MakeSchedule(
                start,
                maturity,
                ql.Period(ql.Annual),
                calendar=self.calendar,
                convention=ql.ModifiedFollowing,
                terminalDateConvention=ql.ModifiedFollowing,
                rule=ql.DateGeneration.Backward,
                endOfMonth=False,
            )

            quote = ql.QuoteHandle(ql.SimpleQuote(price))
            helper = ql.FixedRateBondHelper(
                quote,
                self.settlement_days,
                100.0,
                schedule,
                [coupon],
                self.day_counter,
                ql.Following,
                100.0,
                start,
            )
            helpers.append(helper)

        curve = curve_cls(eval_date_ql, helpers, self.day_counter)
        return ql.YieldTermStructureHandle(curve)

    def get_zero_rates_from_curve(
        self,
        curve: YieldTermStructureHandle,
        eval_date: datetime,
        periods=(0, 1, 2, 3, 6, 12, 24, 36, 60, 84, 120, 180),
    ):
        eval_date_ql = ql.Date(eval_date.day, eval_date.month, eval_date.year)
        rates = []
        for period in periods:
            moved_date = eval_date_ql + ql.Period(period, ql.Months)
            try:
                rate = curve.zeroRate(moved_date, ql.ActualActual(ql.ActualActual.ISMA), ql.Continuous)
            except Exception:
                logger.debug(
                    "failed to calculate zero-rate",
                    extra={"eval_date": eval_date.isoformat(), "period": period},
                )
            else:
                rates.append((rate.rate(), eval_date, moved_date.to_date(), period))

        return rates

    @staticmethod
    def nss(params, periods):
        beta0, beta1, beta2, beta3, tau1, tau2 = params

        return (
            (beta0)
            + (beta1 * (-np.expm1(-periods / tau1) / (periods / tau1)))
            + (beta2 * (-(np.expm1(-periods / tau1) / (periods / tau1)) - (np.exp(-periods / tau1))))
            + (beta3 * (-(np.expm1(-periods / tau2) / (periods / tau2)) - (np.exp(-periods / tau2))))
        )

    @staticmethod
    def objective_function(initial_guess, df):
        nss_ = NSShelper.nss(initial_guess, df.period)
        return ((df.rate - nss_) ** 2).sum()

    def calculate_zero_rates(self, data, dates):
        rates = []

        for eval_date in dates:
            bonds = data.loc[eval_date, ["fix_price", "Kupon", "Data wykupu", "Początek okresu"]]
            curve = self.build_zero_curve_from_bonds(bonds, eval_date)

            rate = self.get_zero_rates_from_curve(curve, eval_date)
            rates.extend(rate)

        zero_rates = (
            pd.DataFrame(rates, columns=["rate", "eval_date", "future_date", "period"])
            .drop_duplicates()
            .astype({"future_date": "datetime64[ns]"})
            .set_index(["eval_date", "future_date"])
            .sort_index()
        )

        return zero_rates

    def calculate_params(self, zero_rates, dates):
        vals = []

        for idx in dates:
            df = zero_rates.loc[idx]
            c = minimize(
                fun=self.objective_function,
                x0=[0.01, 0.01, 0.01, 0.01, 1.00, 1.00],
                args=(df,),
            )
            vals.append(c)

        params = pd.DataFrame(
            [val.x for val in vals],
            columns=["beta0", "beta1", "beta2", "beta3", "tau1", "tau2"],
            index=dates,
        )
        return params

    def calculate_all(self, data, dates):
        zero_rates = self.calculate_zero_rates(data, dates)
        params = self.calculate_params(zero_rates, dates)

        months = np.arange(1, 181)

        curves = params.apply(self.nss, args=(months,), axis="columns", result_type="expand")
        curves.columns = [str(month) for month in months]

        full = params.join(curves)
        return full


class TermStructureBot(TwitterBot):
    BONDSPOT_LINK = "https://www.bondspot.pl/fixing_obligacji"
    REQUESTS_MAX_RATE = 5
    FIGSIZE = (16, 9)
    FONTNAME = "FiraCode Nerd Font"
    TITLE_FONT_SIZE = 24
    SUBTITLE_FONT_SIZE = 14

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.interest_calendar: pd.DataFrame | None = None
        self.bond_prices: pd.DataFrame | None = None
        self.nss_curve: pd.DataFrame | None = None

        with Path("config", "request_header.json").open(encoding="utf-8") as f:
            self._request_headers = json.load(f)

    def update_interest_calendar(self) -> pd.DataFrame:
        resp = httpx.get("https://www.gov.pl/web/finanse/kupony")

        hash_ = re.search(r'href="/attachment/([\w-]+)"', resp.text).groups()[0]
        url = f"https://www.gov.pl/attachment/{hash_}"

        bond_cal = (
            pd.read_excel(
                url,
                header=[0, 1],
                sheet_name="ObligacjeStałoprocentowe",
            )
            .rename(
                columns={
                    "Unnamed: 0_level_0": "Info",
                    "Unnamed: 1_level_0": "Info",
                    "Unnamed: 2_level_0": "Info",
                    "Unnamed: 3_level_0": "Info",
                },
            )
            .replace({"-": pd.NA})
        )

        info = bond_cal.Info  # loc[:, ["Info"]].stack(level=0, future_stack=True).reset_index(1, drop=True)
        calendar = (
            bond_cal.loc[:, [f"Kupon Nr {num}" for num in range(1, 32)]]
            .stack(level=0, future_stack=True)
            .reset_index(1)
            .rename(columns={"level_1": "Numer okresu"})
        )

        df = info.join(calendar).dropna(how="any")
        df["Numer okresu"] = df["Numer okresu"].str[9:]
        df = df.astype({
            "Początek okresu": "datetime64[ns]",
            "Koniec okresu": "datetime64[ns]",
            "Dzień ustalenia praw": "datetime64[ns]",
            "Data wymagalności": "datetime64[ns]",
            "Odsetki (PLN)": "float64",
            "Numer okresu": "int16",
            "Kod ISIN": "string",
            "Seria": "string",
        })

        path = Path("data", "interest_calendar.parquet")
        df.to_parquet(path, index=False)

        self.interest_calendar = df

        return df

    async def _make_request_to_bondspot(
        self,
        client: httpx.AsyncClient,
        date: str,
        fixing: int,
        limiter: AsyncLimiter,
    ) -> httpx.Response:
        async with limiter:
            params = {"date": date, "type": fixing}
            logger.info("making request to bondspot", extra=params)
            return await client.get(
                self.BONDSPOT_LINK,
                params=params,
                headers=self._request_headers,
            )

    async def get_bond_prices_data(
        self,
        start_date: str | datetime = "2000-01-01",
        end_date: str | datetime | None = None,
    ) -> list[httpx.Response]:
        if end_date is None:
            end_date = datetime.today()

        dates = [date.strftime("%Y%m%d") for date in pd.date_range(start_date, end_date, freq="B")]

        if not dates:
            return []

        limiter = AsyncLimiter(max_rate=self.REQUESTS_MAX_RATE, time_period=1)
        async with (
            httpx.AsyncClient(timeout=60.0) as client,
            asyncio.TaskGroup() as tg,
        ):
            tasks = [
                tg.create_task(
                    self._make_request_to_bondspot(
                        client=client,
                        date=date,
                        fixing=fixing,
                        limiter=limiter,
                    ),
                )
                for date, fixing in product(dates, (1, 2))
            ]

        return [task.result() for task in tasks]

    def _filter_dfs(self, results: list[httpx.Response]) -> list[pd.DataFrame]:
        dfs = []
        for result in results:
            html = result.text
            params = result.url.params
            date = params["date"]
            fixing = params["type"]
            try:
                df = pd.read_html(StringIO(html))[2]
            except Exception:
                logger.exception("bad response", extra={"date": date, "fixing": fixing})
            else:
                df["date"] = date
                df["fixing"] = fixing
                dfs.append(df)
        return dfs

    def update_bond_prices(self) -> None:
        current_data = pd.read_parquet(Path("data", "bond_prices.parquet"))
        last_request_date = current_data.Date.max().date() + pd.offsets.BDay(1)

        coroutine = self.get_bond_prices_data(start_date=last_request_date)
        results = asyncio.run(coroutine)
        new_data = self._filter_dfs(results)

        if not new_data:
            logger.warning("no new bond prices data was downloaded")
            self.bond_prices = current_data
            return

        new_data = pd.concat(new_data)

        with Path("config", "column_renames.json").open(encoding="utf-8") as f:
            column_renames = json.load(f)

        with Path("config", "column_types.json").open(encoding="utf-8") as f:
            column_types = json.load(f)

        new_data = (
            new_data.replace({"-": pd.NA, "KURS NIEOKREŚLONY": pd.NA})
            .rename(
                column_renames,
                axis=1,
            )
            .astype(column_types)
        )
        new_data = new_data.drop(columns=new_data.columns.difference(column_types.keys()))

        data = pd.concat([current_data, new_data])
        data.to_parquet(Path("data", "bond_prices.parquet"), index=False)
        self.bond_prices = data

    def update_nss_curve(self) -> pd.DataFrame:
        logger.info("preparing bond prices data for nss")
        interest_calendar = pd.read_parquet(
            Path("data", "interest_calendar.parquet"),
            columns=["Seria", "Kod ISIN", "Koniec okresu", "Początek okresu", "Kupon", "Data wykupu"],
        )
        ceny_rentownosci = pd.read_parquet(
            Path("data", "bond_prices.parquet"),
            columns=["Seria", "Kod ISIN", "Fixing", "fix_price", "Date"],
        )

        data = ceny_rentownosci.merge(interest_calendar, on=["Seria", "Kod ISIN"])
        data = data.loc[(data["Koniec okresu"] >= data.Date) & (data.Date > data["Początek okresu"])]
        data = (
            data.set_index(["Seria", "Date", "Fixing"])
            .sort_index(ascending=True)
            .ffill()
            .reset_index(level="Fixing")
            .ffill()
            .reset_index()
            .drop_duplicates(subset=["Seria", "Date"], keep="last")
            .set_index(["Date", "Seria"])
            .sort_index()
        )

        nss_data = pd.read_parquet(Path("data", "nss_curve.parquet"))
        last_nss_date = nss_data.index.max()

        logger.info("cheking for new data for nss")
        data_to_do_nss = data.loc[last_nss_date + pd.offsets.Day(1) :]
        dates_to_do_nss = data_to_do_nss.index.get_level_values("Date").unique()
        if dates_to_do_nss.empty:
            logger.warning("no new data for nss")
            self.nss_curve = nss_data
            return nss_data

        logger.info("calculating rates and params for nss")
        nss_helper = NSShelper()
        new_nss_data = nss_helper.calculate_all(data_to_do_nss, dates_to_do_nss)

        updated_nss_data = pd.concat([nss_data, new_nss_data])

        logger.info("saving updated nss curve")
        updated_nss_data.to_parquet(Path("data", "nss_curve.parquet"))
        self.nss_curve = updated_nss_data

        return updated_nss_data

    def update_data(self) -> None:
        self.update_interest_calendar()
        self.update_bond_prices()
        self.update_nss_curve()

    def calculate_term_structure(self, *, update_data: bool = False) -> NominalACM:
        if update_data:
            self.update_data()

        data = pd.read_parquet(Path("data", "nss_curve.parquet"))
        data = data.drop(columns=["beta0", "beta1", "beta2", "beta3", "tau1", "tau2"])
        data = data.resample("ME").last()
        data.columns = [int(col) for col in data.columns]

        acm = NominalACM(
            curve=data,
            n_factors=5,
        )

        return acm

    def make_risk_neutral_graph(self, acm: NominalACM, maturities: Iterable = (12, 24, 60, 120)):
        plt.rcParams["font.family"] = self.FONTNAME
        plt.rcParams["font.weight"] = "bold"

        offset_date = datetime.today() - pd.offsets.YearBegin(4)

        fig, ax = plt.subplots(2, 2, sharex="all", figsize=self.FIGSIZE)

        fig.gca().yaxis.set_major_formatter("{x:.0%}")
        fig.suptitle(
            "PLN Sovereign curve - Risk-Neutral rates",
            fontsize=self.TITLE_FONT_SIZE,
        )
        fig.text(0.98, 0.95, "@SliwinskiAlan", fontsize=10, color="gray", ha="right", va="bottom", alpha=0.5)

        for curve, i in zip(maturities, product((0, 1), (0, 1)), strict=False):
            zero_curve = acm.curve.loc[offset_date:, curve]
            rny = acm.rny.loc[offset_date:, curve]

            ax[i].plot(zero_curve, label="Fitted zero-coupon rate", color="white")
            ax[i].plot(rny, label="Risk-Neutral rate", color="white", linestyle=":")

            ax[i].fill_between(
                zero_curve.index,
                zero_curve,
                rny,
                where=zero_curve > rny,
                facecolor="green",
                alpha=0.5,
                label="Term Premium",
                interpolate=True,
            )

            ax[i].fill_between(
                zero_curve.index,
                zero_curve,
                rny,
                where=zero_curve < rny,
                facecolor="red",
                alpha=0.5,
                interpolate=True,
            )

            ax[i].set_title(f"{curve / 12:.0f} year rny", fontsize=self.SUBTITLE_FONT_SIZE)
            ax[i].grid(alpha=0.1)
            ax[i].get_yaxis().set_major_formatter("{x:.1%}")

        plt.legend()
        plt.tight_layout()

        path = "risk_neutral.png"
        fig.savefig(path)

        return path

    def make_term_premium_graph(self, acm: NominalACM, maturities: Iterable = (12, 24, 60, 120)):
        plt.rcParams["font.family"] = self.FONTNAME
        plt.rcParams["font.weight"] = "bold"
        offset_date = datetime.today() - pd.offsets.YearBegin(4)
        fig, ax = plt.subplots(2, 2, sharex="all", figsize=self.FIGSIZE)

        fig.suptitle(
            "PLN Sovereign Curve - Term Premium",
            fontsize=self.TITLE_FONT_SIZE,
        )
        fig.text(0.98, 0.95, "@SliwinskiAlan", fontsize=10, color="gray", ha="right", va="bottom", alpha=0.5)

        for curve, i in zip(maturities, product((0, 1), (0, 1)), strict=False):
            tp = acm.tp.loc[offset_date:, curve]
            ax[i].plot(tp, label="Term Premium", color="white")
            ax[i].fill_between(
                tp.index,
                tp,
                0,
                where=tp > 0,
                facecolor="green",
                alpha=0.5,
                interpolate=True,
            )
            ax[i].fill_between(
                tp.index,
                tp,
                0,
                where=tp < 0,
                facecolor="red",
                alpha=0.5,
                interpolate=True,
            )

            ax[i].set_title(f"{curve / 12:.0f} year term premium", fontsize=self.SUBTITLE_FONT_SIZE)
            ax[i].grid(alpha=0.1)
            ax[i].get_yaxis().set_major_formatter("{x:.1%}")

        plt.legend()
        plt.tight_layout()

        path = "term_premium.png"
        fig.savefig(path)

        return path

    def prepare_tweet(self, acm: NominalACM, maturities: Iterable = (12, 24, 60, 120)):
        rny = self.make_risk_neutral_graph(acm)
        tp = self.make_term_premium_graph(acm)

        rny_curr_values = acm.rny.loc[:, maturities].tail(1).to_numpy().flatten()
        tp_curr_values = acm.tp.loc[:, maturities].tail(1).to_numpy().flatten()

        text = (
            "\U0001f1f5\U0001f1f1 PLN Sovereign curve modelling 📊\n\n"
            "⚖️ Risk-Neutral rates\n"
            + "\n".join([
                f"{maturity / 12:.0f}y {value:.2%}"
                for maturity, value in zip(maturities, list(rny_curr_values), strict=True)
            ])
            + "\n\n"
            "⏳ Term Premium\n"
            + "\n".join([
                f"{maturity / 12:.0f}y {value:.2%}"
                for maturity, value in zip(maturities, list(tp_curr_values), strict=True)
            ])
        )

        return text, [rny, tp]

    def run(self) -> None:
        self.update_data()

        acm = self.calculate_term_structure()

        text, paths = self.prepare_tweet(acm)

        self.make_tweet(text, paths)
