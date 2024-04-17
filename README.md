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