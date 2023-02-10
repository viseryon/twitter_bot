if __name__ == '__main__':
    import world_gov_bonds
    import my_maps
    import twitter
    import poland_bonds
else:
    from . import world_gov_bonds
    from . import my_maps
    from . import twitter
    from . import poland_bonds

import traceback
import os
from datetime import datetime as dt


def post_poland_yield_curve(client, api):

    print('starting post_poland_yield_curve')
    poland_bonds.do_chart()

    text = '''❕ THE SCARY LINE ❕\n
🗨 Rentowność polskich obligacji skarbowych i jej zmiana w ostanim miesiącu. 🗨

source: worldgovernmentbonds.com
#yield #poland #NBP #bonds #python #project'''

    to_post = ['poland_yield_curve.png']
    twitter.tweet_things(client, api, text, to_post)
    print('chart tweeted')

    os.remove('poland_yield_curve.png')
    print('chart removed')


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
    
    print('STARTING MAIN MAKRO_BOT')

    td = dt.today()

    # w niedziele
    try:
        if td.isoweekday() == 7:
            post_poland_yield_curve(client, api)
        else:
            print('dzisiaj bez postowania poland_yield_curve')
    except Exception as e:
        print('\npost_poland_yield_curve ZAKONCZONE NIEPOWODZENIEM\n')
        traceback.print_exception(e)
        print()
    else:
        print('post_poland_yield_curve zakonczone sukcesem')


    print('\nZAKONCZONO MAKRO MAIN')


if __name__ == '__main__':
    pass