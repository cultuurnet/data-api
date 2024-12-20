import json
from google.cloud import secretmanager

class Config:
    def get_api_key(self) -> str:
        # Replace with your actual Google Cloud project ID and secret name
        project_id = "cloud-composer-243010"
        secret_name = "prod_geocoding_api_key"

        # Initialize the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # Build the secret version name
        secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        print("fetching secret {}".format(secret_version_name))
        try:
            # Access the secret version and decode the payload
            response = client.access_secret_version(name=secret_version_name)
            api_key = json.loads(response.payload.data.decode("UTF-8"))['key']
            print(f"secret fetched!")
            return api_key
        except Exception as e:
            print("error fetching secret: {}".format(e))
            return None  # Handle errors or exceptions here