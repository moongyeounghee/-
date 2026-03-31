import requests
import pandas as pd
from datetime import datetime

API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
BASE_URL = "http://apis.data.go.kr/B551177/AirportRailroadOperationInfo/getAirportRailroad"

STN_MAP = {
    "001": "서울역",
    "002": "공덕",
    "003": "홍대입구",
    "004": "디지털미디어시티",
    "005": "마곡나루",
    "006": "김포공항",
    "007": "계양",
    "008": "검암",
    "009": "청라국제도시",
    "010": "영종",
    "011": "운서",
    "012": "공항화물청사",
    "049": "인천공항1터미널",
    "060": "인천공항2터미널"
}

TRN_CLS_MAP = {
    "Comm": "일반열차",
    "Expr": "직통열차",
    "Dirc": "직통열차(Direct)"
}

def format_arex_time(time_str):
    if not time_str or len(time_str) < 12:
        return ""
    # Usually "YYYYMMDDHHMMSS" or "YYYYMMDDHHMM"
    # To HH:MM
    return f"{time_str[8:10]}:{time_str[10:12]}"

def get_railroad_info(station_filter=None):
    """
    공항철도 실시간 운행정보를 조회합니다.
    station_filter (str): 특정 역의 결과만 필터링 (예: "049", "060")
    """
    params = {
        "serviceKey": API_KEY,
        "type": "json",
        "pageNo": "1",
        "numOfRows": "200" # 충분히 많은 열차수 가져오기
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            return pd.DataFrame()
            
        parsed = []
        now_hm = datetime.now().strftime("%H:%M")
        
        for item in items:
            stn_cd = item.get("stnCd", "")
            if station_filter and stn_cd != station_filter:
                continue
                
            trn_no = item.get("trnNo", "")
            trn_cls = item.get("trnClsfNm", "")
            plan_arrv = item.get("planArrvDttm", "")
            accom_arrv = item.get("accomArrvDttm", "")
            
            stn_name = STN_MAP.get(stn_cd, stn_cd)
            trn_name = TRN_CLS_MAP.get(trn_cls, trn_cls)
            
            # Format times
            f_plan = format_arex_time(plan_arrv)
            f_accom = format_arex_time(accom_arrv)
            
            # Determine logic
            display_time = f_plan
            delay_remark = ""
            
            if accom_arrv and plan_arrv:
                try:
                    plan_dt = datetime.strptime(plan_arrv, "%Y%m%d%H%M%S")
                    accom_dt = datetime.strptime(accom_arrv, "%Y%m%d%H%M%S")
                    if (accom_dt - plan_dt).total_seconds() > 180: # 3분 이상 늦음
                        delay_remark = "연착"
                        display_time = f_accom
                except:
                    if accom_arrv > plan_arrv: # Fallback to string
                        delay_remark = "연착"
                        display_time = f_accom
            
            # If no planned arrival but there's a departure (starting station)
            if not display_time:
                plan_dptr = item.get("planDptrDttm", "")
                display_time = format_arex_time(plan_dptr)
                
            # Filter out trains that already passed (optional, keep simple for now)
            
            if display_time:
                parsed.append({
                    "역명": stn_name,
                    "열차번호": trn_no,
                    "등급": trn_name,
                    "예정/도착시간": display_time,
                    "상태": delay_remark if delay_remark else "정상운행",
                    "_sort_time": display_time # For sorting
                })
                
        if not parsed:
            return pd.DataFrame()
            
        df = pd.DataFrame(parsed)
        # Sort by time
        df = df.sort_values(by="_sort_time", na_position="last").drop(columns=["_sort_time"])
        return df
        
    except Exception as e:
        print(f"공항철도 API 호출 실패: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = get_railroad_info(station_filter="060") # T2 test
    print(df.to_string())
