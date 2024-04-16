
import timeit
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

call2 = '/get-statsector/?lat=50.870&lon=4.705'

def test_code_geo():
    response = client.get(call2)
    # data = response.json()
    # print(data)


t = timeit.Timer(test_code_geo)
repeat, number = 10, 1
r = t.repeat(repeat, number) 
best, worse = min(r), max(r)
print(r)
print("{number} loops, best of {repeat}: {best:.3g} seconds per loop, "
     "worse of {repeat}: {worse:.3g} seconds per loop".format(**vars()))