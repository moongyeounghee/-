import requests
import time
import pandas as pd
import streamlit as st

OPENSKY_USERNAME = "moongyeounghee@gmail.com-api-client"
OPENSKY_PASSWORD = "KAJR6qynO7oJTuC9KiZD9NdbMiF3kksE"

# 대륙 반경 확장 (아시아 전역 - 러시아에서 인도네시아까지)
# lamin, lomin, lamax, lomax
BBOX = {
    "lamin": -10.0,
    "lamax": 60.0,
    "lomin": 90.0,
    "lomax": 150.0
}

@st.cache_data(ttl=120, show_spinner=False)
def _fetch_opensky_data():
    url = "https://opensky-network.org/api/states/all"
    try:
        resp = requests.get(url, auth=(OPENSKY_USERNAME, OPENSKY_PASSWORD), timeout=20)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"OpenSky API Error: {resp.status_code}")
            return None
    except Exception as e:
        print(f"OpenSky API Exception: {e}")
        return None

def get_opensky_states(target_callsign=None):
    states = _fetch_opensky_data()
            
    if not states or "states" not in states or not states["states"]:
        return None
        
    # OpenSky returns list of lists for states:
    # 0: icao24, 1: callsign, 2: origin_country, 3: time_position, 4: last_contact,
    # 5: longitude, 6: latitude, 7: baro_altitude, 8: on_ground, 9: velocity,
    # 10: true_track, 11: vertical_rate, 12: sensors, 13: geo_altitude, 14: squawk,
    # 15: spi, 16: position_source
    
    results = []
    for s in states["states"]:
        callsign = str(s[1]).strip() if s[1] else ""
        lon = s[5]
        lat = s[6]
        alt = s[7] # meters
        vel = s[9] # m/s
        on_ground = s[8]
        heading = s[10]
        
        # If target is specified, return only that one
        if target_callsign and target_callsign.upper() == callsign:
            return {
                "callsign": callsign,
                "lon": lon,
                "lat": lat,
                "alt": alt,
                "vel": vel,
                "on_ground": on_ground,
                "heading": heading
            }
            
        if lon and lat:
            results.append({
                "callsign": callsign,
                "lon": lon,
                "lat": lat,
                "alt": alt,
                "vel": vel,
                "on_ground": on_ground,
                "heading": heading
            })
            
    if target_callsign:
        return None # Not found
        
    return pd.DataFrame(results)

IATA_TO_ICAO = {
    # 한국 항공사
    "KE": "KAL", "OZ": "AAR", "7C": "JJA", "TW": "TWB",
    "LJ": "JNA", "BX": "ABL", "RS": "ASV", "ZE": "ESR",
    # 미국
    "DL": "DAL", "AA": "AAL", "UA": "UAL", "AC": "ACA",
    # 아시아
    "CX": "CPA", "SQ": "SIA", "TG": "THA", "VN": "HVN",
    "PR": "PAL", "5J": "CEB", "VJ": "VJC", "AK": "AXM",
    "MH": "MAS", "GA": "GIA", "CI": "CAL", "BR": "EVA",
    "NH": "ANA", "JL": "JAL", "MM": "APJ", "GK": "JJP",
    # 중국
    "CA": "CCA", "MU": "CES", "CZ": "CSN", "HU": "CHH",
    "3U": "CSC", "ZH": "CSZ", "9C": "CQH", "HO": "DKH",
    "SC": "CDG", "FM": "CSH", "ZH": "SZX", "HX": "CRK",
    # 유럽
    "LH": "DLH", "AF": "AFR", "KL": "KLM", "BA": "BAW",
    "EK": "UAE", "QR": "QTR", "EY": "ETD", "TK": "THY",
    # 아프리카/기타
    "ET": "ETH",  # 에티오피아항공
    "QF": "QFA",  # 콴타스
    "VS": "VIR",  # 버진애틀랜틱
    "AM": "AMX",  # 아에로멕시코
    "TN": "THD",  # 에어타히티누이
}

def iata_to_icao_callsign(iata_flight_num):
    import re
    if not iata_flight_num: return ""
    iata_flight_num = str(iata_flight_num).strip().upper()
    # ET673Y → airline=ET, num=673 (끝의 알파벳 좌석클래스 코드 제거)
    match = re.match(r"^([A-Z0-9]{2})(\d+)[A-Z]?$", iata_flight_num)
    if match:
        airline, num = match.groups()
        icao = IATA_TO_ICAO.get(airline, airline)
        return f"{icao}{num}"
    return iata_flight_num

def get_target_flight_status(iata_flight_num):
    """
    IATA 편명(예: KE712)를 받아 OpenSky에서 실시간 위치(고도, 좌표 등)를 반환.
    발견되지 않으면 None 반환.
    """
    if not iata_flight_num: return None
    target_callsign = iata_to_icao_callsign(iata_flight_num)
    return get_opensky_states(target_callsign=target_callsign)

if __name__ == "__main__":
    df = get_opensky_states()
    if df is not None:
        print(f"Found {len(df)} aircrafts near Incheon.")
        print(df.head())
        
    print("Testing KE712:", get_target_flight_status("KE712"))
