import geopandas as gpd
import pandas as pd


def get_europe_df() -> gpd.GeoDataFrame:

    europe = 'mapy/Europe.shp'
    europe_df = gpd.read_file(europe)
    europe_df.drop(['ORGN_NAME'], axis=1, inplace=True)
    europe_df.columns = ['Country', 'geometry']
    europe_df.set_index('Country', inplace=True)

    return europe_df


def get_world_df(region: str = 'World') -> gpd.GeoDataFrame:

    world = 'makro_bot/World_Countries.shp'
    world_df = gpd.read_file(world)
    world_df.columns = ['Country', 'geometry']
    world_df.set_index('Country', inplace=True)

    countries = pd.read_csv('makro_bot/country_continent.csv')
    countries.set_index('Country', inplace=True)
    region = region.lower().title()

    if region == 'Europe':
        return get_europe_df()

    elif region != 'World':
        countries = countries[countries.continent == region]

    merged_df = world_df.join(countries)
    return merged_df


def combine_df_with_map(df: pd.DataFrame, mapa: str = 'world') -> gpd.GeoDataFrame:

    if mapa == 'world':
        map_df = get_world_df()
    elif mapa == 'europe':
        map_df = get_europe_df()
    else:
        map_df = get_world_df()

    merged_df = map_df.join(df, how='right')

    return merged_df


if __name__ == '__main__':
    df = get_world_df()
    print(df.columns)
