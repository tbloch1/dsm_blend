import os
import time
import shutil
import requests
import argparse
import subprocess
import numpy as np
import xarray as xr
import rioxarray as rxr

from tqdm import tqdm
from io import BytesIO
from pyproj import Geod
from zipfile import ZipFile
from rioxarray import merge
from pyproj import Transformer
from OSGridConverter import latlong2grid

def grid2lidargrid(grid_ref):
    tile, east, north = grid_ref.split(' ')
    sub_tile = f'{east[0]}{north[0]}'
    
    if (int(east[1:3]) <= 45) & (int(north[1:3]) > 45):
        # sub_sub_tile = 'nw'
        sub_tile = f'{east[0]}0{north[0]}5'
    if (int(east[1:3]) <= 45) & (int(north[1:3]) <= 45):
        # sub_sub_tile = 'sw'
        sub_tile = f'{east[0]}0{north[0]}0'
    if (int(east[1:3]) > 45) & (int(north[1:3]) > 45):
        # sub_sub_tile = 'ne'
        sub_tile = f'{east[0]}5{north[0]}5'
    if (int(east[1:3]) > 45) & (int(north[1:3]) <= 45):
        # sub_sub_tile = 'se'
        sub_tile = f'{east[0]}5{north[0]}0'

    return f'{tile}{sub_tile}'


def get_latlon_bbox(lat, lon, extent_h, extent_v):

    geod = Geod(ellps="WGS84")

    for offset in range(10):
        if geod.inv(lon, lat, lon+0.01*offset, lat)[2] > (extent_h / 2):
            lon_offset = 0.01*(offset+1)
            break

    for offset in range(10):
        if geod.inv(lon, lat, lon, lat+0.01*offset)[2] > (extent_v / 2):
            lat_offset = 0.01*(offset+1)
            break
    
    min_lat = lat-lat_offset
    max_lat = lat+lat_offset
    min_lon = lon-lon_offset
    max_lon = lon+lon_offset

    lat_range = np.linspace(min_lat, max_lat, 10)
    lon_range = np.linspace(min_lon, max_lon, 10)

    coords = [(_lat, _lon) for _lat in lat_range for _lon in lon_range]

    return coords


def find_all_tiles(lat, lon, extent_h, extent_v):

    coord_range = get_latlon_bbox(lat, lon, extent_h, extent_v)
    grids = [str(latlong2grid(*_coord)) for _coord in coord_range]
    tiles = [grid2lidargrid(grid) for grid in grids]
    tiles = list(set(tiles))

    return tiles


def make_url(year, tile):
    return (
        'https://api.agrimetrics.co.uk/tiles/collections/survey/'
        + f'national_lidar_programme_dsm/{year}/1/'
        + f'{tile}?subscription-key=public'
    )


def valid_content(request_obj):
    '''
    If requested object too small, then it's probably not data.
    Experimenting shows 22 is probably the no-data len().
    '''
    return len(request_obj.content) > 1024


def make_data_folder(script_dir):
    os.makedirs('data', exist_ok=True)
    return 'data'


def request_to_da(request_obj, save_loc, year, tile):
    zf = ZipFile(BytesIO(request_obj.content), mode ='r')
    f = zf.namelist()
    with zf.open(f[0], 'r') as tif:
        da = rxr.open_rasterio(tif)
        (
            da
            .to_dataset(name='dsm')
            .to_zarr(f'{save_loc}/{year}_{tile}_dsm.zarr', mode='w')
        )
        crs = da.rio.crs
        da.close()
        da = (
            xr.open_zarr(f'{save_loc}/{year}_{tile}_dsm.zarr')
            .rio.write_crs(crs)
            ['dsm']
        )
        zf.close()

    zf = []
    return da


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--lat', type=float,
        help='Latitude (decimal)'
    )
    parser.add_argument(
        '--lon', type=float,
        help='Longitude (decimal)'
    )
    parser.add_argument(
        '--skip', type=str,
        help=(
            'If True, then skips downloading data, and ends script early.'
            + 'Useful if you are just re-rendering the same data'
        )
    )
    
    args = parser.parse_args()

    skip = args.skip.lower() not in ['false', 'f', 'no', 'n', '0', 0, False]
    if skip:
        quit()
    else:
        shutil.rmtree('data', ignore_errors=True)

    lat, lon = args.lat, args.lon

    aoi_grid = latlong2grid(latitude = lat, longitude = lon)

    extent_h = 5000
    extent_v = extent_h * 3/7

    script_dir = os.path.dirname(__file__)
    save_loc = make_data_folder(script_dir = script_dir)

    tiles = find_all_tiles(lat, lon, 5000, 5000)

    print('Downloading data')
    das = []
    for tile in tqdm(tiles):
        for year in range(2016, 2023):
            url = make_url(year, tile)
            r = requests.get(url)
            
            if valid_content(r):
                da = request_to_da(r, save_loc, year, tile)
                das.append(da)
                break # Break to next tile
            else:
                # Skip to next year to try
                time.sleep(5)
                continue
    
    if len(das) == 0:
        raise ValueError('No data at coords.')
    
    print('Formatting data')
    da = merge.merge_arrays(das)
    ds = da.to_dataset(name='dsm')
    ds.attrs = ds['dsm'].attrs
    ds['dsm'].attrs = {}

    ds = ds.rio.write_crs('EPSG:27700')
    ds.to_zarr(f'{save_loc}/dsm.zarr', mode='w')

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700")
    lon_, lat_ = transformer.transform(lat,lon)

    coord = ds.sel(y=lat_, x=lon_, method='nearest')
    coordx = coord.x.values
    coordy = coord.y.values
    loc_x = np.argwhere(ds.x.values == coordx)[0][0]
    loc_y = np.argwhere(ds.y.values == coordy)[0][0]

    (
        ds['dsm']
        .isel({
            'band': 0,
            'x': slice(int(loc_x - extent_h/2), int(loc_x + extent_h/2)),
            'y': slice(int(loc_y - extent_v/2), int(loc_y + extent_v/2))
        })
        .rio.to_raster(f'{save_loc}/dsm.tif')
    )