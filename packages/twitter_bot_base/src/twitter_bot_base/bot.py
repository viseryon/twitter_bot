import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv
from mylogging import setup
from tweepy import API, Client, OAuth1UserHandler

load_dotenv()

logger = setup(__name__, __file__)


class TwitterBot(ABC):
    def __init__(self, *, auto_auth: bool = True) -> None:
        """Initialize and authenticate client.

        Authenticates client with tweepy.
        """
        self.client: Client | None = None
        self.api: API | None = None
        self.is_authenticated: bool = False

        if auto_auth:
            self.auth()
            logger.info("auth complete")
        else:
            logger.info("no auto_auth chosen")

    def auth(self) -> tuple[Client, API]:
        """Auth method.

        Reads from keys all the necessary secrets and performs auth with tweepy.

        Returns:
            tuple[Client, API]: stuff needed to make tweets

        """
        logger.info("authenicating...")
        bearer_token = os.environ["BEARER_TOKEN"]
        api_key = os.environ["API_KEY"]
        access_token = os.environ["ACCESS_TOKEN"]
        access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]
        api_secret = os.environ["API_SECRET"]

        try:
            # https://stackoverflow.com/questions/48117126/when-using-tweepy-cursor-what-is-the-best-practice-for-catching-over-capacity-e
            client = Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
            auth = OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
            api = API(auth, retry_count=5, retry_delay=5, retry_errors={503})
        except Exception:
            logger.exception("auth failed")
            sys.exit(1)

        self.client = client
        self.api = api
        self.is_authenticated = True

        return client, api

    def make_tweet(self, text: str, pictures: list[str]) -> None:
        """Make a tweet.

        Args:
            text (str): text to put in the tweet
            pictures (list[str]): list of paths to pictures to tweet

        Raises:
            ValueError: If the client or api is None after attempting authentication.

        """
        if not self.is_authenticated:
            self.auth()

        client, api = self.client, self.api

        # help the type checker: client and api must be present here
        if client is None or api is None:
            msg = "client or api is None"
            raise ValueError(msg)

        if pictures:
            logger.info(
                "adding pictures to the tweet",
                extra={"number_of_pictures": len(pictures)},
            )
            lst = []
            for picture in pictures:
                media = api.media_upload(filename=picture)
                lst.append(media.media_id_string)

            client.create_tweet(text=text, media_ids=lst)

            logger.info("deleting used pictures")
            for picture in pictures:
                Path(picture).unlink()

        else:
            logger.info("posting without pictures")
            client.create_tweet(text=text)

        logger.info(
            "tweet posted successfully",
            extra={"tweet_text": text, "number_of_pictures": len(pictures)},
        )

    @abstractmethod
    def run(self): ...
