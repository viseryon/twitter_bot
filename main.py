import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import pytz
import yahooquery as yq
import yfinance as yf
from matplotlib import pyplot as plt
from pandas import Index
from tweepy import API, Client, OAuth1UserHandler

import keys

"""
script running my twitter bot

it includes TwitterBot class that will run bot that posts pictures with WIG returns
"""

plt.style.use("dark_background")

os.chdir(Path(__file__).parent)


class TwitterBot:
    def __init__(self) -> None:
        # client, api = self.auth()
        # self.client: Client = client
        # self.api: API = api

        wig_components = self._get_wig_components()
        self.wig_components: pd.DataFrame = wig_components
        self.tickers: list = wig_components.yf_ticker.to_list()

        self.prices, self.wig = self._get_data()
        self.curr_prices = self.prices.iloc[-1]

        ts = pd.DataFrame(self.prices.index)
        ts["year"] = ts.Date.dt.year
        ts["quarter"] = ts.Date.dt.quarter
        ts["month"] = ts.Date.dt.month
        ts["week"] = ts.Date.dt.isocalendar().week
        ts["day"] = ts.Date.dt.day
        ts["weekday"] = ts.Date.dt.weekday
        self.ts: pd.DataFrame = ts

        self.tzinfo = pytz.timezone("Europe/Warsaw")
        self.today = pd.Timestamp(datetime.today())

    def _au(
        self, bearer_token, api_key, api_secret, access_token, access_token_secret
    ) -> tuple[Client, API]:
        """auth with tweepy"""

        client = Client(
            bearer_token, api_key, api_secret, access_token, access_token_secret
        )

        auth = OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        api = API(auth, retry_count=5, retry_delay=5, retry_errors=set([503]))
        # https://stackoverflow.com/questions/48117126/when-using-tweepy-cursor-what-is-the-best-practice-for-catching-over-capacity-e
        return client, api

    def auth(self) -> tuple[Client, API]:
        """
        auth method

        reads from keys all the necessary secrets

        Returns:
            tuple[Client, API]: stuff needed make tweets
        """

        bearer_token = keys.BEARER_TOKEN
        api_key = keys.API_KEY
        access_token = keys.ACCESS_TOKEN
        access_token_secret = keys.ACCESS_TOKEN_SECRET
        api_secret = keys.API_SECRET

        client, api = self._au(
            bearer_token, api_key, api_secret, access_token, access_token_secret
        )

        return client, api

    def make_tweet(self, text: str, pictures: list[str]) -> None:
        """
        method that makes a tweet

        Args:
            text (str): text to put in the tweet
            pictures (list[str]): list of paths to pictures to tweet
        """

        if pictures:
            lst = []
            for picture in pictures:
                media = self.api.media_upload(filename=picture)
                lst.append(media.media_id_string)

            self.client.create_tweet(text=text, media_ids=lst)

            for picture in pictures:
                os.remove(picture)

        else:
            self.client.create_tweet(text=text)

    def _get_data(self) -> tuple[pd.DataFrame, pd.Series]:
        """
        get data from YahooFinance

        get pd.DataFrame of prices of selected tickers and transform it

        Returns:
            pd.DataFrame: prices with index of dates and columns of stock prices
        """

        tickers = yf.Tickers(self.tickers + ["WIG.WA"])

        start_date = datetime.today() - timedelta(days=365)

        prices = tickers.history(start=start_date, timeout=20)
        prices = prices.Close
        prices.columns = [tick.removesuffix(".WA") for tick in prices.columns]

        wig = prices.WIG
        prices = prices.drop(columns=["WIG"])

        return prices, wig

    @staticmethod
    def get_symbol(query: str, preferred_exchange: str = "WSE") -> None | str:
        """
        get ticker

        searches Yahoo Finance for a ticker by other identifier

        Args:
            query (str): some identifier
            preferred_exchange (str, optional): what exchange to prioritize. Defaults to "WSE".

        Returns:
            _type_: _description_
        """

        try:
            data = yq.search(query)
        except ValueError:  # Will catch JSONDecodeError
            print(query)
            return None
        else:
            quotes = data["quotes"]
            if len(quotes) == 0:
                return None

            symbol = quotes[0]["symbol"]
            for quote in quotes:
                if quote["exchange"] == preferred_exchange:
                    symbol: str = quote["symbol"]
                    break
            return symbol

    def _get_wig_components(self) -> pd.DataFrame:

        # get data from source
        updated_components = pd.read_html(
            "https://gpwbenchmark.pl/ajaxindex.php?action=GPWIndexes&start=ajaxPortfolio&format=html&lang=EN&isin=PL9999999995&cmng_id=1011&time=1718378430237"
        )[0]

        updated_components = updated_components.iloc[:, :3]
        updated_components.columns = ["company", "ISIN", "shares_num"]

        saved_components = pd.read_csv("wig_comps.csv")

        # add tickers to the source data
        full_components = pd.merge(
            saved_components, updated_components, how="right", on=["company", "ISIN"]
        )

        # check for empty data
        empty_data = full_components[full_components.isnull().any(axis=1)]
        if empty_data.empty:
            full_components["ticker"] = full_components["yf_ticker"].str.removesuffix(
                ".WA"
            )
            return full_components
        else:  # get new ticker from Yahoo Finance
            for indx, (
                company,
                isin,
                ticker,
                sector,
                industry,
                shares_num,
            ) in empty_data.iterrows():
                print(f"Company {company} had missing data.")

                if ticker is np.NaN:
                    # add missing ticker
                    new_symbol = self.get_symbol(company)
                    full_components.loc[indx, "yf_ticker"] = new_symbol

                if sector is np.NaN or industry is np.NaN:
                    # add missing sector and industry values
                    asset_profile = yq.Ticker(new_symbol).asset_profile[new_symbol]
                    full_components.loc[indx, "sector"] = asset_profile["sector"]
                    full_components.loc[indx, "industry"] = asset_profile["industry"]

            # save new csv with full WIG
            full_components.drop(columns="shares_num").to_csv(
                "wig_comps.csv", index=False
            )

        full_components["ticker"] = full_components["yf_ticker"].str.removesuffix(".WA")
        return full_components

    def get_start_date(self, period="day") -> Index:
        """
        get a start date of some period to calculate returns

        possible periods: ytd, qtd, mtd, week, day, year

        Args:
            period (str, optional): what period the changes will be calculated. Defaults to "day".

        Raises:
            NotImplementedError

        Returns:
            Index: index to use with df.loc
        """

        if period == "ytd":
            return self.ts.loc[self.ts[self.ts.year == self.today.year - 1].index.max() :].index
        elif period == "mtd":
            return self.ts.iloc[
                self.ts[
                    (self.ts.year == self.today.year) & (self.ts.month == self.today.month)
                ].index.min()
                - 1 :
            ].index
        elif period == "qtd":
            return self.ts.iloc[
                self.ts[
                    (self.ts.year == self.today.year) & (self.ts.quarter == self.today.quarter)
                ].index.min()
                - 1 :
            ].index
        elif period == "week":  # remember to do this on weekends!
            return self.ts.iloc[
                self.ts[
                    (self.ts.year == self.today.year) & (self.ts.week == self.today.week)
                ].index.min()
                - 1 :
            ].index
        elif period == "day":
            return self.ts.tail(2).index
        elif period == "year":
            return self.ts.iloc[self.ts.index.max() - 252 :].index
        else:
            raise NotImplementedError(f"period {period} not available")

    def is_trading_day(self) -> bool:
        if pd.Timestamp(datetime.today().date()) in self.ts.Date.to_list():
            return True
        return False

    ### performance heatmaps

    def post_daily_returns(self):
        if not self.is_trading_day():
            return

        # calculate daily returns
        indicies = self.get_start_date("day")
        data: pd.DataFrame = self.prices.iloc[indicies].pct_change().dropna().T
        data.columns = ["returns"]

        wig_return: float = self.wig.iloc[indicies].pct_change().values[0]

        data = pd.merge(
            self.wig_components.set_index("ticker"),
            data,
            right_index=True,
            left_index=True,
            validate="one_to_one",
        )
        # data.columns
        # ['company', 'ISIN', 'yf_ticker', 'sector', 'industry', 'shares_num', 'returns']

        data = data.drop(columns=["ISIN", "yf_ticker"])
        data["curr_prices"] = self.curr_prices

        data["mkt_cap"] = data["curr_prices"] * data["shares_num"]
        data = data.reset_index().rename({"index": "ticker"}, axis=1)

        # 'ticker', 'company', 'sector', 'industry', 'shares_num', 'returns', 'curr_prices', 'mkt_cap'

        fig = px.treemap(
            data,
            path=[px.Constant("WIG"), "sector", "industry", "ticker"],
            values="mkt_cap",
            color="returns",
            color_continuous_scale=["#CC0000", "#353535", "#00CC00"],
            custom_data=data[["returns", "company", "ticker", "curr_prices", "sector"]],
        )

        fig.update_traces(
            insidetextfont=dict(
                size=120,
            ),
            textfont=dict(size=40),
            textposition="middle center",
            texttemplate="<br>%{customdata[2]}<br>    <b>%{customdata[0]:.2%}</b>     <br><sup><i>%{customdata[3]:.2f} zł</i><br></sup>",
            marker_line_width=3,
            marker_line_color="#1a1a1a",
            root=dict(color="#1a1a1a"),
        )

        fig.update_coloraxes(
            showscale=True,
            cmin=-0.03,
            cmax=0.03,
            cmid=0,
        )

        fig.update_layout(
            margin=dict(t=200, l=5, r=5, b=120),
            width=7680,
            height=4320,
            title=dict(
                text=f"INDEX WIG  ⁕ {datetime.now(self.tzinfo):%Y/%m/%d}",
                font=dict(
                    color="white",
                    size=150,
                ),
                yanchor="middle",
                xanchor="center",
                xref="paper",
                yref="paper",
                x=0.5,
            ),
            paper_bgcolor="#1a1a1a",
            # paper_bgcolor="rgba(0,0,0,0)",
            colorway=["#D9202E", "#AC1B26", "#7F151D", "#3B6323", "#518A30", "#66B13C"],
        )

        fig.add_annotation(
            text=("source: YahooFinance!, @SliwinskiAlan"),
            x=0.90,
            y=-0.023,
            font=dict(family="Calibri", size=80, color="white"),
            opacity=0.7,
            align="left",
        )

        fig.add_annotation(
            text=(datetime.now(self.tzinfo).strftime(r"%Y/%m/%d %H:%M")),
            x=0.1,
            y=-0.025,
            font=dict(family="Calibri", size=80, color="white"),
            opacity=0.7,
            align="left",
        )

        fig.add_annotation(
            text=("@SliwinskiAlan"),
            x=0.5,
            y=-0.025,
            font=dict(family="Calibri", size=80, color="white"),
            opacity=0.7,
            align="left",
        )

        # fig.show()
        fig.write_image("wig_heatmap.png")
        return
        data["udzial_zmiana_pct"] = data.Udzial * data.Zmiana_pct
        sectors_change = (
            data.groupby("Sector")["udzial_zmiana_pct"].sum()
            / data.groupby("Sector")["Udzial"].sum()
        )

        sectors_change = sectors_change.sort_values(ascending=False)
        data = data.sort_values("Zmiana_pct", ascending=False)

        data_string = f"\nWIG perf 1D: {stat_chng:.2%}"

        if stat_chng > 0.02:
            data_string += " 🟢🟢🟢\n"
        elif stat_chng > 0.01:
            data_string += " 🟢🟢\n"
        elif stat_chng > 0.005:
            data_string += " 🟢\n"
        elif stat_chng > -0.005:
            data_string += " ➖\n"
        elif stat_chng > -0.01:
            data_string += " 🔴\n"
        elif stat_chng > -0.02:
            data_string += " 🔴🔴\n"
        else:
            data_string += " 🔴🔴🔴\n"

        data_string += f"\n🟢 {data.Ticker.iloc[0]} {data.Nazwa.iloc[0]} {data.Zmiana_pct.iloc[0]:.2%}\n🔴 {data.Ticker.iloc[-1]} {data.Nazwa.iloc[-1]} {data.Zmiana_pct.iloc[-1]:.2%}\n\n"

        for i, (sector, change) in enumerate(sectors_change.items()):
            if i < 3:
                data_string += f"{i+1}. {sector} ->{change:>7.2%}\n"

        return True

    def post_weekly_returns(self):
        raise NotImplementedError

    def post_monthly_returns(self):
        raise NotImplementedError

    def post_quarterly_returns(self):
        raise NotImplementedError

    def post_yearly_returns(self):
        raise NotImplementedError

    def run(self): ...


if __name__ == "__main__":
    bot = TwitterBot()
    bot.run()
