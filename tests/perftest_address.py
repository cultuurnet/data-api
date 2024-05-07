
import timeit
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:

    call1 = '/get-statsector/?address=Parkstraat%20215%20Leuven'

    def test_code_address():
        response = client.get(call1)
        # data = response.json()
        # print(data)


    t = timeit.Timer(test_code_address)
    # !!! DO NOT INCREASE AS THIS WILL CALL THE UNDERLYING API !!!
    repeat, number = 10, 1
    r = t.repeat(repeat, number) 
    best, worse = min(r), max(r)
    print(r)
    print("{number} loops, best of {repeat}: {best:.3g} seconds per loop, "
        "worse of {repeat}: {worse:.3g} seconds per loop".format(**vars()))