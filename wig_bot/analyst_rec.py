import requests
import pandas as pd
from datetime import datetime as dt


def analyst_recomendations():

    header = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}
    link = 'https://www.stockwatch.pl/rekomendacje/'
    
    r = requests.get(link, headers=header).text

    df = pd.read_html(r)[0]

    td = dt.today()
    td = dt.strftime(td, r'%Y-%m-%d')

    df = df[df['Data wydania'] == td]

    if df.empty:
        return False

    df.Rekomendacja = df.Rekomendacja.str.upper()

    text = 'Nowe Rekomendacje 📝\n\n\n'
    for key, value in df.iterrows():
        if value[1] == 'KUPUJ':
            text += f'🟢 {value[0]:10} PT = {value[2]}\n'
        elif value[1] == 'REDUKUJ':
            text += f'🔴 {value[0]:10} PT = {value[2]}\n'
        elif value[1] == 'TRZYMAJ':
            text += f'🟡 {value[0]:10} PT = {value[2]}\n'
        elif value[1] == 'AKUMULUJ':
            text += f'🟡🟢 {value[0]:10} PT = {value[2]}\n'
        else:
            text += f'⚫ {value[0]:10} PT = {value[2]}\n'
            text += f'{value[6]:}\n\n'
            continue
        text += f'{value[6]:} rekomenduje {value[1]:}\n\n'

    text += '#GPW #WIG #giełda #akcje #python #project'

    return text