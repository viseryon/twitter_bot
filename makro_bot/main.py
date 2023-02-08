if __name__ == '__main__':
    import world_gov_bonds
    import my_maps
    import twitter
else:
    from . import world_gov_bonds
    from . import my_maps
    from . import twitter
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import calendar
import os
from datetime import datetime as dt


def post_cb_rates_map_changes(client, api):

    cb_rates = world_gov_bonds.get_cb_rates_and_changes()
    my_maps.chart_stuff_on_map(cb_rates, 0, 'cb_rates_map', 'Central Bank Interest Rates', russia=True)

    cb_rates_changes = cb_rates[cb_rates.Period == 'Jan 23'].dropna()
    t = ''
    for indx, value in cb_rates_changes.iterrows():
        v = int(value[1])
        if v > 0:
            t += f'{indx} +{v} bp\n'
        else:
            t += f'{indx} -{v} bp\n'

    text = f'''JAK ZMIENIŁY SIĘ STOPY PROCENTOWE BANKÓW CENTRALNYCH W OSTANIM MIESIĄCU?

{t}
#interest_rates #central_banks #python #project'''

    print(text)

    print('\n', len(text))
    # twitter.tweet_things(client, api, text, 'makro_bot/cb_rates_map.png')
    # print('chart tweeted')
    # os.remove('makro_bot/cb_rates_map.png')
    # print('chart removed')


    pass



def main(client, api):
    
    td = dt.today()
    # post_cb_rates_map_changes(1,1)
    # ostatni_dzien_msc = calendar.monthrange(td.year, td.month)[1]
    # if td.day == ostatni_dzien_msc:
    #     post_cb_rates_map_changes(client, api)
    # else:
    #     print('dzisiaj bez postowania cb_rates_map_changes')


    pass

if __name__ == '__main__':
    # main(1, 1)
    post_cb_rates_map_changes(1, 1)
