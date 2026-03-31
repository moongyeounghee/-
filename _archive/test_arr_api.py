import requests

API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"

def test_api(url):
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "pageNo": "1",
        "numOfRows": "100"
    }
    print(f"Testing {url}")
    try:
        response = requests.get(url, params=params, timeout=10)
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            try:
                print("Response:", response.json())
            except:
                print("Raw text:", response.text[:500])
        else:
            print("Raw text:", response.text[:500])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_api("http://apis.data.go.kr/B551177/StatusOfArrivalsAPI/getArrivalsList")
    test_api("http://apis.data.go.kr/B551177/StatusOfArrivals/getArrivalsCongestion")
