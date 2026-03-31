import requests
import pandas as pd
from datetime import datetime

API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
BASE_URL = "http://apis.data.go.kr/B551177/ShtbusInfo/getShtbArrivalPredInfo"

STOP_MAP = {
    "10000020": "제1여객터미널(T1)",
    "10000021": "제2여객터미널(T2)",
    "10000022": "장기주차장(P1/P2)",
    "10000023": "화물터미널역",
    "10000024": "국제업무단지",
    "10000025": "정비고"
}

ROUTE_MAP = {
    "11100001": "T1-T2 순환",
    "11100002": "장기주차장 순환",
    "11100003": "화물터미널 노선",
    "11100004": "물류단지 노선"
}

def get_shuttle_arrivals():
    """
    셔틀버스 실시간 도착 예측 정보를 가져옵니다.
    """
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "pageNo": "1",
        "numOfRows": "100"
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            return pd.DataFrame()
            
        parsed = []
        for item in items:
            stop_id = item.get("stopId", "")
            route_id = item.get("routeId", "")
            pred_time = item.get("predTimes", "0") # Predicted time in seconds? minutes? Usually minutes for Korean APIs, but let's check.
            
            # format time
            ofr_time = item.get("ofrTime", "")
            formatted_time = ""
            if len(ofr_time) >= 14:
                formatted_time = f"{ofr_time[8:10]}:{ofr_time[10:12]}"
            
            stop_name = STOP_MAP.get(stop_id, stop_id)
            route_name = ROUTE_MAP.get(route_id, route_id)
            
            parsed.append({
                "정류장": stop_name,
                "노선": route_name,
                "도착예정": f"약 {pred_time}분 후" if pred_time and pred_time != "0" else "잠시 후 도착",
                "기준시간": formatted_time
            })
            
        df = pd.DataFrame(parsed)
        # 같은 정류장/노선 별로 가장 빠른 도착 한대씩만 보여줄 수도 있지만, 우선 전체 반환
        return df
        
    except Exception as e:
        print(f"셔틀버스 API 호츌 실패: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = get_shuttle_arrivals()
    print("🚌 실시간 셔틀버스 예측 정보 🚌")
    print(df.to_string())
