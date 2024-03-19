from google.cloud import secretmanager

class Config:
    def get_api_key(self) -> str:
        # Replace with your actual Google Cloud project ID and secret name
        project_id = "cloud-composer-243010"
        secret_name = "geocoding-api-key"

        # Initialize the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # Build the secret version name
        secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        print("fetching secret {}".format(secret_version_name))
        try:
            # Access the secret version and decode the payload
            response = client.access_secret_version(name=secret_version_name)
            api_key = response.payload.data.decode("UTF-8")
            print("secret fetched")
            return api_key
        except Exception as e:
            return None  # Handle errors or exceptions here