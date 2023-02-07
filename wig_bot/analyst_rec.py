import pandas as pd
from datetime import datetime as dt


def analyst_recomendations():

    df = pd.read_html('https://strefainwestorow.pl/rekomendacje/lista-rekomendacji/wszystkie')[0]

    td = dt.today()
    td = dt.strftime(td, r'%d.%m.%Y')
    df.Rodzaj = df.Rodzaj.str.upper()
    df['Spółka'] = df['Spółka'].str.replace('*', '', regex=False)

    new_df = df[df['Data publ.'] == '23.01.2023']

    if new_df.empty:
        return False

    text = '📝 Nowe Rekomendacje 📝\n\n'
    for key, value in new_df.iterrows():
        
        if value[1] == 'KUPUJ':
            text += f'🟢 {value[0]:10}\nPT = {value[2]}'
        elif value[1] == 'REDUKUJ':
            text += f'🔴 {value[0]:10}\nPT = {value[2]}'
        elif value[1] == 'TRZYMAJ':
            text += f'🟡 {value[0]:10}\nPT = {value[2]}'
        elif value[1] == 'AKUMULUJ':
            text += f'🟢 {value[0]:10}\nPT = {value[2]}'
        elif value[1] == 'WYCENA':
            text += f'⚪ {value[0]:10}\nPT = {value[2]}'
        elif value[1] == 'SPRZEDAJ':
            text += f'🔴 {value[0]:10}\nPT = {value[2]}'
        elif value[1] == 'NEUTRALNA':
            text += f'🔵 {value[0]:10}\nPT = {value[2]}'
        elif value[1] == 'ZAWIESZONA':
            text += f'⚫ {value[0]:10}\nPT = {value[2]}'
        else:
            text += f'🟤 {value[0]:10}\nPT = {value[2]}'
            text += f'{value[6]:}\n\n'
            continue

        if type(value[4]) != float:
            text += f' ({value[4]})'

        text += f'\n{value[6]:} -> {value[1]:}\n\n'

    text += '#GPW #WIG #giełda #akcje #python #project'


    return text