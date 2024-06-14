import os
import time
import traceback
from calendar import monthrange
from datetime import datetime as dt
from datetime import timedelta

import numpy as np
import pandas as pd

from . import dni_opcje, option_mispricing, twitter, wig20_options, wig_heatmaps


def posting_wig20_heatmap(client, api):
    print("starting posting_wig20_heatmap")

    if not dni_opcje.is_good_day_to_post_option_charts():
        print("dzisiaj bez postowania wig20_heatmap")
        return

    wig_heatmaps.wig20_do_chart()

    text = f"""📈 WIG20 HEATMAP 📉

Indeks WIG20 w nowej odsłonie!

#WIG20 #WIG #index #giełda #GPW #python #project
"""

    to_post = ["wig20_heatmap.png"]
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print("wig20_heatmap chart removed")

    pass


def posting_wig_sectors_heatmap(client, api):
    print(f"starting posting_wig_sectors_heatmap")

    if not dni_opcje.is_good_day_to_post_option_charts():
        print("dzisiaj bez postowania wig_sectors_heatmap")
        return

    data_string = wig_heatmaps.wig_sectors_do_chart()

    text = f"""📈 INDEKSY SEKTOROWE WIG 📉

{data_string}

#WIG20 #WIG #index #GPW #python
"""

    to_post = ["wig_sectors_heatmap.png"]
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print("wig_sectors_heatmap chart removed")

    pass


def posting_wig_sectors_heatmap_1w_perf(client, api):
    print("starting posting_wig_sectors_heatmap_1w_perf")

    data_string = wig_heatmaps.wig_sectors_do_chart_1w_perf()

    text = f"""📈 INDEKSY SEKTOROWE WIG 1W 📉

{data_string}

#WIG #GPW #python
"""

    to_post = ["wig_sectors_heatmap_1w_perf.png"]
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print("wig_sectors_heatmap_1w_perf chart removed")

    pass


def posting_wig_heatmap(client, api):
    print(f"starting posting_wig_heatmap")

    if not dni_opcje.is_good_day_to_post_option_charts():
        print("dzisiaj bez postowania wig_heatmap")
        return

    data_string = wig_heatmaps.wig_do_chart()

    text = f"""📈 WIG HEATMAP 📉
{data_string}
#WIG20 #WIG #index #giełda #GPW #python #project
"""

    to_post = ["wig_heatmap.png"]
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print("wig_heatmap chart removed")

    pass


def is_last_day_of_month():
    _, last_day = monthrange(dt.now().year, dt.now().month)

    if last_day == dt.today().day:
        return True

    return False


def posting_wig_heatmap_1m_perf(client, api):
    print(f"starting posting_wig_heatmap_1m_perf")

    data_string = wig_heatmaps.wig_do_chart_1m_perf()

    text = f"""📈 WIG HEATMAP {dt.now().strftime('%B %Y')} 📉
{data_string}
#WIG20 #WIG #index #giełda #GPW #python #project
"""

    to_post = ["wig_heatmap_1m_perf.png"]
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print("wig_heatmap_1m_perf chart removed")

    pass


def posting_wig_heatmap_1w_perf(client, api):
    print("starting posting_wig_heatmap_1w_perf")

    data_string = wig_heatmaps.wig_do_chart_1w_perf()

    text = f"""📈 WIG HEATMAP WEEK {dt.now():%W} 📉
{data_string}
#WIG20 #WIG #index #giełda #GPW #python #project
"""

    to_post = ["wig_heatmap_1w_perf.png"]
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print("wig_heatmap_1w_perf chart removed")


def posting_option_mispricing(client, api):
    print("starting posting_option_mispricing")

    df = wig20_options.get_todays_options_quotes()
    if type(df) != pd.DataFrame:
        print("dzisiaj bez postowania option_mispricing")
        return False

    option_mispricing.do_charts(wig20_options.get_wig20(), df)

    text = f"""📊 WIG20 OPTIONS MISPRICING 📊

Opcje, których cena rynkowa znacznie różni się od ceny implikowanej na podstawie trójmianowego modelu wyceny opcji.

#WIG20 #WIG #options #opcje #giełda #python #project
"""

    to_post = ["undervalued.png", "overvalued.png"]
    twitter.tweet_things(client, api, text, to_post)

    for chart in to_post:
        os.remove(chart)

    print("option_mispricing charts removed")

    pass


def posting_option_charts(client, api):
    print("starting posting_option_charts")

    if not wig20_options.do_charts():
        print("dzis bez postowania opcji")
        return False

    print("wig20_options charts generated")
    charts = [x for x in os.listdir() if x.endswith(".png")]
    charts.sort()
    print(charts)
    to_post = charts[:2] + [charts[-2]]
    to_post = list(set(to_post))
    to_post.sort()
    to_post.insert(0, "all.png")
    print(to_post)

    text = """💡 OPCJE NA INDEX WIG20 💡

📈 Jak opcje wyceniają prawdopodobieństwo osiągnięcia danego strike'a po dzisiejszej sesji? 📉

#GPW #WIG20 #WIG #options #opcje #giełda #python #project"""

    twitter.tweet_things(client, api, text, to_post)

    for chart in charts:
        os.remove(chart)

    print("wig20_option charts removed")


