if __name__ == '__main__':
    import wig20_options
    import analysts_pts
    import analyst_rec
    import twitter
    import option_mispricing
    import wig_bot.wig_heatmaps as wig_heatmaps
    import dni_opcje
else:
    from . import wig20_options
    from . import analysts_pts
    from . import analyst_rec
    from . import twitter
    from . import option_mispricing
    from . import wig_heatmaps
    from . import dni_opcje

import pandas as pd
import time
import traceback
import os
import numpy as np
from datetime import timedelta, datetime as dt


def posting_wig20_heatmap(client, api):
    print('starting posting_wig20_heatmap')

    if not dni_opcje.is_good_day_to_post_option_charts():
        print('dzisiaj bez postowania wig20_heatmap')
        return
    
    wig_heatmaps.wig20_do_chart()

    text = f'''📈 WIG20 HEATMAP 📉

#WIG20 #WIG #giełda #python #project
'''

    to_post = ['wig20_heatmap.png']
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print('wig20_heatmap chart removed')

    pass


def posting_wig_sectors_heatmap(client, api):
    print(f'starting posting_wig_sectors_heatmap')

    if not dni_opcje.is_good_day_to_post_option_charts():
        print('dzisiaj bez postowania wig_sectors_heatmap')
        return
    
    wig_heatmaps.wig_sectors_do_chart()

    text = f'''📈 INDEKSY SEKTOROWE WIG w 8K! 📉

Wielkości pól odpowiadają wielkości pakietów akcji w indeksie, nie kapitalizacji rynkowej spółki.

#WIG20 #WIG #indices #index #giełda #python #project
'''

    to_post = ['wig_sectors_heatmap.png']
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print('wig_sectors_heatmap chart removed')

    pass


def posting_option_mispricing(client, api):

    print('starting posting_option_mispricing')

    df = wig20_options.get_todays_options_quotes()
    if type(df) != pd.DataFrame:
        print('dzisiaj bez postowania option_mispricing')
        return False

    option_mispricing.do_charts(
        wig20_options.get_wig20(), df)

    text = f'''📊 WIG20 OPTIONS MISPRICING 📊

Opcje, których cena rynkowa znacznie różni się od ceny implikowanej na podstawie trójmianowego modelu wyceny opcji.

#WIG20 #WIG #options #opcje #giełda #python #project
'''

    to_post = ['undervalued.png', 'overvalued.png']
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print('option_mispricing charts removed')

    pass


def posting_option_charts(client, api):
    print('starting posting_option_charts')

    if not wig20_options.do_charts():
        print('dzis bez postowania opcji')
        return False

    print('wig20_options charts generated')
    charts = [x for x in os.listdir() if x.endswith('.png')]
    charts.sort()
    print(charts)
    to_post = charts[:2] + [charts[-2]]
    to_post = list(set(to_post))
    to_post.sort()
    to_post.insert(0, 'all.png')
    print(to_post)

    text = '''💡 OPCJE NA INDEX WIG20 💡

📈 Jak opcje wyceniają prawdopodobieństwo osiągnięcia danego strike'a po dzisiejszej sesji? 📉

#GPW #WIG20 #WIG #options #opcje #giełda #python #project'''

    twitter.tweet_things(client, api, text, to_post)

    for chart in charts:
        os.remove(chart)

    print('wig20_option charts removed')


