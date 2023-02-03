if __name__ == '__main__':
    import world_gov_bonds
else:
    from . import world_gov_bonds

import geopandas as gpd
import pandas as pd
from datetime import datetime as dt
import matplotlib.pyplot as plt
plt.style.use('dark_background')


def get_europe_df() -> gpd.GeoDataFrame:

    europe = 'mapy/Europe.shp'
    europe_df = gpd.read_file(europe)
    europe_df.drop(['ORGN_NAME'], axis=1, inplace=True)
    europe_df.columns = ['Country', 'geometry']
    europe_df.set_index('Country', inplace=True)

    return europe_df


def get_world_df(region: str = 'World', russia: bool = False, only_independent: bool = True) -> gpd.GeoDataFrame:

    world = 'makro_bot/World_Countries.shp'
    world_df = gpd.read_file(world)
    world_df.columns = ['Country', 'geometry']
    world_df.set_index('Country', inplace=True)

    countries = pd.read_csv('makro_bot/country_continent.csv')
    countries.set_index('Country', inplace=True)
    region = region.lower().title()

    if region != 'World':
        countries = countries[countries.continent == region]

    if not russia and 'Russia' in countries.index:
        countries.drop('Russia', inplace=True)

    if only_independent:
        countries = countries[countries.dependent == 'False']

    merged_df = world_df.join(countries, how='right')
    return merged_df


def combine_df_with_map(df: pd.DataFrame, mapa: str = 'world', russia: bool = False, only_independent: bool = True) -> gpd.GeoDataFrame:

    map_df = get_world_df(region=mapa, russia=russia,
                          only_independent=only_independent)
    merged_df = map_df.join(df, how='right')

    return merged_df, map_df


def chart_stuff_on_map(df: pd.DataFrame, col: int, png_name: str, title: str = None, region: str = 'world', russia: bool = False, only_independent: bool = False) -> None:
    """save map with chosen data

    Args:
        df (pd.DataFrame): index has to be 'Country'
        col (int): # of the column, if > than # of columns -> 0
        png_name (str): ---
        title (str, optional): title of the chart, if not given -> title of the column
        region (str, optional): 'world' or continents
        russia (bool, optional): include russia
        only_independent (bool, optional): include dependecies
    """        

    if col >= df.shape[1]:
        col = 0
    col = df.columns[col]

    if not title:
        title = col

    ready_df, background_df = combine_df_with_map(
        df, region, russia=russia, only_independent=only_independent)

    fig, ax = plt.subplots(figsize=(16,9))
    backgournd = background_df.plot(ax=ax, color='grey')
    main_plot = ready_df.plot(
        ax=ax, column=col, legend=True, legend_kwds={'shrink': 0.5})

    ax.axis('off')
    ax.grid(alpha=0.5)
    # ax.annotate()
    plt.title(title)
    plt.tight_layout()
    plt.savefig(f'makro_bot/{png_name}.png', dpi=1000)

    return


if __name__ == '__main__':
    df = world_gov_bonds.get_gov_bonds()
    chart_stuff_on_map(df, 2, 'abd')
    pass
