import wig20_options
import analysts_pts
import analyst_rec
import twitter
import os
import dni_opcje
import numpy as np
from datetime import timedelta, datetime as dt


def tweet_charts(text, charts):

    client, api = twitter.au()
    print('auth completed')
    twitter.tweet_things(client, api, text=text, obrazki=charts)


def tweet_only_text(text):
    client, api = twitter.au()
    print('auth completed')
    twitter.tweet_things(client, api, text=text)


def posting_option_charts():
    print('starting posting_option_charts')

    wig20_options.do_charts()
    print('wig20_options charts generated')
    charts = [x for x in os.listdir() if x.endswith('.png')]
    charts.sort()
    print(charts)
    to_post = [charts[-1]] + charts[:2] + [charts[-2]]
    to_post = list(set(to_post))
    print(to_post)

    text = '''OPCJE NA INDEX WIG20 💡

📈 Jak opcje wyceniają prawdopodobieństwo osiągnięcia danego strike'a po dzisiejszej sesji? 📉

#GPW #WIG20 #WIG #options #opcje #giełda #python #project'''

    tweet_charts(text, to_post)

    for chart in charts:
        os.remove(chart)

    print('wig20_option charts removed')


def posting_analyst_pts():
    print('starting posting_analyst_pts')
    wig20_40_comps = analysts_pts.wig20_40_components()

    with open('last_10_pts_posts_tickers.txt', 'r', encoding='UTF-8') as f:
        last_10_tickers = f.read()
        last_10_tickers = last_10_tickers.split(',')[-10:]
        print(last_10_tickers)

    def do_chart():

        ticker = np.random.choice(wig20_40_comps.Ticker)
        indxx = wig20_40_comps[wig20_40_comps.Ticker == ticker].indx.values[0]
        share = wig20_40_comps[wig20_40_comps.Ticker ==
                               ticker].Udział.values[0]

        print(f'wylosowano {ticker}')

        if ticker in last_10_tickers:
            print(f'{ticker} na liscie 10 ostatnich')
            print('ponowne losowanie')
            return do_chart()

        pts = analysts_pts.do_chart(ticker)

        if pts:
            pt_bull, pt_bear, pt_mean, last_close, nr_of_analyst = pts

            text = f"""Analyst Price Targets for {ticker}
            
📈 BULL {pt_bull:.2f} ({pt_bull/last_close - 1:.2%})
📉 BEAR {pt_bear:.2f} ({pt_bear/last_close - 1:.2%})
📊 MEAN {pt_mean:.2f} ({pt_mean/last_close - 1:.2%})

% of the WIG{indxx}     {share} 
last close         {last_close:.2f}
number of analysts {nr_of_analyst:.0f}

source: yfinance
#GPW #WIG{indxx} #WIG #{ticker} #giełda #akcje #python #project"""

            print(text)
            tweet_charts(text, [f'{ticker}_pts.png'])

            print('analyst_pts chart tweeted')

            os.remove(f'{ticker}_pts.png')
            print('analyst_pts chart removed')

        else:
            print(f'za malo opinii dla {ticker}')
            print('nowe losowanie')
            return do_chart()

        with open('last_10_pts_posts_tickers.txt', 'a', encoding='UTF-8') as f:
            f.write(f',{ticker}')

    do_chart()


def main():

    td = dt.today()
    tmr = td + timedelta(1)

    # kazdego sprawdzaj rekomendacje
    analyst_recs = analyst_rec.analyst_recomendations()
    if analyst_recs:
        tweet_only_text(text=analyst_recs)
    else:
        print('dzis bez postowania rekomendacji')


    # kazdego dnia postuj opcje
    if dni_opcje.is_good_day_to_post_option_charts():
        posting_option_charts()
    else:
        print('dzis bez postowania opcji')

    # w poniedzialki postuj analyst pts
    if td.isoweekday() == 1:
        posting_analyst_pts()
    else:
        print('dzis bez postowania pts')

    print('wszystko ukonczone sukcesem')


if __name__ == '__main__':
    main()
    pass