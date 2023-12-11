import geopandas as gpd

# Download a new file from https://statbel.fgov.be/nl/open-data?category=209
# Select the geojson (ZIP) Belgische Lambert 1972 (EPSG: 31370) version
# Unzip the geojson file
statsectors = gpd.read_file('sh_statbel_statistical_sectors_31370_20230101.geojson')
statsectors.to_parquet(path='statistical_sectors_2023.parquet')

