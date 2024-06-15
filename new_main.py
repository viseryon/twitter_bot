import numpy as np
import pandas as pd
import yahooquery as yq
from tweepy import API, Client, OAuth1UserHandler


class TwitterBot:
    def __init__(self) -> None:
        client, api = self.auth()
        self.client: Client = client
        self.api: API = api

        wig_components = self._get_wig_components()
        self.wig_components: pd.DataFrame = wig_components
        self.tickers: list = wig_components.tickers.to_list()

        self.prices = self._get_data()

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

    def _get_data(self):

        tickers = yq.Ticker(self.tickers)
        self._yq_tickers = tickers

        prices = tickers.history()[["adjclose"]]
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

        # check empty tickers
        empty_tickers = full_components[full_components.ticker.isna()]
        if not empty_tickers.empty:
            return full_components
        else:  # get new ticker from Yahoo Finance
            for indx, (company, _, ticker, _) in empty_tickers.iterrows():
                print(f"Company {company} had no ticker.")
                empty_tickers.loc[indx, "ticker"] = self.get_symbol(company)

        # save new csv with full WIG
        full_components[["company", "ISIN", "ticker"]].to_csv(
            "wig_comps.csv", index=False
        )
        return full_components

    def run(self):
        raise NotImplementedError


if __name__ == "__main__":
    bot = TwitterBot()
    bot.run()
