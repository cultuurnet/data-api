import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from functools import cache
from hashlib import md5
from importlib import resources as impresources
from time import sleep

import os
import geopandas as gpd
import httpx
import requests
import sys 
import traceback


from cachetools.func import ttl_cache
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query, Request
from pyproj import CRS, Transformer
from shapely.geometry import Point

from app.secretmanager import Config

from . import data


if (
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None
    or os.getenv("LOCAL_LOGGING", "False") == "True"
):
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s - %(name)s",
    )
else:
    import google.cloud.logging

    # Instantiate a client
    client = google.cloud.logging.Client()

    # Retrieves a Cloud Logging handler based on the environment
    # you're running in and integrates the handler with the
    # Python logging module. By default this captures all logs
    # at INFO level and higher
    client.setup_logging(log_level=logging.INFO)

    logger = logging.getLogger(__name__)
    # logger.addHandler(logging.StreamHandler())

if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") != None:
    logger.info("Starting with geo_coding enabled")
    config = Config()
    api_key = config.get_api_key()
else:
    logger.info("Starting with geo_coding disabled")
    api_key = ""

# Location of static file
statsector_parquet = impresources.files(data) / "statistical_sectors_2023.parquet"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()


app = FastAPI(lifespan=lifespan)

# Create a cache with a maximum size of 100 entries and a TTL of 600 seconds
address_cache = TTLCache(maxsize=100, ttl=600)

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
    request: Request,
    lat: float = Query(default=None, description="Latitude"),
    lon: float = Query(default=None, description="Longitude"),
    address: str = Query(default=None, description="Address"),
):
    redacted_address = "*" * len(address) if address is not None else None
    logger.info(
        f"Statsector calculations for lat: {lat}, lon: {lon}, address: {redacted_address}"
    )

    # Figure out lat and long (if needed, we do an address lookup)
    if lat is not None and lon is not None:
        if not isinstance(lat, float) or not isinstance(lon, float):
            raise HTTPException(
                status_code=400, detail="'lat' and 'lon' must be of type float."
            )

        # await asyncio.sleep(1)  # Simulate a slow response
    elif address is not None:
        # Additional validation: Ensure address is a string
        if not isinstance(address, str):
            return {"error": "'address' must be of type string."}
        lat, lon = await lookup_address(address, request)
    else:
        raise HTTPException(
            status_code=400,
            detail="Either both 'lat' and 'lon' or 'address' must be provided.",
        )

    logger.info(
        f"Continuing calculations for lat: {lat}, lon: {lon}, address: {redacted_address}"
    )

    # Transform to Lambert projection
    res_lam = transformer_w2l.transform(lat, lon)
    lam_coo = Point(res_lam[0], res_lam[1])

    try:
        # Look up coordinates in the file
        sector_results = statsectors[statsectors["geometry"].contains(lam_coo)]
        first_sector_result = sector_results.iloc[0]

        response = {
            "lat": lat,
            "lon": lon,
            "sector_id": first_sector_result["cd_sector"],
            "sector_name": first_sector_result["tx_sector_descr_nl"],
        }

        if first_sector_result["cd_sector"]:
            logger.debug(f"Found sector: {response['sector_id']}")
            return response
        else:
            return {"error": "Sector not found for the given coordinates"}
    except Exception as e:
        return {"error": str(e)}


# @ttl_cache(maxsize=10000, ttl=10 * 60)
async def lookup_address(address: str, request: Request):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": address,
        "key": api_key,
    }

    # Check if the result is already in the cache
    result = address_cache.get(address)
    if result is not None:
        logger.info(f"Address found in cache")
        return result[0], result[1]

    try:
        # We don't log the address, as it may contain sensitive information
        logger.info(f"Looking up address using Google Maps Geocoding API")

        # response = requests.get(base_url, params=params)

        requests_client = request.app.requests_client
        response = await requests_client.get(base_url, params=params)

        data = response.json()

        if response.status_code == 200:
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                lat = location["lat"]
                lon = location["lng"]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Geocoding API response status: {data['status']}",
                )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Internal request failed with status code: {response.status_code}",
            )
    except Exception as e:
        # Log an error, and correlate it with a guid, so we don't expose it to the end-user
        error_id = uuid.uuid4()
        exc_type, exc_value, exc_traceback = sys.exc_info()

        # Get formatted exception info
        error_details = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )

        logger.error(
            f"An error occurred ({error_id}):\n"
            f"Type: {exc_type.__name__}\n"
            f"Message: {str(e)}\n"
            f"Traceback:\n{error_details}"
        )
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred - error id: {error_id}"
        )

    # Store the result in the cache
    address_cache[address] = lat, lon
    return lat, lon


@app.post("/")
async def get_statsector_bq(request: Request, payload: dict):
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
        logger.info(f"request: {json.dumps(payload)}")
        mode = payload["userDefinedContext"]["mode"]
        field = payload["userDefinedContext"]["field"]

        logger.info(f"BigQuery mode set to {mode}")
        logger.info("Processing BigQuery batch of {}".format(len(payload["calls"])))

        results = []

        # Assemble all tasks
        if mode == "address":
            tasks = [
                get_statsector(request=request, address=call[0], lat=None, lon=None)
                for call in payload["calls"]
            ]
        elif mode == "coordinates":
            results = []
            logger.info(
                "Processing BigQuery coordinates batch of {}".format(
                    len(payload["calls"])
                )
            )
            tasks = [
                get_statsector(request=request, lat=call[0], lon=call[1], address=None)
                for call in payload["calls"]
            ]
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")

        # Wait for tasks to complete
        # Exceptions must be returned so we can handle them!
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process responses
        for response in responses:
            try:
                results.append(response[field])

            # Catch ALL issues that happened during processing or during the extraction of the field
            except Exception as e:
                logger.error(
                    f"Adding None to result due to {type(e).__name__} with details {str(e)} - on result: {response}"
                )
                results.append(None)

        logger.info(f"Done processing batch. Returning {len(results)} results.")
        return {"replies": results}
    except KeyError as e:
        print(f"KeyError: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload format")
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