def posting_analyst_pts(client, api):
    print("starting posting_analyst_pts")
    wig20_40_comps = analysts_pts.wig20_40_components()

    losowania = 0

    def do_chart():
        ticker = np.random.choice(wig20_40_comps.Ticker)
        indxx = wig20_40_comps[wig20_40_comps.Ticker == ticker].indx.values[0]
        share = wig20_40_comps[wig20_40_comps.Ticker == ticker].Udział.values[0]

        print(f"wylosowano {ticker}")

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
            twitter.tweet_things(client, api, text, [f"{ticker}_pts.png"])

            print("analyst_pts chart tweeted")

            os.remove(f"{ticker}_pts.png")
            print("analyst_pts chart removed")

        else:
            print("nowe losowanie")
            nonlocal losowania
            losowania += 1
            if losowania == 5:
                print("za duzo bledow od yfinance")
                print("dzis bez postowania analyst_pts")
                return
            return do_chart()

    do_chart()


def clean_dir_from_pngs():
    """remove all pngs"""
    pictures = [x for x in os.listdir() if x.endswith(".png")]

    for picture in pictures:
        os.remove(picture)


def main(client, api):
    print("STARTING MAIN WIG_BOT")

    td = dt.today()
    tmr = td + timedelta(1)

    time.sleep(60 * 5)
    # kazdego sprawdzaj rekomendacje
    try:
        analyst_recs = analyst_rec.analyst_recomendations()
        if analyst_recs:
            twitter.tweet_things(client, api, text=analyst_recs)
        else:
            print("dzis bez postowania rekomendacji")
    except Exception as e:
        print("\nanalyst_recs ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")
    else:
        print("analyst_recs zakonczone sukcesem")

    time.sleep(60 * 5)
    # kazdego dnia postuj opcje
    try:
        posting_option_charts(client, api)
    except Exception as e:
        print("\nposting_option_charts ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")

    else:
        print("posting_option_charts zakonczone sukcesem")

    time.sleep(60 * 5)
    # w soboty postuj analyst pts
    try:
        if td.isoweekday() == 6:
            posting_analyst_pts(client, api)
        else:
            print("dzis bez postowania pts")
    except Exception as e:
        print("\nposting_analyst_pts ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")

    else:
        print("posting_analyst_pts zakonczone sukcesem")

    # time.sleep(60*5)
    # # kazdego dnia rob mispricing
    # try:
    #     posting_option_mispricing(client, api)
    # except Exception as e:
    #     print('\nposting_option_mispricing ZAKONCZONE NIEPOWODZENIEM\n')
    #     traceback.print_exception(e)
    #     print()
    #     clean_dir_from_pngs()
    #     print('cleaned dir from pngs')

    # else:
    #     print('posting_option_mispricing zakonczone sukcesem')

    time.sleep(60 * 5)
    # kazdego dnia rob wig20_heatmap
    try:
        posting_wig20_heatmap(client, api)
    except Exception as e:
        print("\nposting_wig20_heatmap ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")

    else:
        print("posting_wig20_heatmap zakonczone sukcesem")

    time.sleep(60 * 5)
    # kazdego dnia rob wig_sectors_heatmap
    try:
        posting_wig_sectors_heatmap(client, api)
    except Exception as e:
        print("\nposting_wig_sectors_heatmap ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")

    else:
        print("posting_wig_sectors_heatmap zakonczone sukcesem")

    time.sleep(60 * 5)
    # kazdego dnia rob wig_heatmap
    try:
        posting_wig_heatmap(client, api)
    except Exception as e:
        print("\nposting_wig_heatmap ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")

    else:
        print("posting_wig_heatmap zakonczone sukcesem")

    # ostatniego dnia msc rob wig_heatmap_1m_perf
    time.sleep(60 * 5)
    if td.day == 1:
        try:
            posting_wig_heatmap_1m_perf(client, api)
        except Exception as e:
            print("\nposting_wig_heatmap_1m_perf ZAKONCZONE NIEPOWODZENIEM\n")
            traceback.print_exception(e)
            print()
            clean_dir_from_pngs()
            print("cleaned dir from pngs")

        else:
            print("posting_wig_heatmap_1m_perf zakonczone sukcesem")
    else:
        print("dzisiaj bez postowania wig_heatmap_1m_perf")

    time.sleep(60 * 5)
    # w soboty postuj wig_heatmap_1w_perf
    try:
        if td.isoweekday() == 6:
            posting_wig_heatmap_1w_perf(client, api)
        else:
            print("dzis bez postowania wig_heatmap_1w_perf")
    except Exception as e:
        print("\nposting_wig_heatmap_1w_perf ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")

    else:
        print("posting_wig_heatmap_1w_perf zakonczone sukcesem")

    time.sleep(60 * 5)
    # w soboty postuj wig_sectors_heatmap_1w_perf
    try:
        if td.isoweekday() == 6:
            posting_wig_sectors_heatmap_1w_perf(client, api)
        else:
            print("dzis bez postowania wig_sectors_heatmap_1w_perf")
    except Exception as e:
        print("\nposting_wig_sectors_heatmap_1w_perf ZAKONCZONE NIEPOWODZENIEM\n")
        traceback.print_exception(e)
        print()
        clean_dir_from_pngs()
        print("cleaned dir from pngs")

    else:
        print("posting_wig_sectors_heatmap_1w_perf zakonczone sukcesem")

    print("\nZAKONCZONO WIG20 MAIN\n")


if __name__ == "__main__":
    pass
