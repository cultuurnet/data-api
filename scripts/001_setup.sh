#!/bin/bash

gcloud components update
gcloud auth login
gcloud auth application-default login
gcloud auth configure-docker
gcloud components install docker-credential-gcr
