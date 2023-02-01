import tweepy
import keys

def au():
    client = tweepy.Client(keys.bearer_token, keys.api_key,
                        keys.api_secret, keys.access_token, keys.access_token_secret)

    auth = tweepy.OAuth1UserHandler(
        keys.api_key, keys.api_secret, keys.access_token, keys.access_token_secret)
    api = tweepy.API(auth)

    return client, api

def tweet_things(client, api, text='test', obrazki=None):

    if obrazki:
        lst = []
        for obrazek in obrazki:
            media = api.media_upload(filename=obrazek)
            lst.append(media.media_id_string)
        
        client.create_tweet(text=text, media_ids=lst)

    else:
        client.create_tweet(text=text)


    print('tweeted successfully')


if __name__ == '__main__':
    pass
