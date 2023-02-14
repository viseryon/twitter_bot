import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime as dt
import squarify
plt.style.use('dark_background')


def do_chart():

    try:
        df = pd.read_html('https://www.bankier.pl/inwestowanie/profile/quote.html?symbol=WIG20')[1]
    except:
        return False


    df.drop(columns=['Zmiana', 'Wpływ na indeks', 'Udział w obrocie', 'Pakiet'], inplace=True) 

    df.Kurs = df.Kurs / 10000
    df['Change'] = df['Zmiana procentowa']
    df['Zmiana procentowa'] = df['Zmiana procentowa'].str.replace(',', '.')
    df['Zmiana procentowa'] = df['Zmiana procentowa'].str.rstrip('%')

    df['Udział w portfelu'] = df['Udział w portfelu'].str.replace(',', '.')
    df['Udział w portfelu'] = df['Udział w portfelu'].str.rstrip('%')


    df[['Kurs', 'Zmiana procentowa', 'Udział w portfelu']] = df[['Kurs', 'Zmiana procentowa', 'Udział w portfelu']].astype(float)

    color_bin = [float('-inf'),-3,-1,0,1,3,float('+inf')]
    df['colors'] = pd.cut(df['Zmiana procentowa'], bins=color_bin, labels=['#D9202E', '#AC1B26', '#7F151D', '#3B6323', '#518A30','#66B13C'])

    df['Tick_Chn'] = df['Ticker'] + '\n' + df['Change']

    fig, ax = plt.subplots(figsize=(16,9))
    squarify.plot(
        df['Udział w portfelu'], 
        label=df['Tick_Chn'], 
        color=df['colors'], 
        alpha=0.8, 
        linewidth=2, edgecolor="black",
        text_kwargs={'fontsize':20, 'weight':'bold', 'color':'white'}, 
        norm_x=100, norm_y=125)

    fig.text(0.8, 0.00, 'source: bankier.pl', {'weight':'bold', 'fontsize':12})
    fig.text(0.1, 0.00, f'{dt.now():%Y-%m-%d %H:%M:%S}', {'weight':'bold','fontsize':12})

    plt.title(f'WIG20 HEATMAP - {dt.now():%d/%m}', fontsize=32)
    plt.tight_layout()
    plt.axis('off')

    fig.savefig('wig20_heatmap.png', transparent=False, dpi=800)

    return True

if __name__ == '__main__':
    do_chart()