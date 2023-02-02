import wig_bot.main as wig_main
import makro_bot.main as makro_main
import twitter
import keys


def autoryzacja():

    bearer_token = keys.bearer_token
    api_key = keys.api_key
    access_token = keys.access_token
    access_token_secret = keys.access_token_secret
    api_secret = keys.api_secret

    client, api = twitter.au(bearer_token, api_key, api_secret, access_token, access_token_secret)
    print('auth completed')

    return client, api



def main():

    client, api = autoryzacja()

    # wig_main.main(client, api)

    makro_main.main(client, api)



if __name__ == '__main__':
    main()