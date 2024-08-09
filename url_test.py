import requests

def test_url (url):
    response = requests.get(url)
    print("\n"+url)
    if response.status_code == 200:
       
        print(response.json())
    else:
        print(response.status_code)
test_url('https://fapi.binance.com/fapi/v1/time')
test_url('https://api-gcp.binance.com/api/v3/time')
test_url('https://api.binance.com/api/v3/time')
test_url('https://api1.binance.com/api/v3/time')
test_url('https://api2.binance.com/api/v3/time')
test_url('https://api3.binance.com/api/v3/time')
test_url('https://api4.binance.com/api/v3/time')
