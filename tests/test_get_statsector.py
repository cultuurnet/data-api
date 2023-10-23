import unittest
from fastapi.testclient import TestClient
from main import app

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
        self.assertEqual(response.status_code, 400)  # Assuming you return 400 for missing parameters
        self.assertIn("error", data)

    def test_get_statsector_invalid_coordinates(self):
        response = client.get("/get-statsector/?lat=invalid&lon=invalid")
        data = response.json()
        self.assertEqual(response.status_code, 400)  # Assuming you return 400 for invalid coordinates
        self.assertIn("error", data)

    def test_get_statsector_invalid_address(self):
        response = client.get("/get-statsector/?address=123")
        data = response.json()
        self.assertEqual(response.status_code, 400)  # Assuming you return 400 for invalid address
        self.assertIn("error", data)

if __name__ == "__main__":
    unittest.main()
