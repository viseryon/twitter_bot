import yahooquery as yq
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import pandas as pd
from datetime import timedelta, datetime as dt
import numpy as np

plt.style.use("dark_background")


def wig20_40_components():
    wig20 = pd.read_html("https://www.biznesradar.pl/gielda/indeks:WIG20")[0]
    wig20["Ticker"] = wig20.Profil.str[:3]
    wig20.drop(["Czas", "1r 3m"], axis=1, inplace=True)
    wig20["indx"] = 20

    wig40 = pd.read_html("https://www.biznesradar.pl/gielda/indeks:mWIG40")[0]
    wig40["Ticker"] = wig40.Profil.str[:3]
    wig40.drop(["Czas", "1r 3m"], axis=1, inplace=True)
    wig40["indx"] = 40

    both = pd.concat([wig20, wig40])
    return both


def do_chart(ticker: str, polish=True):
    if polish:
        full_ticker = ticker + ".WA"
    else:
        full_ticker = ticker

    stonk = yq.Ticker(full_ticker)

    nr_of_analysts = stonk.financial_data[full_ticker]["numberOfAnalystOpinions"]

    if nr_of_analysts < 3:
        print(f"za malo opinii dla {ticker}")
        return False

    history = stonk.history("1y")
    history = history.droplevel(0, axis=0)

    td = dt.today()
    mth_12 = td + timedelta(days=365)
    days_future = pd.date_range(td, mth_12)
    b_days = len(days_future)

    dates_to_plot = days_future.to_pydatetime()

    last_close = stonk.financial_data[full_ticker]["currentPrice"]
    pt_bull = stonk.financial_data[full_ticker]["targetHighPrice"]
    pt_bear = stonk.financial_data[full_ticker]["targetLowPrice"]
    pt_median = stonk.financial_data[full_ticker]["targetMedianPrice"]

    lines = [
        np.linspace(last_close, pt, b_days) for pt in [pt_bull, pt_bear, pt_median]
    ]

    bull = lines[0]
    bear = lines[1]
    base = lines[2]

    noww = dt.now()
    noww = noww.strftime(r"%Y/%m/%d %H:%M:%S")

    fig, ax = plt.subplots(figsize=(11, 7))

    plt.plot(dates_to_plot, bull, color="green", label="High", lw=3)
    plt.plot(dates_to_plot, bear, color="red", label="Low", lw=3)
    plt.plot(dates_to_plot, base, color="grey", label="Median", lw=3)
    plt.plot(history.index, history.adjclose, "gold")
    plt.legend(fontsize="large")
    plt.title(f"Analyst Price Targets: {full_ticker}", fontsize="xx-large", y=1.03)

    fig.text(0.1, 0.025, noww)
    fig.text(0.8, 0.025, "source: Yahoo Finance")
    fig.text(
        0.4,
        0.025,
        f"Number of Analysts' Targets: {nr_of_analysts:.0f}",
        fontsize="large",
    )
    fig.text(0.8, 0.92, "@SliwinskiAlan", {"color": "grey"})

    plt.grid(which="both", alpha=0.5)
    plt.gca().yaxis.set_major_formatter(StrMethodFormatter("{x:_.2f}"))

    plt.text(
        days_future[-1],
        bull[-1] + 0.5,
        f"{bull[-1]:_.2f} | {bull[-1] / last_close - 1:.2%}",
        fontsize="x-large",
        horizontalalignment="center",
        bbox=dict(facecolor="black", edgecolor="white", boxstyle="round"),
    )
    plt.text(
        days_future[-1],
        bear[-1] + 0.5,
        f"{bear[-1]:_.2f} | {bear[-1] / last_close - 1:.2%}",
        fontsize="x-large",
        horizontalalignment="center",
        bbox=dict(facecolor="black", edgecolor="white", boxstyle="round"),
    )
    plt.text(
        days_future[-1],
        base[-1] + 0.5,
        f"{base[-1]:_.2f} | {base[-1] / last_close - 1:.2%}",
        fontsize="x-large",
        horizontalalignment="center",
        bbox=dict(facecolor="black", edgecolor="white", boxstyle="round"),
    )

    fig.savefig(f"{ticker}_pts.png", dpi=700)
    print("chart saved")

    return pt_bull, pt_bear, pt_median, last_close, nr_of_analysts


if __name__ == "__main__":
    do_chart("LPP")
    # wig20_40_components()
    pass