def posting_analyst_pts(client, api):
    print('starting posting_analyst_pts')
    wig20_40_comps = analysts_pts.wig20_40_components()

    losowania = 0
    def do_chart():

        ticker = np.random.choice(wig20_40_comps.Ticker)
        indxx = wig20_40_comps[wig20_40_comps.Ticker == ticker].indx.values[0]
        share = wig20_40_comps[wig20_40_comps.Ticker ==
                               ticker].Udział.values[0]

        print(f'wylosowano {ticker}')

        pts = analysts_pts.do_chart(ticker)
        if pts:
            pt_bull, pt_bear, pt_mean, last_close, nr_of_analyst = pts

            text = f"""Analyst Price Targets for {ticker}
            
📈 BULL {pt_bull:_.2f} ({pt_bull/last_close - 1:.2%})
📉 BEAR {pt_bear:_.2f} ({pt_bear/last_close - 1:.2%})
📊 MEAN {pt_mean:_.2f} ({pt_mean/last_close - 1:.2%})

% of the WIG{indxx}: {share} 
# of analysts: {nr_of_analyst:.0f}
last close: {last_close:_.2f}

source: yfinance
#GPW #WIG{indxx} #WIG #{ticker} #giełda #akcje #python #project"""

            print(text)
            twitter.tweet_things(client, api, text, [f'{ticker}_pts.png'])

            print('analyst_pts chart tweeted')

            os.remove(f'{ticker}_pts.png')
            print('analyst_pts chart removed')

        else:
            print('nowe losowanie')
            nonlocal losowania
            losowania += 1
            if losowania == 5:
                print('za duzo bledow od yfinance')
                print('dzis bez postowania analyst_pts')
                return
            return do_chart()


    do_chart()


def clean_dir_from_pngs():
    '''remove all pngs'''
    pictures = [x for x in os.listdir() if x.endswith('.png')]

    for picture in pictures:
        os.remove(picture)


def main(client, api):

    print('STARTING MAIN WIG_BOT')

    td = dt.today()
    tmr = td + timedelta(1)

    time.sleep(2)
    # kazdego sprawdzaj rekomendacje
    try:
        analyst_recs = analyst_rec.analyst_recomendations()
        if analyst_recs:
            twitter.tweet_things(client, api, text=analyst_recs)
        else:
            print('dzis bez postowania rekomendacji')
    except Exception as e:
        print('\nanalyst_recs ZAKONCZONE NIEPOWODZENIEM\n')
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print('cleaned dir from pngs')
    else:
        print('analyst_recs zakonczone sukcesem')


    time.sleep(2)
    # kazdego dnia postuj opcje
    try:
        posting_option_charts(client, api)
    except Exception as e:
        print('\nposting_option_charts ZAKONCZONE NIEPOWODZENIEM\n')
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print('cleaned dir from pngs')

    else:
        print('posting_option_charts zakonczone sukcesem')



    time.sleep(2)
    # w soboty postuj analyst pts
    try:
        if td.isoweekday() == 6:
            posting_analyst_pts(client, api)
        else:
            print('dzis bez postowania pts')
    except Exception as e:
        print('\nposting_analyst_pts ZAKONCZONE NIEPOWODZENIEM\n')
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print('cleaned dir from pngs')

    else:
        print('posting_analyst_pts zakonczone sukcesem')


    time.sleep(2)
    # kazdego dnia rob mispricing
    try:
        posting_option_mispricing(client, api)
    except Exception as e:
        print('\nposting_option_mispricing ZAKONCZONE NIEPOWODZENIEM\n')
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print('cleaned dir from pngs')

    else:
        print('posting_option_mispricing zakonczone sukcesem')


    time.sleep(2)
    # kazdego dnia rob wig20_heatmap
    try:
        posting_wig20_heatmap(client, api)
    except Exception as e:
        print('\nposting_wig20_heatmap ZAKONCZONE NIEPOWODZENIEM\n')
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print('cleaned dir from pngs')

    else:
        print('posting_wig20_heatmap zakonczone sukcesem')


    time.sleep(2)
    # kazdego dnia rob wig_sectors_heatmap
    try:
        posting_wig_sectors_heatmap(client, api)
    except Exception as e:
        print('\nposting_wig_sectors_heatmap ZAKONCZONE NIEPOWODZENIEM\n')
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print('cleaned dir from pngs')

    else:
        print('posting_wig_sectors_heatmap zakonczone sukcesem')
    
    print('\nZAKONCZONO WIG20 MAIN\n')


if __name__ == '__main__':
    pass
