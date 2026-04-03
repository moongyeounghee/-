import sys
import io
import requests
import pandas as pd
from datetime import datetime

# 공공데이터포털 API 인증키 및 엔드포인트 URL
API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
URL = "https://apis.data.go.kr/B551177/statusOfAllFltDeOdp/getFltArrivalsDeOdp"

def format_time(time_str):
    """ '202603240005' 형식을 '00:05' 형식으로 변환 """
    if not time_str or len(time_str) < 12:
        return "N/A"
    return f"{time_str[8:10]}:{time_str[10:12]}"

def get_arrival_flights():
    """
    공공데이터포털의 입국(도착) 여객기 운항정보 API를 호출하여 DataFrame 형태로 반환합니다.
    (최신 날짜 기준)
    """
    today_str = datetime.now().strftime("%Y%m%d")
    
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "1000",
        "searchDate": today_str,
        "searchFrom": "0000",
        "searchTo": "2400",
        "passengerOrCargo": "p",  # 여객기만
        "type": "json"            # JSON 응답 포맷
    }
    
    try:
        response = requests.get(URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 에러 체크
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            print(f"API 에러: {header.get('resultMsg', 'Unknown')}")
            return None
            
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            print("조회된 입국/도착 운항 정보가 없습니다.")
            return None
            
        parsed_data = []
        for v in items:
            flight_id = v.get("flightId", "")
            airline = v.get("airline", "")
            airport = v.get("airport", "")
            
            sch_time = format_time(v.get("scheduleDatetime"))
            est_time = format_time(v.get("estimatedDatetime"))
            
            carousel = v.get("carousel", "미정")
            exit_no = v.get("exitNumber", "미정")
            terminal = v.get("terminalId", "N/A")
            remark = v.get("remark", "")
            master_id = str(v.get("masterFlightId", "")).strip()
            actual_flight = master_id if master_id else flight_id
            
            parsed_data.append({
                "편명": flight_id,
                "실제운항편명": actual_flight,
                "항공사": airline,
                "출발지": airport,
                "예정시간": sch_time,
                "변경/도착시간": est_time,
                "수하물수취대": carousel,
                "출구": exit_no,
                "터미널": terminal,
                "상태": remark
            })
            
        return pd.DataFrame(parsed_data)
        
    except requests.exceptions.RequestException as e:
        print(f"API 통신 실패 (네트워크 에러): {e}")
        return None
    except ValueError:
        print("JSON 데이터를 파싱하는데 실패했습니다.")
        return None

if __name__ == "__main__":
    # 윈도우 터미널 인코딩(이모지 등) 에러 방지
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

    print("🛬 실시간 인천공항 입국(도착) 여객기 정보 조회 중...\n")
    df_arrivals = get_arrival_flights()
    
    if df_arrivals is not None and not df_arrivals.empty:
        # 1. 현재 시간 가져오기 (비교를 위해 HH:MM 포맷)
        current_time_hm = datetime.now().strftime("%H:%M")
        print(f"⏰ [현재 시간 기준]: {current_time_hm} 이후 도착 스케줄\n")
        
        # 2. 현재 시간 이후의 항공편만 필터링 (문자열 비교 활용)
        # N/A 값 방지 위해 결측치 제외
        df_valid = df_arrivals[df_arrivals["예정시간"] != "N/A"]
        df_filtered = df_valid[df_valid["예정시간"] >= current_time_hm].copy()
        
        if df_filtered.empty:
            print("⚠️ 현재 시간 이후의 데이터가 없어, 조회된 데이터 중 가장 마지막(가장 늦은 시간) 10개 스케줄을 보여드립니다.\n")
            # 전체 데이터를 시간순 정렬하여 마지막 10개 추출
            df_sorted = df_valid.sort_values(by="예정시간", ascending=True).reset_index(drop=True)
            print(df_sorted.tail(10).to_string())
            
            print("\n💡 [입국 현황 요약 (전체 100건)]")
            total = len(df_sorted)
            delayed = df_sorted[df_sorted['상태'].str.contains('지연', na=False)]
            arrived = df_sorted[df_sorted['상태'].str.contains('도착', na=False)]
            print(f"👉 총 조회된 여객기 수: {total} 편")
            print(f"👉 '도착 완료'된 여객기: {len(arrived)} 편")
            print(f"👉 '지연' 상태인 여객기: {len(delayed)} 편")
        else:
            # 3. 시간순 정렬 (현재 시간과 가장 가까운 비행기가 위로 오도록)
            df_sorted = df_filtered.sort_values(by="예정시간", ascending=True).reset_index(drop=True)
            
            # 상위 20개만 출력
            print(df_sorted.head(20).to_string())
            
            print("\n💡 [입국 현황 요약 (현재시간 이후)]")
            total = len(df_sorted)
            delayed = df_sorted[df_sorted['상태'].str.contains('지연', na=False)]
            arrived = df_sorted[df_sorted['상태'].str.contains('도착', na=False)]
            print(f"👉 남은 조회된 여객기 수: {total} 편")
            print(f"👉 벌써 '도착 완료' 처리된 여객기 (조기 도착 등): {len(arrived)} 편")
            print(f"👉 '지연' 상태인 여객기: {len(delayed)} 편")
    else:
        print("입국 정보를 불러오지 못했습니다.")
