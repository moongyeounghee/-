import requests
import xml.etree.ElementTree as ET
import pandas as pd

# 공공데이터포털 API 인증키 및 엔드포인트 URL
API_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
URL = "https://apis.data.go.kr/B551177/statusOfDepartureCongestion/getDepartureCongestion"

def get_departure_congestion():
    """
    공공데이터포털의 출국장 혼잡도 API를 호출하여 현재 게이트별 대기 시간과 대기 인원을 DataFrame 형태로 반환합니다.
    """
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "100"
    }
    
    try:
        # HTTP GET 요청
        response = requests.get(URL, params=params, timeout=10)
        response.raise_for_status()
        
        # XML 파싱
        root = ET.fromstring(response.content)
        
        # 응답 코드 체크 (00 이 정상)
        result_code = root.find('.//resultCode')
        if result_code is not None and result_code.text != '00':
            msg = root.find('.//resultMsg')
            print(f"API 응답 에러: {msg.text if msg is not None else 'Unknown'}")
            return None
            
        items = root.findall('.//item')
        parsed_data = []
        for item in items:
            # 안전하게 태그 값 추출
            gate_id = item.find('gateId').text if item.find('gateId') is not None else ""
            wait_time = item.find('waitTime').text if item.find('waitTime') is not None else "0"
            wait_len = item.find('waitLength').text if item.find('waitLength') is not None else "0"
            op_time = item.find('operatingTime').text if item.find('operatingTime') is not None else "N/A"
            
            parsed_data.append({
                "게이트(Gate)": gate_id,
                "대기 시간(분)": int(wait_time),
                "대기 인원(명)": int(wait_len),
                "운영 시간": op_time or "상시"
            })
            
        return pd.DataFrame(parsed_data)
        
    except requests.exceptions.RequestException as e:
        print(f"API 통신 실패 (네트워크 에러): {e}")
        return None
    except ET.ParseError:
        print("XML 데이터를 해석하는데 실패했습니다.")
        return None

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

    print("🚀 실시간 인천공항 출국장 혼잡도 조회 중...\n")
    df_congestion = get_departure_congestion()
    
    if df_congestion is not None and not df_congestion.empty:
        # 대기 시간이 가장 긴(혼잡한) 게이트 순으로 정렬하여 출력
        df_sorted = df_congestion.sort_values(by="대기 시간(분)", ascending=False).reset_index(drop=True)
        print(df_sorted.to_string())
        
        print("\n💡 [분석 요약]")
        most_congested = df_sorted.iloc[0]
        most_free = df_sorted.iloc[-1]
        print(f"👉 가장 붐비는 곳: {most_congested['게이트(Gate)']} ({most_congested['대기 인원(명)']}명, {most_congested['대기 시간(분)']}분 대기)")
        print(f"👉 가장 널널한 곳: {most_free['게이트(Gate)']} ({most_free['대기 인원(명)']}명, {most_free['대기 시간(분)']}분 대기)")
    else:
        print("출국장 혼잡도 데이터를 불러오지 못했습니다.")
