import pandas as pd
from datetime import timedelta, datetime as dt
import requests
from bs4 import BeautifulSoup

def get_gov_bonds():
    gov_bonds = pd.read_html('http://www.worldgovernmentbonds.com/')[1]
    gov_bonds.columns = gov_bonds.columns.droplevel()
    gov_bonds.drop(['Unnamed: 0_level_1', 'Unnamed: 4_level_1'],
                   axis=1, inplace=True)

    gov_bonds.Country = gov_bonds.Country.str.replace('[(*)]', '', regex=True)
    gov_bonds.Country = gov_bonds.Country.str.rstrip(' ')

    gov_bonds['S&P'] = gov_bonds['S&P'].astype('category')

    gov_bonds.Yield = gov_bonds.Yield.str.replace('%', '', regex=True)
    gov_bonds.Yield = gov_bonds.Yield.astype(float).round(3)

    gov_bonds.Rate = gov_bonds.Rate.str.replace('%', '', regex=True)
    gov_bonds.Rate = gov_bonds.Rate.astype(float).round(2)

    gov_bonds.Bund = gov_bonds.Bund.str.replace(' bp', '', regex=True)
    gov_bonds.Bund = gov_bonds.Bund.astype(float).round(1)

    gov_bonds['T-Note'] = gov_bonds['T-Note'].str.replace(
        ' bp', '', regex=True)
    gov_bonds['T-Note'] = gov_bonds['T-Note'].astype(float).round(1)

    gov_bonds.columns = ['Country', 'S&P',
                         'Yield_(%)', 'Rate_(%)', 'Bund_(bp)', 'TNote_(bp)']

    gov_bonds.set_index('Country', inplace=True)

    return gov_bonds


def get_credit_ratings():
    credit_ratings = pd.read_html(
        'http://www.worldgovernmentbonds.com/world-credit-ratings/')[0]
    credit_ratings.drop(['Unnamed: 0'], axis=1, inplace=True)
    credit_ratings[credit_ratings == '-'] = None
    credit_ratings.set_index('Country', inplace=True)

    return credit_ratings


def get_sov_cds():
    cds = pd.read_html('http://www.worldgovernmentbonds.com/sovereign-cds/')[0]

    cds.columns = cds.columns.droplevel()
    cds.drop(['Unnamed: 0_level_1'], axis=1, inplace=True)
    cds.columns = ['Country', 'S&P Rating', '5Y CDS',
                   'Var 1m (%)', 'Var 6m (%)', 'PD (%)', 'Date']

    cds['Var 1m (%)'] = cds['Var 1m (%)'].str.replace(' %', '')
    cds['Var 6m (%)'] = cds['Var 6m (%)'].str.replace(' %', '')
    cds['PD (%)'] = cds['PD (%)'].str.replace(' %', '')

    cds[['5Y CDS', 'Var 1m (%)', 'Var 6m (%)', 'PD (%)']] = cds[[
        '5Y CDS', 'Var 1m (%)', 'Var 6m (%)', 'PD (%)']].astype(float)
    cds['S&P Rating'] = cds['S&P Rating'].astype('category')
    cds.set_index('Country', inplace=True)

    return cds


def get_cb_rates_and_changes() -> pd.DataFrame:

    link = 'http://www.worldgovernmentbonds.com/central-bank-rates/'
    cb_rates = pd.read_html(link)[0]
    clm = cb_rates.columns[0]
    cb_rates.drop(columns=clm, inplace=True)

    cb_rates['Central Bank Rate'] = cb_rates['Central Bank Rate'].str.replace(' %', '')
    cb_rates['Variation'] = cb_rates['Variation'].str.replace(' bp', '')
    cb_rates.columns = ['Country', 'Rate_(%)', 'Variation_(%)', 'Period']
    cb_rates[['Rate_(%)', 'Variation_(%)']] = cb_rates[['Rate_(%)', 'Variation_(%)']].astype(float)
    cb_rates.set_index('Country', inplace=True)

    return cb_rates


def get_news():
    link = 'http://www.worldgovernmentbonds.com/latest-news/'
    r = requests.get(link).text
    soup = BeautifulSoup(r, features='lxml')

    a = [x.text for x in soup.find_all('p', {'class': 'w3-small'})]

    a = [x.split('\n') for x in a]

    cb_rates_changes = []
    ratings_changes = []
    rates_change = True
    for news in a:
        if news == '\n\n\n See all Central Bank Rates\n\n':
            rates_change = False
            continue

        if news == '\n\n\n See all Countries Credit Ratings\n\n':
            continue

        if rates_change:
            cb_rates_changes.append(news)
        else:
            ratings_changes.append(news)

    return cb_rates_changes, ratings_changes


if __name__ == '__main__':
    pass
