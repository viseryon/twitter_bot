import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime as dt, timedelta
import plotly.express as px
import yahooquery as yq
plt.style.use('dark_background')


def wig20_do_chart():

    try:
        data = pd.read_html('https://www.bankier.pl/inwestowanie/profile/quote.html?symbol=WIG20', decimal=',', thousands='\xa0')[1]
    except:
        return False

    data['Zmiana procentowa'] = data['Zmiana procentowa'].str.replace(',', '.')
    data['Zmiana procentowa'] = data['Zmiana procentowa'].str.rstrip('%').astype(float)
    data.drop(columns=['Zmiana', 'Wpływ na indeks', 'Udział w obrocie', 'Udział w portfelu'], inplace=True)
    data.rename({'Zmiana procentowa':'Zmiana_pct'}, axis=1, inplace=True)
    data.Zmiana_pct /= 100

    data['Udzial'] = data.Kurs * data.Pakiet
    
    fig = px.treemap(
        data, 
        path=[px.Constant('     '), 'Ticker'],

        values='Udzial',
        color='Zmiana_pct',
        hover_name='Nazwa',
        color_continuous_scale=['#CC0000', '#353535', '#00CC00'],
        hover_data=['Kurs', 'Zmiana_pct'],
        custom_data=data[['Zmiana_pct', 'Nazwa', 'Ticker', 'Kurs']],

    )


    fig.update_traces(
        insidetextfont=dict(
            size=160,
        ),

        textfont=dict(
            size=40
        ),

        textposition='middle center',
        texttemplate='<br>%{customdata[2]}<br>    <b>%{customdata[0]:.2%}</b>     <br><sup><i>%{customdata[3]:.2f} zł</i><br></sup>',

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
        root=dict(color='#1a1a1a'),


    )

    fig.update_coloraxes(
        showscale=True,
        cmin=-0.03, cmax=0.03, cmid=0 ,
    )

    fig.update_layout(
        margin=dict(t=200, l=5, r=5, b=120),
        width=7680,
        height=4320,
        title=dict(
            text=f'INDEX WIG20 HEATMAP {dt.now():%Y/%m/%d}',
            font=dict(
                color='white',
                size=150,
            ),
            yanchor='middle', xanchor='center',
            xref='paper', yref='paper',
            x=0.5
        ),
        paper_bgcolor="#1a1a1a",
        # paper_bgcolor="rgba(0,0,0,0)",
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

    fig.add_annotation(
        text=('@SliwinskiAlan'),
        x=0.5, y=-0.025,#
        font=dict(
            family="Calibri",
            size=80,
            color='white'
        ),
        opacity=0.7,
        align="left",
    )


    # fig.show()
    fig.write_image('wig20_heatmap.png')
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
        coloraxis_colorbar=dict(
            title="",
            thicknessmode="pixels", thickness=130,
            tickvals=[-0.029, -0.02, -0.01, 0, 0.01, 0.02, 0.029],
            ticktext=['-3%', '-2%', '-1%', '0%', '+1%', '+2%', '+3%'],
            orientation='v',
            tickfont=dict(
                color='white',
                size=55,
            ),
            ticklabelposition='inside',
        ),
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

    
def wig_do_chart():

    try:
        data = pd.read_html('https://www.bankier.pl/inwestowanie/profile/quote.html?symbol=WIG', decimal=',', thousands='\xa0')[1]

    except:
        return False
    
    data['Zmiana procentowa'] = data['Zmiana procentowa'].str.replace(',', '.')
    data['Zmiana procentowa'] = data['Zmiana procentowa'].str.rstrip('%').astype(float)
    data.drop(columns=['Zmiana', 'Wpływ na indeks', 'Udział w obrocie', 'Udział w portfelu'], inplace=True)
    data.rename({'Zmiana procentowa':'Zmiana_pct'}, axis=1, inplace=True)
    data.Zmiana_pct /= 100

    data['Udzial'] = data.Kurs * data.Pakiet
    
    tickers = data.Ticker.to_list()
    tickers = [f'{tick}.WA' for tick in tickers]
    
    yq_data = yq.Ticker(tickers).summary_profile
    
    sector, industry = [], []
    for v in yq_data.values():
        sector.append(v['sector'])
        industry.append(v['industry'])
        
       
    rn = {
    "Financial Data & Stock Exchanges": "Financial Data<br>Stock Exchanges",
    'Utilities—Regulated Gas': 'Regulated Gas',
    'Utilities—Independent Power Producers': 'Independent<br>Power Producers',
    'Utilities—Renewable': 'Renewable',
    'Utilities—Regulated Electric': 'Regulated Electric',
    'Real Estate—Diversified': 'Diversified',
    'Real Estate Services': 'Services',
    'Real Estate—Development': 'Development',
    'Farm & Heavy Construction Machinery': 'Farm & Heavy<br>Construction Machinery',
    'Staffing & Employment Services': 'Staffing & Employment<br>Services',
    'Tools & Accessories': 'Tools<br>& Accessories',
    'Building Products & Equipment': 'Building Products<br>& Equipment',
    'Integrated Freight & Logistics': 'Integrated Freight<br>& Logistics',
    'Specialty Industrial Machinery': 'Specialty<br>Industrial Machinery',
    'Electrical Equipment & Parts': 'Electrical Equipment<br>& Parts',
    'Metal Fabrication': 'Metal<br>Fabrication',
    'Aerospace & Defense': 'Aerospace<br>& Defense',
    'Paper & Paper Products': 'Paper<br>& Paper Products',
    'Specialty Chemicals': 'Specialty<br>Chemicals',
    'Specialty Business Services': 'Specialty<br>Business Services',
    'Drug Manufacturers—Specialty & Generic': 'Drug Manufacturers<br>Specialty & Generic',
    'Medical Care Facilities': 'Medical Care<br>Facilities',
    'Medical Instruments & Supplies': 'Medical Instruments<br>& Supplies',
    'Pharmaceutical Retailers': 'Pharmaceutical<br>Retailers',
    'Electronic Components': 'Electronic<br>Components',
    'Scientific & Technical Instruments': 'Scientific & Technical<br>Instruments',
    'Electronics & Computer Distribution': 'Electronics<br>& Computer Distribution',
    'Furnishings, Fixtures & Appliances': 'Furnishings, Fixtures<br>& Appliances',
    'Travel Services': 'Travel<br<Services',
    'Information Technology Services': 'Information Technology<br>Services',
    'Software—Infrastructure': 'Software<br>Infrastructure',
    'Medical Devices': 'Medical<br>Devices',
    }
    
    industry = [rn.get(ind, ind) for ind in industry]
    
    data['Sector'] = sector
    data['Industry'] = industry
 

    fig = px.treemap(
        data, 
        path=[px.Constant('WIG'), 'Sector', 'Industry', 'Ticker'],

        values='Udzial',
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
        texttemplate='<br>%{customdata[2]}<br>    <b>%{customdata[0]:.2%}</b>     <br><sup><i>%{customdata[3]:.2f} zł</i><br></sup>',

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
        root=dict(color='#1a1a1a'),


    )

    fig.update_coloraxes(
        showscale=True,
        cmin=-0.03, cmax=0.03, cmid=0 ,
    )

    fig.update_layout(
        margin=dict(t=200, l=5, r=5, b=120),
        width=7680,
        height=4320,
        title=dict(
            text=f'INDEX WIG HEATMAP {dt.now():%Y/%m/%d}',
            font=dict(
                color='white',
                size=150,
            ),
            yanchor='middle', xanchor='center',
            xref='paper', yref='paper',
            x=0.5
        ),
        paper_bgcolor="#1a1a1a",
        # paper_bgcolor="rgba(0,0,0,0)",
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

    fig.add_annotation(
        text=('@SliwinskiAlan'),
        x=0.5, y=-0.025,#
        font=dict(
            family="Calibri",
            size=80,
            color='white'
        ),
        opacity=0.7,
        align="left",
    )


    # fig.show()
    fig.write_image('wig_heatmap.png')


    data['udzial_zmiana_pct'] = data.Udzial * data.Zmiana_pct
    sectors_change = data.groupby('Sector')['udzial_zmiana_pct'].sum() / data.groupby('Sector')['Udzial'].sum()
    
    sectors_change = sectors_change.sort_values(ascending=False)
    data = data.sort_values('Zmiana_pct', ascending=False)
    
    data_string = f'\n🟢 {data.Ticker.iloc[0]} {data.Nazwa.iloc[0]} {data.Zmiana_pct.iloc[0]:.2%}\n🔴 {data.Ticker.iloc[-1]} {data.Nazwa.iloc[-1]} {data.Zmiana_pct.iloc[-1]:.2%}\n\n'

    for i, (sector, change) in enumerate(sectors_change.items()):
        data_string += f'{i+1}. {sector} ->{change:>7.2%}\n'

    return data_string



if __name__ == '__main__':
    wig20_do_chart()