import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime as dt
import numpy as np
plt.style.use('dark_background')


def do_chart():

    df = pd.read_html('http://www.worldgovernmentbonds.com/country/poland/')[0]

    df.columns = ['a','Residual_Maturity','Last','Chg_1M','Chg_6M','b','c','d','e','Last_change']
    df.drop(columns=['a','b','c','d','e'], inplace=True)

    df.Last = df.Last.str.replace('%' ,'')
    df.Chg_1M = df.Chg_1M.str.replace('n.a.', '', regex=True)
    df.Chg_6M = df.Chg_6M.str.replace('n.a.', '', regex=True)
    df.Chg_1M = df.Chg_1M.str.replace(' bp', '', regex=True)
    df.Chg_6M = df.Chg_6M.str.replace(' bp', '', regex=True)
    df = df.replace('', np.nan, regex=True)
    df = df.replace('', np.nan, regex=True)

    df[['Chg_1M', 'Chg_6M', 'Last']] = df[['Chg_1M', 'Chg_6M', 'Last']].astype(float)

    df.dropna(inplace=True)

    fig, ax = plt.subplots(figsize=(16,9))
    ax.plot(df.Residual_Maturity, df.Last, linewidth=4, label='Current Yield Curve')
    ax.plot(df.Residual_Maturity, df.Last - df.Chg_1M / 100, linewidth=2, linestyle='-', color='grey', label='Yield Curve 1M ago')

    color = ['r' if y < 0 else 'g' for y in df.Chg_1M]
    bars = ax.bar(
        df.Residual_Maturity, df.Chg_1M / 100, 
        bottom=df.Last - df.Chg_1M / 100, color=color, width=0.1)
    
    ax.bar_label(
        bars, label_type='center', 
        fontsize=17, labels=[f'{x * 100:.0f} bp' for x in bars.datavalues], 
        bbox=dict(facecolor='black', edgecolor='white', boxstyle='round'))
    
    ax.yaxis.set_major_formatter('{x:.1f} %')
    
    plt.title('Poland Government Bonds - Yield Curve and 1M change', fontsize=25, pad=10)
    plt.xlabel('Maturities', fontsize=14, labelpad=10)
    plt.ylabel('Yield', fontsize=14)

    fig.text(0.75, 0.015, 'source: worldgovernmentbonds.com')
    fig.text(0.525, 0.015, '@SliwinskiAlan')
    fig.text(0.10, 0.015, f'{dt.now():%Y/%m/%d %H:%M:%S}')

    plt.legend(fontsize='x-large')
    plt.tight_layout()
    plt.grid(alpha=0.5, visible=True)
    plt.savefig('poland_yield_curve.png', dpi=450)

    return True

if __name__ == '__main__':
    do_chart()