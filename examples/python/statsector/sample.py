import urllib

import google.auth.transport.requests
import google.oauth2.id_token


def make_authorized_get_request(endpoint, audience):
    """
    make_authorized_get_request makes a GET request to the specified HTTP endpoint
    by authenticating with the ID token obtained from the google-auth client library
    using the specified audience value.
    """

    # Cloud Run uses your service's hostname as the `audience` value
    # audience = 'https://my-cloud-run-service.run.app/'
    # For Cloud Run, `endpoint` is the URL (hostname + path) receiving the request
    # endpoint = 'https://my-cloud-run-service.run.app/my/awesome/url'

    req = urllib.request.Request(endpoint)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)

    req.add_header("Authorization", f"Bearer {id_token}")
    response = urllib.request.urlopen(req)

    return response.read()


# main function that calls the api
if __name__ == "__main__":
    result = make_authorized_get_request("https://statsector-hwezb647ha-ew.a.run.app/get-statsector/?lat=50.870&lon=4.705", "https://statsector-hwezb647ha-ew.a.run.app")
    print(str(result))