import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestGetStatsectorEndpoint(unittest.TestCase):
    def test_get_statsector_with_coordinates(self):
        response = client.get("/get-statsector/?lat=50.870&lon=4.705")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("sector_id", data)
        self.assertIn("sector_name", data)

    def test_get_statsector_with_address(self):
        response = client.get("/get-statsector/?address=Parkstraat 215 Leuven")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("sector_id", data)
        self.assertIn("sector_name", data)

    def test_get_statsector_missing_parameters(self):
        response = client.get("/get-statsector/")
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", data)
        self.assertIn("Either 'lat' and 'lon' or 'address' must be provided.", data['detail'])

    def test_get_statsector_invalid_coordinates(self):
        response = client.get("/get-statsector/?lat=invalid&lon=invalid")
        data = response.json()
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", data)

    def test_get_statsector_invalid_address(self):
        response = client.get("/get-statsector/?address=123")
        data = response.json()
        self.assertEqual(response.status_code, 500) 
        self.assertIn("detail", data)
        self.assertIn("An internal error occurred", data['detail'])
        # check that there is a uuid in detail
        uuid_regex = r"error id: [a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}"
        self.assertRegex(data['detail'], uuid_regex)

if __name__ == "__main__":
    unittest.main()
