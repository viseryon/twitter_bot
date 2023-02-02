from . import world_gov_bonds
from . import my_maps
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd


def chart_yields():
    df = world_gov_bonds.get_gov_bonds()
    ready_df, background_df = my_maps.combine_df_with_map(
        df, 'europe', russia=False, only_independent=False)

    fig, ax = plt.subplots()
    backgournd = background_df.plot(ax=ax, color='grey')
    fig = ready_df.plot(ax=ax, column='Yield_(%)', legend=True)
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('makro_bot/abd.png', dpi=1000)


def main(client, api):
    # chart_yields()
    pass

if __name__ == '__main__':
    main(1, 1)
