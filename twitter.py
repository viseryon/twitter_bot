import tweepy


def au(bearer_token, api_key, api_secret, access_token, access_token_secret):
    client = tweepy.Client(
        bearer_token, api_key, api_secret, access_token, access_token_secret
    )

    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth, retry_count=5, retry_delay=5, retry_errors=set([503]))
    # https://stackoverflow.com/questions/48117126/when-using-tweepy-cursor-what-is-the-best-practice-for-catching-over-capacity-e
    return client, api


def tweet_things(client, api, text="test", obrazki=None):
    if obrazki:
        lst = []
        for obrazek in obrazki:
            media = api.media_upload(filename=obrazek)
            lst.append(media.media_id_string)

        client.create_tweet(text=text, media_ids=lst)

    else:
        client.create_tweet(text=text)

    print("tweeted successfully")


if __name__ == "__main__":
    pass
