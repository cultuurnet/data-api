#! env /bin/bash

# Local docker build

poetry export -f requirements.txt --output requirements.txt
docker build . -t statsector