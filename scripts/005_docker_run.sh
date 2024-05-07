#! env /bin/bash

# -ti is needed to pass ctrl-c to the container
# see: https://stackoverflow.com/questions/71620812/uvicorn-wont-quit-with-ctrlc
docker run -ti -p 8000:8080 statsector