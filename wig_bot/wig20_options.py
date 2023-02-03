import pandas as pd
import requests
import yfinance as yf
from datetime import datetime as dt
from matplotlib import pyplot as plt
plt.style.use('dark_background')


def get_options():
    r = requests.get(
        'https://www.gpw.pl/ajaxindex.php?action=DRGreek&start=list&format=html&lang=PL')
    date, df = pd.read_html(r.text, encoding='utf-8')

    df.set_index('Lp', inplace=True)
    df.columns = ['title', 'imp_vol', 'vol', 'rfr',
                  'div_y', 'delta', 'gamma', 'theta', 'vega', 'rho']
    df.iloc[:, 3:] /= 10_000
    df.iloc[:, 1:3] /= 100

    expirations = list(pd.date_range(
        '2023-01-01', '2023-12-31', freq='WOM-3FRI'))
    expirations = [str(x).split()[0] for x in expirations]

    options = dict()
    for i, exp in zip(range(65, 89), 2 * expirations):
        if i - 65 < 12:
            options[chr(i)] = [True, exp]
        else:
            options[chr(i)] = [False, exp]

    exp_date, c_p, strike = [], [], []
    for i, w in df.iterrows():
        exp_date.append(options[w['title'][4]][1])
        c_p.append(options[w['title'][4]][0])
        strike.append(int(w['title'][-4:]))

    df['exp_date'] = exp_date
    df['c_p'] = c_p
    df['strike'] = strike

    date = date.values.flatten()[0]
    date = date.split(' | ')[1]
    date = dt.strptime(date, r'%Y-%m-%d').date()

    return df, expirations, date


def get_wig20():

    noww = dt.now()
    noww = noww.strftime(r'%Y-%m-%d')
    wig20 = yf.download('WIG20.WA', noww)
    wig20 = wig20['Adj Close']

    return round(float(wig20), 2)


def do_charts():
    wig20 = get_wig20()
    options = get_options()

    noww = dt.now()
    noww = noww.strftime(r'%Y/%m/%d %H:%M:%S')

    chain, exp_dates, _ = options

    avb_dates = []

    def main_plot():

        fig, ax = plt.subplots()

        for i, date in enumerate(exp_dates):

            period_options = chain[chain.exp_date == date]

            if period_options.shape[0]:
                avb_dates.append(date)

                data = period_options.groupby('strike').mean(
                    numeric_only=True).delta + 0.5

                plt.plot(data, label=date)

        plt.tight_layout(pad=3, h_pad=4)
        plt.axvline(x=wig20, label='curr wig20',
                    ymin=0.1, ymax=0.9, ls='dashed')
        fig.text(0.1, 0.02, noww)
        fig.text(0.75, 0.02, 'source: www.gpw.pl')
        plt.ylabel('probability')
        plt.xlabel('strike')
        plt.grid(which='both', alpha=0.5)
        plt.title(f'Price target of WIG20 based on option contracts')
        plt.legend()
        fig.savefig('all.png', transparent=False)

        return ax

    def simple_plots():

        r = list()

        for date in avb_dates:
            period_options = chain[chain.exp_date == date]
            data = period_options.groupby('strike').mean(
                numeric_only=True).delta + 0.5

            fig, ax = plt.subplots()
            # f = plt.subplots()

            plt.plot(data, label=date)
            plt.tight_layout(pad=3, h_pad=4)
            plt.axvline(x=wig20, label='curr wig20',
                        ymin=0.1, ymax=0.9, ls='dashed')
            fig.text(0.1, 0.02, noww)
            fig.text(0.75, 0.02, 'source: www.gpw.pl')
            plt.ylabel('probability')
            plt.xlabel('strike')
            plt.grid(which='both', alpha=0.5)
            plt.title(
                f'Price target of WIG20 based on {date} option contracts')
            plt.legend()
            fig.savefig(f'{date}.png', transparent=False)

            r.append(ax)

        return r

    def both():
        r = [main_plot()]
        r.extend(simple_plots())
        return r

    return both()


if __name__ == '__main__':
    do_charts()
