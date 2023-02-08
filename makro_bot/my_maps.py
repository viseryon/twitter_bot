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


def get_world_df(region: str = 'World', russia: bool = False, only_independent: bool = True, antarctica: bool = False) -> gpd.GeoDataFrame:

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

    if not antarctica:
        countries = countries[countries.continent != 'Antarctica']

    merged_df = world_df.join(countries, how='right')
    return merged_df


def combine_df_with_map(df: pd.DataFrame, mapa: str = 'world', russia: bool = False, only_independent: bool = True, antarctica: bool = False) -> gpd.GeoDataFrame:

    map_df = get_world_df(region=mapa, russia=russia,
                          only_independent=only_independent)
    merged_df = map_df.join(df, how='right')

    return merged_df, map_df


def chart_stuff_on_map(df: pd.DataFrame, col: int, png_name: str, title: str = None, region: str = 'world', russia: bool = False, only_independent: bool = False, antarctica: bool = False) -> None:
    """save map with chosen data

    Args:
        df (pd.DataFrame): index has to be 'Country'
        col (int): # of the column, if > than # of columns -> 0
        png_name (str): ---
        title (str, optional): title of the chart, if not given -> title of the column
        region (str, optional): 'world' or continents
        russia (bool, optional): include russia
        only_independent (bool, optional): include dependecies
        antarctica (bool, optional): include antarctica
    """

    if col >= df.shape[1]:
        col = 0
    col = df.columns[col]

    if not title:
        title = col

    ready_df, background_df = combine_df_with_map(
        df, region, russia=russia, only_independent=only_independent)

    fig, ax = plt.subplots(figsize=(13, 7))
    backgournd = background_df.plot(ax=ax, color='grey')
    main_plot = ready_df.plot(
        ax=ax, column=col, legend=True, legend_kwds={'shrink': 0.5})

    ax.axis('off')
    ax.grid(visible=True, alpha=1, which='both', axis='both')
    fig.text(x=0.5, y=0.1, s='source: worldgovernmentbonds.com', color='grey')

    plt.title(title, fontsize='xx-large', horizontalalignment='center')
    plt.tight_layout()
    plt.savefig(f'{png_name}.png', dpi=500)

    return


if __name__ == '__main__':
    pass
