import dataframe_image as dfi
import pandas as pd
from datetime import datetime as dt
import math
import numpy as np
import df2img


def crr_trinomial_tree(S, K, r, T, t, v, c_p):

    # S  : spot price
    # K  : strike
    # r  : riskless rate
    # T  : maturity (in yrs.)
    # t  : number of steps
    # v  : annualized volatility
    # c_p  : True of False

    # Calculate time increment
    dt = T / t

    # Set c_p of option
    if c_p:
        x = 1
    else:
        x = -1

    # Initialize tree
    crrTree = np.empty((2 * t + 1, 1))
    crrTree[:] = np.nan

    # Initialize tree parameters
    u = math.exp(v * math.sqrt(2 * dt))
    d = 1/u
    m = 1

    # Pu
    pu = ((math.exp(r*dt/2) - math.exp(-1*v*math.sqrt(dt/2))) /
          (math.exp(v*math.sqrt(dt/2)) - math.exp(-1*v*math.sqrt(dt/2))))**2
    # Pd
    pd = ((math.exp(v*math.sqrt(dt/2)) - math.exp(r*dt/2)) /
          (math.exp(v*math.sqrt(dt/2)) - math.exp(-1*v*math.sqrt(dt/2))))**2
    # Pm
    pm = 1 - (pu + pd)

    for row in range(0, 2*t + 1):

        St = S * u**(max(t - row, 0)) * d**(max(row - t, 0))
        crrTree[row, 0] = max(x * St - x * K, 0)

    for col in range(t-1, -1, -1):
        for row in range(0, col*2+1):

            # move backwards from previous prices
            Su = crrTree[row,  0]
            Sm = crrTree[row + 1, 0]
            Sd = crrTree[row + 2, 0]
            # Calcuate price on tree
            continuation = math.exp(-r * dt) * (pu * Su + pm * Sm + pd * Sd)

            # Determine price at current node
            crrTree[row, 0] = continuation

    return crrTree[0, 0]


def do_charts(wig20, df):

    import wig20_options
    wig20 = wig20_options.get_wig20()
    print('pobrano wig20')

    df = wig20_options.get_todays_options_quotes()
    print('pobrano opcje i ich kwotowania')

    td = dt.today()
    trinomial = []

    for indx, vals in df.iterrows():
        S = wig20
        K = vals[12]
        r = vals[3]
        v = vals[2] / 100

        c_p = vals[11]

        T = vals[10]
        T = dt.strptime(T, r'%Y-%m-%d')
        T = (T - td).days
        t = 500
        T = T / 365

        wynik = crr_trinomial_tree(S, K, r, T, t, v, c_p)
        trinomial.append(wynik)
    print('wyliczono imp_price')

    df['Implied Price'] = trinomial
    df['Implied Price'] = df['Implied Price'].round(2)

    df['Difference'] = (df['Implied Price'] / df.kurs - 1) * 100
    df['Difference'] = df['Difference'].astype(float).round(2)

    to_table = df[['title', 'exp_date', 'strike', 'c_p',
                   'kurs', 'Implied Price', 'Difference']].copy()

    to_table.rename({'title': 'Contract', 'exp_date': 'Expiration',
                    'strike': 'Strike', 'c_p': 'Type', 'kurs': 'Price'}, inplace=True, axis=1)
    to_table.loc[to_table.Type == True, 'Type'] = 'CALL'
    to_table.loc[to_table.Type == False, 'Type'] = 'PUT'

    print('przygotowano df do obrazkow')

    def apply_formatting(df: pd.DataFrame, title: str) -> None:
        formatowanie = df.style
        formatowanie = formatowanie.format({
            'Price': "{:.2f}",
            'Implied Price': "{:.2f}",
            'Difference': "{:.2f} %",
        })
        formatowanie = formatowanie.set_properties(**{'background-color': 'black',
                                                      'color': 'white',
                                                      'border-color': 'white'})
        formatowanie = formatowanie.set_table_styles(
            [{
                'selector': 'th',
                'props': [
                    ('background-color', 'black'),
                    ('color', 'cyan')]
            },
                {
                'selector': 'caption',
                    'props': [
                        ('background-color', 'black'),
                        ('color', 'white'),
                        ('font-size', '125%')]
            }])
        formatowanie = formatowanie.hide(axis="index")
        formatowanie = formatowanie.set_caption(title)

        if 'overvalued' in title:
            dfi.export(formatowanie, 'overvalued.png', dpi=700)
        else:
            dfi.export(formatowanie, 'undervalued.png', dpi=700)


    def new_formatting(df: pd.DataFrame, title: str) -> None:

        df = df.head(7)
        df.index = range(1, 8)

        df.Price = df.Price.map("{0:.2f}".format)
        df['Implied Price'] = df['Implied Price'].map("{0:.2f}".format)
        df['Difference'] = df['Difference'].map("{0:.2f}%".format)

        fig = df2img.plot_dataframe(
            df,
            col_width=[0.2,0.8,0.8,0.5,0.5,0.6,0.8,0.8],
            title=dict(
                text="This is a title starting at the x-value x=0.1",
                font_color="white",
                font_size=20,
                x=0.25,
                xanchor="left",
                yanchor='middle'
            ),
            tbl_header=dict(
                fill_color="black",
                font_color="cyan",
                font_size=14,
                align='center',
                line_width=0
            ),
            tbl_cells=dict(
                fill_color="black",
                font_color="white",
                line_width=0,
            ),
            fig_size=(800, 250),
            paper_bgcolor="black",
        )
        
        fig.add_annotation(text=f"{1}",
                        xref="paper", yref="paper",
                        font=dict(color='grey'),
                        x=0.05, y=0.0, showarrow=False)
        
        fig.add_annotation(text="source: gpw",
                        xref="paper", yref="paper",
                        font=dict(color='grey'),
                        x=0.95, y=0.0, showarrow=False)
        
        if 'overvalued' in title:
            fig.write_image('overvalued.png', scale=3)
        else:
            fig.write_image('undervalued.png', scale=3)

    overvalued = to_table.sort_values('Difference', ascending=True)
    overvalued = overvalued.head(7)
    undervalued = to_table.sort_values('Difference', ascending=False)
    undervalued = undervalued.head(7)

    new_formatting(overvalued, 'Most overvalued WIG20 options')
    print('zapisano obrazek overvalued')
    new_formatting(undervalued, 'Most undervalued WIG20 options')
    print('zapisano obrazek undervalued')


if __name__ == '__main__':
    do_charts(1, 1)
