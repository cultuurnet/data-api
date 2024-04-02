import timeit
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

call1 = '/get-statsector/?address=Parkstraat%20215%20Leuven'
call2 = '/get-statsector/?lat=50.870&lon=4.705'

def test_code():
    response = client.get(call1)
    data = response.json()

# Time the code execution 10 times
execution_time = timeit.timeit(test_code, number=10)

print(f"Execution time: {execution_time} seconds")