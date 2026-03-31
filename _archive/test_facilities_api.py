import requests
import json

def test_api():
    key = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
    url = "http://apis.data.go.kr/B551177/FacilitiesInformation/getFacilitesInfo"
    params = {"serviceKey": key, "type": "json", "numOfRows": 5, "pageNo": 1}
    
    res = requests.get(url, params=params, timeout=10)
    if res.status_code == 200:
        data = res.json()
        with open("facilities.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Data saved to facilities.json successfully!")
    else:
        print("Status", res.status_code, "Error:", res.text[:200])

if __name__ == "__main__":
    test_api()
