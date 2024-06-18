import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import yahooquery as yq
from matplotlib import pyplot as plt
from tweepy import API, Client, OAuth1UserHandler

import keys

plt.style.use("dark_background")

os.chdir(Path(__file__).parent)


class TwitterBot:
    def __init__(self) -> None:
        # client, api = self.auth()
        # self.client: Client = client
        # self.api: API = api

        wig_components = self._get_wig_components()
        self.wig_components: pd.DataFrame = wig_components
        self.tickers: list = wig_components.ticker.to_list()

        self.prices = self._get_data()

        ts = pd.DataFrame(self.prices.index)
        ts["year"] = ts.date.dt.year
        ts["quarter"] = ts.date.dt.quarter
        ts["month"] = ts.date.dt.month
        ts["week"] = ts.date.dt.isocalendar().week
        ts["day"] = ts.date.dt.day
        ts["weekday"] = ts.date.dt.weekday
        self.ts: pd.DataFrame = ts

    def _au(
        self, bearer_token, api_key, api_secret, access_token, access_token_secret
    ) -> tuple[Client, API]:
        client = Client(
            bearer_token, api_key, api_secret, access_token, access_token_secret
        )

        auth = OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        api = API(auth, retry_count=5, retry_delay=5, retry_errors=set([503]))
        # https://stackoverflow.com/questions/48117126/when-using-tweepy-cursor-what-is-the-best-practice-for-catching-over-capacity-e
        return client, api

    def auth(self) -> tuple[Client, API]:
        bearer_token = keys.BEARER_TOKEN
        api_key = keys.API_KEY
        access_token = keys.ACCESS_TOKEN
        access_token_secret = keys.ACCESS_TOKEN_SECRET
        api_secret = keys.API_SECRET

        client, api = self._au(
            bearer_token, api_key, api_secret, access_token, access_token_secret
        )

        return client, api

    def _make_tweet(self, text: str, pictures=None):
        if pictures:
            lst = []
            for picture in pictures:
                media = self.api.media_upload(filename=picture)
                lst.append(media.media_id_string)

            self.client.create_tweet(text=text, media_ids=lst)

        else:
            self.client.create_tweet(text=text)

    def _get_data(self) -> pd.DataFrame:

        tickers = yq.Ticker(self.tickers)
        self._yq_tickers = tickers

        start_date = datetime.today() - timedelta(days=365)

        prices = tickers.history(start=start_date, interval="1d")[["adjclose"]]
        prices = prices.reset_index().pivot(
            index="date", columns="symbol", values="adjclose"
        )

        return prices

    @staticmethod
    def get_symbol(query, preferred_exchange="WSE"):
        try:
            data = yq.search(query)
        except ValueError:  # Will catch JSONDecodeError
            print(query)
        else:
            quotes = data["quotes"]
            if len(quotes) == 0:
                return "No Symbol Found"

            symbol = quotes[0]["symbol"]
            for quote in quotes:
                if quote["exchange"] == preferred_exchange:
                    symbol = quote["symbol"]
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
        print("empty data")
        print(empty_data)
        if empty_data.empty:
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
                    full_components.loc[indx, "ticker"] = new_symbol

                if sector is np.NaN or industry is np.NaN:
                    # add missing sector and industry values
                    asset_profile = yq.Ticker(new_symbol).asset_profile[new_symbol]
                    full_components.loc[indx, "sector"] = asset_profile["sector"]
                    full_components.loc[indx, "industry"] = asset_profile["industry"]

            # save new csv with full WIG
            full_components.drop(columns="shares_num").to_csv(
                "wig_comps.csv", index=False
            )

        return full_components

    def get_start_date(self, period="ytd"):

        td = pd.Timestamp(datetime.today())

        if period == "ytd":
            return self.ts.loc[self.ts[self.ts.year == td.year - 1].index.max() :].index
        elif period == "mtd":
            return self.ts.iloc[
                self.ts[
                    (self.ts.year == td.year) & (self.ts.month == td.month)
                ].index.min()
                - 1 :
            ].index
        elif period == "qtd":
            return self.ts.iloc[
                self.ts[(self.ts.year == td.year) & (self.ts.quarter == td.quarter)].index.min() - 1 :
            ].index
        elif period == "week":  # remember to do this on weekends!
            return self.ts.iloc[
                self.ts[(self.ts.year == td.year) & (self.ts.week == td.week)].index.min() - 1 :
            ].index
        elif period == "day":
            return self.ts.tail(2).index
        elif period == "year":
            return self.ts.iloc[self.ts.index.max() - 252 :]
        else:
            raise ValueError(f'period {period} not available')

    def run(self):
        raise NotImplementedError


if __name__ == "__main__":
    bot = TwitterBot()
    bot.run()
