import requests
import pandas as pd

API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
BASE_URL = "http://apis.data.go.kr/B551177/BusInformation/getBusInfo"

def format_bus_time(t_str):
    if not t_str or len(t_str) != 4:
        return "정보없음"
    return f"{t_str[:2]}:{t_str[2:]}"

def get_bus_by_keyword(keyword, terminal="1"):
    """
    키워드(예: 강남, 수원, 홍대)를 포함하는 공항버스의 노선 정보(첫차/막차/요금 등)를 반환.
    terminal: "1" (T1) or "2" (T2)
    """
    if not keyword:
        return []
        
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "pageNo": "1",
        "numOfRows": "300" # 전체 공항버스 리스트를 한 번에 가져옴
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            return []
            
        matched_buses = []
        for item in items:
            route_info = item.get("routeinfo", "")
            if not route_info: 
                continue
                
            # 노선 정보(정류장 리스트)에 검색 키워드가 포함되어 있는지 확인
            if keyword in route_info:
                b_num = item.get("busnumber", "")
                fare = item.get("adultfare", "")
                fare_str = f"{int(fare):,}원" if fare and fare.isdigit() else fare
                
                if terminal == "1":
                    first = item.get("t1endfirst", "")
                    last = item.get("t1endlast", "")
                else:
                    first = item.get("t2endfirst", "")
                    last = item.get("t2endlast", "")
                    # T2 막차가 없는 경우 T1 시간으로 Fallback
                    if not first: first = item.get("t1endfirst", "")
                    if not last: last = item.get("t1endlast", "")
                    
                first_str = format_bus_time(first)
                last_str = format_bus_time(last)
                
                matched_buses.append({
                    "icon": "🚌",
                    "name": f"공항버스 {b_num}번",
                    "time": f"첫차 {first_str} / 막차 {last_str}",
                    "cost": fare_str if fare_str else "현장 문의",
                    "tip": f"정차역: {keyword} 방면"
                })
                
                # 최대 3개까지만 추천 (너무 많아지는 것 방지)
                if len(matched_buses) >= 3:
                    break
                    
        return matched_buses
        
    except Exception as e:
        print(f"공항버스 API 호출 실패: {e}")
        return []

if __name__ == "__main__":
    buses = get_bus_by_keyword("수원")
    for b in buses:
        print(b)
