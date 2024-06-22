import logging
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

logging.basicConfig(
    level=logging.INFO,
    # filename="app.log",
    format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)


class TwitterBot:
    def __init__(self) -> None:
        client, api = self.auth()
        self.client: Client = client
        self.api: API = api
        logging.info("auth complete")

        wig_components = self._get_wig_components()
        self.wig_components: pd.DataFrame = wig_components
        self.tickers: list = wig_components.yf_ticker.to_list()
        logging.info("downloaded wig components")

        self.prices, self.wig = self._get_data()
        self.curr_prices = self.prices.iloc[-1]
        logging.info("downloaded data")

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
        logging.info("init complete")

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

        logging.info("authenicating...")
        bearer_token = keys.BEARER_TOKEN
        api_key = keys.API_KEY
        access_token = keys.ACCESS_TOKEN
        access_token_secret = keys.ACCESS_TOKEN_SECRET
        api_secret = keys.API_SECRET

        try:
            client, api = self._au(
                bearer_token, api_key, api_secret, access_token, access_token_secret
            )
        except Exception as e:
            logging.exception("auth failed", e)
            exit(1)

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

        prices: pd.DataFrame = tickers.history(
            start=start_date, timeout=20, progress=False, threads=False
        ).Close
        prices.columns = [tick.removesuffix(".WA") for tick in prices.columns]
        prices = prices.ffill()

        wig = prices.WIG
        prices = prices.drop(columns=["WIG"])

        return prices, wig

    @staticmethod
    def get_symbol(
        query: str, preferred_exchange: str = "WSE", max_tries=5, **kwargs
    ) -> str:
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
            tries = kwargs.get("tries", 0)
            if tries >= max_tries:
                raise ValueError(
                    f"YahooFinance have not returned the necessary ticker\n{query = }"
                )
            return TwitterBot.get_symbol(query, tries=tries + 1)
        else:
            quotes = data["quotes"]
            if len(quotes) == 0:
                tries = kwargs.get("tries", 0)
                if tries >= 5:
                    raise ValueError(
                        f"YahooFinance have not returned the necessary ticker\n{query = }"
                    )
                return TwitterBot.get_symbol(query, tries=tries + 1)

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

        pretty_industry = {
            "Financial Data & Stock Exchanges": "Financial Data<br>& Stock Exchanges",
            "Utilities - Regulated Gas": "Regulated Gas",
            "Utilities - Independent Power Producers": "Independent<br>Power Producers",
            "Utilities - Renewable": "Renewable",
            "Utilities - Regulated Electric": "Regulated Electric",
            "Real Estate - Diversified": "Diversified",
            "Real Estate Services": "Services",
            "Real Estate - Development": "Development",
            "Farm & Heavy Construction Machinery": "Farm & Heavy<br>Construction Machinery",
            "Staffing & Employment Services": "Staffing & Employment<br>Services",
            "Tools & Accessories": "Tools & Accessories",
            "Building Products & Equipment": "Building Products & Equipment",
            "Integrated Freight & Logistics": "Integrated Freight & Logistics",
            "Specialty Industrial Machinery": "Specialty Industrial<br>Machinery",
            "Electrical Equipment & Parts": "Electrical Equipment & Parts",
            "Metal Fabrication": "Metal Fabrication",
            "Aerospace & Defense": "Aerospace & Defense",
            "Paper & Paper Products": "Paper & Paper Products",
            "Specialty Chemicals": "Specialty Chemicals",
            "Specialty Business Services": "Specialty Business<br>Services",
            "Drug Manufacturers - Specialty & Generic": "Drug Manufacturers<br>Specialty & Generic",
            "Medical Care Facilities": "Medical Care<br>Facilities",
            "Medical Instruments & Supplies": "Medical Instruments<br>& Supplies",
            "Pharmaceutical Retailers": "Pharmaceutical<br>Retailers",
            "Electronic Components": "Electronic Components",
            "Scientific & Technical Instruments": "Scientific & Technical<br>Instruments",
            "Electronics & Computer Distribution": "Electronics & Computer<br>Distribution",
            "Furnishings, Fixtures & Appliances": "Furnishings,<br>Fixtures & Appliances",
            "Travel Services": "Travel Services",
            "Information Technology Services": "Information Technology<br>Services",
            "Software - Infrastructure": "Infrastructure",
            "Medical Devices": "Medical Devices",
            "Banks - Regional": "Banks - Regional",
            "Oil & Gas Integrated": "Integrated",
            "Insurance - Property & Casualty": "Property & Casualty",
            "Internet Retail": "Internet Retail",
            "Apparel Manufacturing": "Apparel Manufacturing",
            "Copper": "Copper",
            "Grocery Stores": "Grocery Stores",
            "Electronic Gaming & Multimedia": "Electronic<br>Gaming & Multimedia",
            "Engineering & Construction": "Engineering & Construction",
            "Aluminum": "Aluminum",
            "Credit Services": "Credit Services",
            "Banks - Diversified": "Banks - Diversified",
            "Apparel Retail": "Apparel Retail",
            "Leisure": "Leisure",
            "Telecom Services": "Telecom Services",
            "Auto Parts": "Auto Parts",
            "Capital Markets": "Capital Markets",
            "Software - Application": "Application",
            "Discount Stores": "Discount Stores",
            "Entertainment": "Entertainment",
            "Coking Coal": "Coking Coal",
            "Medical Distribution": "Medical Distribution",
            "Restaurants": "Restaurants",
            "Agricultural Inputs": "Agricultural Inputs",
            "Diagnostics & Research": "Diagnostics & Research",
            "Waste Management": "Waste Management",
            "Biotechnology": "Biotechnology",
            "Oil & Gas Refining & Marketing": "Refining & Marketing",
            "Railroads": "Railroads",
            "Airlines": "Airlines",
            "Residential Construction": "Residential<br>Construction",
            "Publishing": "Publishing",
            "Steel": "Steel",
            "Thermal Coal": "Thermal Coal",
            "Confectioners": "Confectioners",
            "Packaged Foods": "Packaged Foods",
            "Specialty Retail": "Specialty Retail",
            "Chemicals": "Chemicals",
            "Beverages - Wineries & Distilleries": "Wineries & Distilleries",
            "Asset Management": "Asset Management",
            "Infrastructure Operations": "Infrastructure<br>Operations",
            "Conglomerates": "Conglomerates",
            "Farm Products": "Farm Products",
            "Security & Protection Services": "Security & Protection<br>Services",
            "Solar": "Solar",
            "Computer Hardware": "Computer Hardware",
            "Broadcasting": "Broadcasting",
            "Rental & Leasing Services": "Rental & Leasing<br>Services",
            "Industrial Distribution": "Industrial<br>Distribution",
            "Advertising Agencies": "Advertising<br>Agencies",
            "Household & Personal Products": "Household & Personal<br>Products",
            "Building Materials": "Building Materials",
            "Food Distribution": "Food Distribution",
            "Trucking": "Trucking",
            "Beverages - Non-Alcoholic": "Non-Alcoholic",
            "Footwear & Accessories": "Footwear & Accessories",
            "Consulting Services": "Consulting Services",
            "Communication Equipment": "Communication<br>Equipment",
            "Internet Content & Information": "Internet<br>Content & Information",
            "Lumber & Wood Production": "Lumber & Wood<br>Production",
            "Insurance - Diversified": "Diversified",
        }
        # check for empty data
        empty_data = full_components[full_components.isnull().any(axis=1)]
        if empty_data.empty:
            full_components["ticker"] = full_components["yf_ticker"].str.removesuffix(
                ".WA"
            )
            full_components.industry = full_components.industry.replace(pretty_industry)
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

        full_components.industry = full_components.industry.replace(pretty_industry)
        full_components["ticker"] = full_components["yf_ticker"].str.removesuffix(".WA")
        return full_components

    def get_periods_indicies(self, period="day") -> Index:
        """
        get a start date and last date of some period to calculate returns

        possible periods: ytd, qtd, mtd, week, day, year

        Args:
            period (str, optional): what period the changes will be calculated. Defaults to "day".

        Raises:
            NotImplementedError

        Returns:
            Index: index to use with df.iloc
        """

        if period == "ytd":
            return (
                self.ts.loc[self.ts[self.ts.year == self.today.year - 1].index.max() :]
                .iloc[[0, -1]]
                .index
            )
        elif period == "mtd":
            return (
                self.ts.iloc[
                    self.ts[
                        (self.ts.year == self.today.year)
                        & (self.ts.month == self.today.month)
                    ].index.min()
                    - 1 :
                ]
                .iloc[[0, -1]]
                .index
            )
        elif period == "qtd":
            return (
                self.ts.iloc[
                    self.ts[
                        (self.ts.year == self.today.year)
                        & (self.ts.quarter == self.today.quarter)
                    ].index.min()
                    - 1 :
                ]
                .iloc[[0, -1]]
                .index
            )
        elif period == "week":  # remember to do this on weekends!
            return (
                self.ts.iloc[
                    self.ts[
                        (self.ts.year == self.today.year)
                        & (self.ts.week == self.today.week)
                    ].index.min()
                    - 1 :
                ]
                .iloc[[0, -1]]
                .index
            )
        elif period == "day":
            return self.ts.iloc[[-2, -1]].index
        elif period == "year":
            return self.ts.iloc[self.ts.index.max() - 252 :].iloc[[0, -1]].index
        else:
            raise NotImplementedError(f"period {period} not available")

    def is_trading_day(self) -> bool:
        if pd.Timestamp(datetime.today().date()) in self.ts.Date.to_list():
            return True
        return False

    def _prepare_tweet_text(
        self, data: pd.DataFrame, wig_return: float, period: str
    ) -> str:
        """
        prepare text for the tweet

        method for calculating data that will be on the tweet

        Args:
            data (pd.DataFrame): data to calculate sectors returns
            wig_return (float): 
            period (str): period to go to the tweet title

        Returns:
            str: text to directly put on the tweet
        """
        
        data["contribution"] = data.mkt_cap * data.returns

        sectors_return = (
            data.groupby("sector")["contribution"].sum()
            / data.groupby("sector")["mkt_cap"].sum()
        ).sort_values(ascending=False)

        tweet_text = f"WIG Index {period} perf: {wig_return:.2%}"

        if wig_return > 0.02:
            tweet_text += " 🟢🟢🟢\n"
        elif wig_return > 0.01:
            tweet_text += " 🟢🟢\n"
        elif wig_return > 0.005:
            tweet_text += " 🟢\n"
        elif wig_return > -0.005:
            tweet_text += " ➖\n"
        elif wig_return > -0.01:
            tweet_text += " 🔴\n"
        elif wig_return > -0.02:
            tweet_text += " 🔴🔴\n"
        else:
            tweet_text += " 🔴🔴🔴\n"

        tweet_text += f"\n🟢 {data.ticker.iloc[0]} {data.company.iloc[0]} {data.returns.iloc[0]:.2%}\n🔴 {data.ticker.iloc[-1]} {data.company.iloc[-1]} {data.returns.iloc[-1]:.2%}\n\n"

        for i, (sector, change) in enumerate(sectors_return.items(), start=1):
            if i < 4:
                tweet_text += f"{i}. {sector} -> {change:.2%}\n"
            else:
                break

        return tweet_text

    ### performance heatmaps

    def make_heatmap(self, data: pd.DataFrame, path: str, period: str) -> None:
        """
        saves wig heatmap

        creates actual wig heatmap and saves it

        Args:
            data (pd.DataFrame): cols('ticker', 'company', 'sector', 'industry', 'shares_num', 'returns', 'curr_prices', 'mkt_cap')
            path (str): filename with extension
            period (str): used only for title
        """

        font = "Segoe UI"

        fig = px.treemap(
            data,
            path=["sector", "ticker"],
            values="mkt_cap",
            color="returns",
            color_continuous_scale=["#CC0000", "#292929", "#00CC00"],
            custom_data=data[["returns", "company", "ticker", "curr_prices", "sector"]],
        )

        fig.update_traces(
            insidetextfont=dict(size=140, family=font),
            textfont=dict(size=60, family=font),
            textposition="middle center",
            texttemplate="<br>%{customdata[2]}<br>    <b>%{customdata[0]:.2%}</b>     <br><sup><i>%{customdata[3]:.2f} zł</i><br></sup>",
            marker=dict(
                cornerradius=25,
                line_width=3,
                line_color="#2e2e2e",
            ),
        )

        fig.update_coloraxes(
            showscale=True,
            cmin=-0.03,
            cmax=0.03,
            cmid=0,
        )

        fig.update_layout(
            margin=dict(t=350, l=5, r=5, b=120),
            width=7680,
            height=4320,
            title=dict(
                text=f"INDEX WIG<br><sup>{period} performance ⁕ {datetime.now(self.tzinfo):%Y/%m/%d}</sup>",
                font=dict(color="white", size=170, family=font),
                yanchor="middle",
                xanchor="center",
                xref="paper",
                yref="paper",
                x=0.5,
                pad=dict(t=100, b=100),
            ),
            paper_bgcolor="#1a1a1a",
            colorway=["#d11635", "#AC1B26", "#7F151D", "#3B6323", "#518A30", "#66B13C"],
        )

        fig.add_annotation(
            text=("source: YahooFinance!"),
            x=0.90,
            y=-0.023,
            font=dict(family=font, size=80, color="white"),
            opacity=0.7,
            align="left",
        )

        fig.add_annotation(
            text=(datetime.now(self.tzinfo).strftime(r"%Y/%m/%d %H:%M")),
            x=0.1,
            y=-0.025,
            font=dict(family=font, size=80, color="white"),
            opacity=0.7,
            align="left",
        )

        fig.add_annotation(
            text=("@SliwinskiAlan"),
            x=0.5,
            y=-0.025,
            font=dict(family=font, size=80, color="white"),
            opacity=0.7,
            align="left",
        )

        fig.write_image(path)

    def heatmap_daily_returns(self) -> tuple[str, str]:
        """
        method for creating wig heatmap for 1d performance

        calculates necessary data and prepares heatmap and text for the tweet

        Returns:
            tuple[str, str]: path to picture and tweet text
        """

        # calculate daily returns
        indicies = self.get_periods_indicies("day")
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
        data = (
            data.reset_index()
            .rename({"index": "ticker"}, axis=1)
            .sort_values("returns", ascending=False)
        )

        # data.columns
        # 'ticker', 'company', 'sector', 'industry', 'shares_num', 'returns', 'curr_prices', 'mkt_cap'

        path = "wig_heatmap_1d.png"
        self.make_heatmap(data, path, "1D")

        # text for the tweet
        tweet_text = self._prepare_tweet_text(data, wig_return, period="1D")

        return (path, tweet_text)

    def heatmap_weekly_returns(self):
        raise NotImplementedError

    def heatmap_monthly_returns(self):
        raise NotImplementedError

    def heatmap_quarterly_returns(self):
        raise NotImplementedError

    def heatmap_yearly_returns(self):
        raise NotImplementedError

    def run(self):
        """
        run twitter bot

        make calculations, heatmaps and post them to twitter
        """
        logging.info("running main function")
        # post daily heatmap
        if self.is_trading_day():
            logging.info("posting daily heatmap")
            path, tweet_string = self.heatmap_daily_returns()
            self.make_tweet(tweet_string, [path])
            logging.info("tweeted successfully")


if __name__ == "__main__":
    logging.info("starting...")
    bot = TwitterBot()
    bot.run()
