#!/bin/bash

gcloud config set run/region europe-west1
gcloud config set project cloud-composer-243010

poetry export -f requirements.txt --output requirements.txt
gcloud run deploy statsector --port 8080 --source . --no-allow-unauthenticated --memory 1G