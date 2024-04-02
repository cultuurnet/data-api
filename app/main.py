from functools import cache
from cachetools.func import ttl_cache

import logging
from importlib import resources as impresources
import uuid

import geopandas as gpd
import requests
from fastapi import FastAPI, Query, HTTPException
from pyproj import CRS, Transformer
from shapely.geometry import Point
from fastapi import HTTPException

from app.secretmanager import Config

from . import data

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

config = Config()
api_key = config.get_api_key()

# Location of static file
statsector_parquet = impresources.files(data) / 'statistical_sectors_2023.parquet'

app = FastAPI()

# Global setup

# Stat Sector uses Lambert projection
# So we have to have transformers, World Geodetic System to Lambert and back
# https://www.ngi.be/website/de-lambert-kaartprojectie-2/
crs_lambert = CRS.from_string("EPSG:31370")
crs_wgs = CRS.from_string("EPSG:4326")

transformer_l2w = Transformer.from_crs(crs_lambert, crs_wgs)
transformer_w2l = Transformer.from_crs(crs_wgs, crs_lambert)


# Cache this so the file is only read once (during lifecyle of container)
@cache
def get_statsectors():
    logger.info("reading file...")
    return gpd.read_parquet(statsector_parquet)

# The following file takes a short while to load
statsectors = get_statsectors()

@app.get("/", tags=["root"])
async def root():
    return {"message": "Statsector API"}


@app.get("/get-statsector/")
async def get_statsector(
    lat: float = Query(default=None, description="Latitude"),
    lon: float = Query(default=None, description="Longitude"),
    address: str = Query(default=None, description="Address"),
):
    
    # Figure out lat and long (if needed, we do an address lookup)
    if lat is not None and lon is not None:
        if not isinstance(lat, float) or not isinstance(lon, float):
            raise HTTPException(status_code=400, detail="'lat' and 'lon' must be of type float.")
    elif address is not None:
        # Additional validation: Ensure address is a string
        if not isinstance(address, str):
            return {"error": "'address' must be of type string."}
        lat, lon = lookup_address(address)
    else:
        raise HTTPException(status_code=400, detail="Either both 'lat' and 'lon' or 'address' must be provided.")

    # Transform to Lambert projection
    res_lam = transformer_w2l.transform(lat, lon)
    lam_coo = Point(res_lam[0], res_lam[1])

    try:
        # Look up coordinates in the file
        sector_results = statsectors[statsectors["geometry"].contains(lam_coo)]
        first_sector_result = sector_results.iloc[0]

        response = {
            "sector_id": first_sector_result["cd_sector"],
            "sector_name": first_sector_result["tx_sector_descr_nl"],
        }

        if first_sector_result["cd_sector"]:
            return response
        else:
            return {"error": "Sector not found for the given coordinates"}
    except Exception as e:
        return {"error": str(e)}

@ttl_cache(maxsize=10000, ttl=10 * 60)
def lookup_address(address: str):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": address,
        "key": api_key,
    }

    try:
        # We don't log the address, as it may contain sensitive information
        logger.info(f"Looking up address using Google Maps Geocoding API")

        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                lat = location["lat"]
                lon = location["lng"]
            else:
                raise HTTPException(status_code=400, detail=f"Geocoding API response status: {data['status']}")
        else:
            raise HTTPException(status_code=500, detail=f"Internal request failed with status code: {response.status_code}")
    except Exception as e:
        # Log an error, and correlate it with a guid, so we don't expose it to the end-user
        error_id = uuid.uuid4()
        logger.error(f"An error occurred ({error_id}): {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred - error id: {error_id}")
    
    return lat, lon
    

@app.post("/")
async def get_statsector_bq(payload: dict):
    """Example payload
    {
        "requestId": "124ab1c",
        "caller": "//bigquery.googleapis.com/projects/myproject/jobs/myproject:US.bquxjob_5b4c112c_17961fafeaf",
        "sessionUser": "test-user@test-company.com",
        "userDefinedContext": {
        "key1": "value1",
        "key2": "v2"
        },
        "calls": [
        [null, 1, "", "abc"],
        ["abc", "9007199254740993", null, null]
        ]
    }

    """
    try:
        mode = payload["userDefinedContext"]["mode"]
        field = payload["userDefinedContext"]["field"]
        if mode == "address":
            results = []
            for call in payload["calls"]:
                result = await get_statsector(address=call[0], lat=None, lon=None)
                results.append(result[field])
        
            return { "replies":  results } 

        elif mode == "coordinates":
            results = []
            for call in payload["calls"]:
                result = await get_statsector(lat=call[0], lon=call[1], address=None)
                results.append(result[field])
            
            return { "replies":  results } 
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")
    except KeyError as e:
        print(f'KeyError: {e}')
        raise HTTPException(status_code=400, detail="Invalid payload format")
    except Exception as e:
        print(f'Exception: {e}')
        raise HTTPException(status_code=500, detail=str(e))
