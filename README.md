# Statsector API

## Dev environment setup

### Running the app in dev mode

We use poetry to manage dependencies.
If you don't have poetry installed, you can run `pip install poetry`, or install via e.g. Homebrew.


```sh
gcloud components update
gcloud auth login
gcloud auth application-default login
gcloud config set run/region europe-west1
gcloud config set project cloud-composer-243010
poetry install
poetry shell
uvicorn app.main:app --reload
```

### Running the tests

#### Unit Tests
```sh
poetry run python -m unittest discover -s tests
```
#### Performance Tests

The following tests can be run to test the performance of the API with e.g. caching enabled.

Testing the geo to statsector conversion
```sh
poetry run python -m tests.perftest_geo
```

Testing the address to statsector conversion

> Warning: Do not test this with too high loads and with caching disabled, 
> as it will result in a lot of requests to the Google Maps API, and increase costs.

```sh
poetry run python -m tests.perftest_address
```

### Deploying to Cloud Run

Make sure you ran the above steps first, as this also sets your config for Cloud Run.


```sh
gcloud auth configure-docker
gcloud components install docker-credential-gcr
poetry export -f requirements.txt --output requirements.txt
gcloud run deploy statsector --port 8080 --source .
```

### Issues

```sh
➜  statsector git:(main) ✗ gcloud run deploy statsector --port 8080 --source .       
ERROR: Error in retrieving repository from Artifact Registry.
ERROR: (gcloud.run.deploy) INVALID_ARGUMENT: Request contains an invalid argument.
```

This resulted from cloud build not having permissions:
was made Artifact registry admin, but in the end it was a wrong region setup.


## Providing API access

1. Create a service account in Google Cloud IAM
2. Create a json key for the service account and download it
3. Grant *invoker* access to the service account on the Cloud Run service


## Run your own statsector container

To run locally without any Python knowledge / requirements, build the docker image like this:

```sh
docker build . -t statsector
```

Then, you can start your container like this:

```sh
docker run -p 8000:8080 statsector
```

(or use any other docker tools you prefer)

Once your container is up-and-running, you will see this:
```
INFO:app.main:Starting with geo_coding disabled
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

And you can query statsectors like this:

```sh
curl 'http://localhost:8000/get-statsector/?lat=50.940&lon=4.204'
{
  "sector_id": "23052A0PA",
  "sector_name": "MERCHTEM-ZUID"
}
```

(or using the HTTP client of your language and choice)

Things to note:

- The statsector API endpoints are unauthenticated. If you want to run this in production, you will have to deal with this yourself.
- By default the app is `Starting with geo_coding disabled`. If you need geocoding (`?address=A real street with number, zipcode city`), you need to configure Google Cloud credentials.

