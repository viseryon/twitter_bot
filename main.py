from wig_bot import main as wig_main
from makro_bot import main as makro_main
import twitter
import keys


def autoryzacja():
    client, api = twitter.au()
    print('auth completed')

    return client, api



def main():

    client, api = autoryzacja()

    wig_main.main(client, api)

    makro_main.main(client, api)



if __name__ == '__main__':
    main()