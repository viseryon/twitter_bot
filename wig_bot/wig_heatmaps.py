import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime as dt, timedelta
import squarify
import plotly.express as px
plt.style.use('dark_background')


def wig20_do_chart():

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

    fig.savefig('wig20_heatmap.png', transparent=False, dpi=400)

    return True


def wig_sectors_do_chart():

    l = [
    'BANKI',
    'BUDOW',
    'CHEMIA',
    'NRCHOM', 
    'ENERG', 
    'INFO',
    'MEDIA',
    'PALIWA',
    'SPOZYW', 
    'GORNIC',
    'LEKI',
    'MOTO',
    'ODZIEZ',
    'GRY'
]

    lst = [f'WIG-{to}' for to in l]

    data = pd.DataFrame()
    try:
        for sector in lst:
            df = pd.read_html(f'https://www.bankier.pl/inwestowanie/profile/quote.html?symbol={sector}', decimal=',', thousands='\xa0')[1]
            df['Sector'] = [sector] * df.shape[0]
            data = pd.concat([data, df])
    except:
        return False
    

    data['Zmiana procentowa'] = data['Zmiana procentowa'].str.replace(',', '.')
    data['Zmiana procentowa'] = data['Zmiana procentowa'].str.rstrip('%').astype(float)
    data['Udział w portfelu'] = data['Udział w portfelu'].str.replace(',', '.')
    data['Udział w portfelu'] = data['Udział w portfelu'].str.rstrip('%').astype(float)
    data.drop(columns=['Zmiana', 'Wpływ na indeks', 'Udział w obrocie'], inplace=True)
    data.rename({'Zmiana procentowa':'Zmiana_pct', 'Udział w portfelu':'Udzial'}, axis=1, inplace=True)
    data.Zmiana_pct /= 100
    data.Udzial /= 100

    data['Pakiet_pln'] = data.Pakiet * data.Kurs

    data['zmiana_x_udzial'] = data.Zmiana_pct * data.Udzial

    fig = px.treemap(
        data, 
        path=[px.Constant('- - - I N D E K S Y - - -'), 'Sector', 'Ticker'],

        values='Pakiet_pln',
        color='Zmiana_pct',
        hover_name='Nazwa',
        color_continuous_scale=['#CC0000', '#353535', '#00CC00'],
        hover_data=['Kurs', 'Zmiana_pct'],
        custom_data=data[['Zmiana_pct', 'Nazwa', 'Ticker', 'Kurs', 'Sector']],

    )


    fig.update_traces(
        hovertemplate='<b>%{customdata[4]}</b><br><br>' +
        '<b>%{customdata[2]}</b> %{customdata[3]:.2f} %{customdata[0]:.2%}<br>' + 
        '%{customdata[1]}',
        insidetextfont=dict(
            size=120,
        ),

        textfont=dict(
            size=40
        ),

        textposition='middle center',
        texttemplate='%{customdata[2]}<br><b>%{customdata[0]:.2%}</b><br><sup><i>%{customdata[3]:.2f} zł</i></sup>',

        hoverlabel=dict(
            bgcolor='#444444',
            bordercolor='gold',
            font=dict(
                color='white',
                size=16
            )
        ),
        marker_line_width=3,
        marker_line_color='#1a1a1a',
        root=dict(color='#1a1a1a')

    )

    fig.update_coloraxes(
        showscale=True,
        cmin=-0.03, cmax=0.03, cmid=0 
    )

    fig.update_layout(
        margin=dict(t=200, l=5, r=5, b=120),
        width=7680,
        height=4320,
        title=dict(
            text=f'INDEKSY SEKTOROWE WIG {dt.now() + timedelta(hours=2):%Y/%m/%d}',
            font=dict(
                color='white',
                size=150,
            ),
            yanchor='middle', xanchor='center',
            xref='paper', yref='paper',
            x=0.5
        ),
        paper_bgcolor="#1a1a1a",
        colorway=['#D9202E', '#AC1B26', '#7F151D', '#3B6323', '#518A30','#66B13C'],
    )

    fig.add_annotation(
        text=("source: bankier.com"),
        x=0.90, y=-0.023,#
        font=dict(
            family="Calibri",
            size=80,
            color='white'
        ),
        opacity=0.7,
        align="left",
    )

    fig.add_annotation(
        text=(dt.now().strftime(r'%Y/%m/%d %H:%M')),
        x=0.1, y=-0.025,#
        font=dict(
            family="Calibri",
            size=80,
            color='white'
        ),
        opacity=0.7,
        align="left",
    )


    # fig.show()
    fig.write_image('wig_sectors_heatmap.png')

    return True

if __name__ == '__main__':
    wig20_do_chart()