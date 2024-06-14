from tweepy import API, Client, OAuth1UserHandler

import keys


class TwitterBot:
	def __init__(self):
		client, api = self.auth()
		self.client: Client = client
		self.api: API = api
		self.data = None

	def _au(self, bearer_token, api_key, api_secret, access_token, access_token_secret) -> tuple[Client, API]:
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

	def get_data(self):
		if self.data:
			return self.data
		
		
		
		


if __name__ == "__main__":
	bot = TwitterBot()
	
