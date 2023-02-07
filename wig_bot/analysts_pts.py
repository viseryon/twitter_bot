import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import timedelta, datetime as dt
import numpy as np


def wig20_40_components():
    wig20 = pd.read_html('https://www.biznesradar.pl/gielda/indeks:WIG20')[0]
    wig20['Ticker'] = wig20.Profil.str[:3]
    wig20.drop(['Czas', '1r 3m'], axis=1, inplace=True)
    wig20['indx'] = 20

    wig40 = pd.read_html('https://www.biznesradar.pl/gielda/indeks:mWIG40')[0]
    wig40['Ticker'] = wig40.Profil.str[:3]
    wig40.drop(['Czas', '1r 3m'], axis=1, inplace=True)
    wig40['indx'] = 40

    both = pd.concat([wig20, wig40])
    return both


def do_chart(ticker: str, polish=True):

    if polish:
        full_ticker = ticker + '.WA'
    else:
        full_ticker = ticker

    stonk = yf.Ticker(full_ticker)

    analyst_pts = stonk.get_analyst_price_target(as_dict=True)

    nr_of_analyst = analyst_pts[0]['numberOfAnalystOpinions']
    try:
        if nr_of_analyst < 3:
            print('too few analysts')
            return False
    except TypeError:
        print('got type error')
        print('yfinance zwrocilo cos dziwnego')
        return False

    history = stonk.history('6mo')
    history.reset_index(inplace=True)

    td = dt.today()
    mth_12 = td + timedelta(days=365)
    business_days = pd.date_range(td, mth_12, freq='B')
    b_days = len(business_days)

    dates_to_plot = np.append(history.Date.values, business_days.to_numpy())

    last_close = analyst_pts[0]['currentPrice']
    pt_bull = analyst_pts[0]['targetHighPrice']
    pt_bear = analyst_pts[0]['targetLowPrice']
    pt_mean = analyst_pts[0]['targetMeanPrice']

    lines = [np.linspace(last_close, pt, b_days)
             for pt in [pt_bull, pt_bear, pt_mean]]
    bull = np.append(history.Close.values, lines[0])
    bear = np.append(history.Close.values, lines[1])
    base = np.append(history.Close.values, lines[2])

    noww = dt.now()
    noww = noww.strftime(r'%Y/%m/%d %H:%M:%S')

    plt.style.use('dark_background')
    fig, ax = plt.subplots()
    fig.set_size_inches(11, 7)
    plt.tight_layout(pad=3)

    plt.plot(dates_to_plot, bull)
    plt.plot(dates_to_plot, bear)
    plt.plot(dates_to_plot, base)
    plt.legend(['High', 'Low', 'Mean'], fontsize='large')
    plt.title(f'Analyst Price Targets {full_ticker}', fontsize='xx-large')

    fig.text(0.1, 0.025, noww)
    fig.text(0.8, 0.025, 'source: yfinance')
    fig.text(
        0.4, 0.025, f'Number of Analyst Opinions {nr_of_analyst:.0f}', fontsize='large')
    plt.grid(which='both', alpha=0.5)
    plt.text(business_days[-1], bull[-1] + 0.5,
             f'{bull[-1]:_.2f}', fontsize='x-large', horizontalalignment='center',
             bbox=dict(facecolor='black', edgecolor='white', boxstyle='round'))
    plt.text(business_days[-1], bear[-1] + 0.5,
             f'{bear[-1]:_.2f}', fontsize='x-large', horizontalalignment='center',
             bbox=dict(facecolor='black', edgecolor='white', boxstyle='round'))
    plt.text(business_days[-1], base[-1] + 0.5,
             f'{base[-1]:_.2f}', fontsize='x-large', horizontalalignment='center',
             bbox=dict(facecolor='black', edgecolor='white', boxstyle='round'))

    fig.savefig(f'{ticker}_pts.png')
    print('chart saved')

    return pt_bull, pt_bear, pt_mean, last_close, nr_of_analyst


if __name__ == '__main__':
    do_chart('LPP')
    # wig20_40_components()
    pass
