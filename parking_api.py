import requests
import pandas as pd
from datetime import datetime

API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
URL = "https://apis.data.go.kr/B551177/StatusOfParking/getTrackingParking"

def get_parking_status():
    """
    공공데이터포털의 주차장 혼잡도 API를 호출하여 DataFrame 형태로 반환합니다.
    (잔여대수 = 총 주차면수(parkingarea) - 주차된 차량수(parking))
    """
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "50",
        "type": "json"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            print(f"Parking API Error: {header.get('resultMsg', 'Unknown')}")
            return None
            
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            return None
            
        parsed_data = []
        for v in items:
            floor = v.get("floor", "").strip()
            # 예: "T1 단기1층", "T2 장기주차장"
            try:
                parked = int(v.get("parking", 0))
                capacity = int(v.get("parkingarea", 0))
            except ValueError:
                parked = 0
                capacity = 0
                
            available = max(0, capacity - parked)
            
            terminal = "T2" if "T2" in floor else "T1"
            
            # 단기 / 장기 구분
            if "단기" in floor:
                ptype = "단기주차장"
            elif "장기" in floor:
                ptype = "장기주차장"
            else:
                ptype = "기타주차장"
                
            parsed_data.append({
                "터미널": terminal,
                "주차장유형": ptype,
                "구역/층": floor,
                "주차대수": parked,
                "총면수": capacity,
                "잔여대수": available
            })
            
        return pd.DataFrame(parsed_data)
        
    except requests.exceptions.RequestException as e:
        print(f"Parking API Network Error: {e}")
        return None
    except Exception as e:
        print(f"Parking API Parsing Error: {e}")
        return None

def get_recommended_parking(terminal="T1"):
    """
    특정 터미널(T1/T2)의 단기주차장 중 가장 잔여 대수가 많은 구역 1개를 추천합니다.
    (맞이객은 보통 단기주차장을 이용)
    """
    df = get_parking_status()
    if df is None or df.empty:
        return None
        
    df_term = df[(df["터미널"] == terminal) & (df["주차장유형"] == "단기주차장")]
    if df_term.empty:
        # 단기가 없으면 장기라도
        df_term = df[df["터미널"] == terminal]
        
    if df_term.empty:
        return None
        
    # 잔여대수 기준 내림차순 정렬하여 가장 널널한 1곳 반환
    best = df_term.sort_values(by="잔여대수", ascending=False).iloc[0]
    return best.to_dict()

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
    print("T1 추천:", get_recommended_parking("T1"))
    print("T2 추천:", get_recommended_parking("T2"))
