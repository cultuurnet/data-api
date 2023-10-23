#!/bin/bash

poetry install
poetry run uvicorn app.main:app --reload
