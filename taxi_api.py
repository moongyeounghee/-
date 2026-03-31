import requests
import pandas as pd
from datetime import datetime

API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
BASE_URL = "http://apis.data.go.kr/B551177/StatusOfTaxi/getTaxiStatus"

def get_taxi_status(terminal="P01"):
    """
    택시 승강장 실시간 대기 현황을 가져옵니다.
    terminal: P01 (T1?), P02 (T2?) 등
    """
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "pageNo": "1",
        "numOfRows": "10"
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            return pd.DataFrame()
            
        parsed = []
        for item in items:
            t = item.get("terno", "")
            if terminal and t != terminal:
                continue
                
            parsed.append({
                "택시 종류": "서울 택시",
                "대기 대수": int(item.get("seoultaxicnt", 0)),
                "탑승장": item.get("seoultaxistand", "")
            })
            parsed.append({
                "택시 종류": "인천 택시",
                "대기 대수": int(item.get("incheontaxicnt", 0)),
                "탑승장": item.get("incheontaxistand", "")
            })
            parsed.append({
                "택시 종류": "경기 택시",
                "대기 대수": int(item.get("gyenggitaxicnt", 0)),
                "탑승장": item.get("gyenggitaxistand", "")
            })
            parsed.append({
                "택시 종류": "모범/대형 택시",
                "대기 대수": int(item.get("besttaxicnt", 0)),
                "탑승장": item.get("bestVantaxistand", "")
            })
            
        return pd.DataFrame(parsed)
        
    except Exception as e:
        print(f"택시 API 호출 실패: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = get_taxi_status()
    print(df.to_string())
