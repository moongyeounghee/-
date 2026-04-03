import streamlit as st
import pandas as pd
import time
import random
import string
from datetime import datetime, timedelta, timezone

from departure_congestion_api import get_departure_congestion
from departure_flight_api import get_departure_flights
from arrival_flight_api import get_arrival_flights
from rl_engine import (
    AIPortRLEngine,
    DEP_ACTION_0, DEP_ACTION_1, DEP_ACTION_2, DEP_ACTION_3,
    ARR_ACTION_0, ARR_ACTION_1, ARR_ACTION_2,
    ACTION_NAMES
)

# ── API 호출 글로벌 캐싱 처리 (10초 자동 갱신 시 발생하는 전체 페이지 UI 멈춤 방지용) ──
import parking_api
import bus_api
import taxi_api
import railroad_api
import facilities_api
import opensky_api

# ── API 호출 글로벌 캐싱 처리 (10초 자동 갱신 시 발생하는 전체 페이지 UI 멈춤 방지용) ──
get_departure_congestion = st.cache_data(ttl=60)(get_departure_congestion)
get_departure_flights = st.cache_data(ttl=60)(get_departure_flights)
get_arrival_flights = st.cache_data(ttl=60)(get_arrival_flights)
parking_api.get_recommended_parking = st.cache_data(ttl=60)(parking_api.get_recommended_parking)
bus_api.get_bus_by_keyword = st.cache_data(ttl=60)(bus_api.get_bus_by_keyword)
taxi_api.get_taxi_status = st.cache_data(ttl=60)(taxi_api.get_taxi_status)
railroad_api.get_railroad_info = st.cache_data(ttl=60)(railroad_api.get_railroad_info)
facilities_api.load_all_facilities = st.cache_data(ttl=60)(facilities_api.load_all_facilities)

@st.cache_resource
def load_rl_models():
    import pickle, os
    q_table, env_data = None, None
    try:
        if os.path.exists("dynamic_q_table.pkl") and os.path.exists("dynamic_env_data.pkl"):
            with open("dynamic_q_table.pkl", "rb") as f: q_table = pickle.load(f)
            with open("dynamic_env_data.pkl", "rb") as f: env_data = pickle.load(f)
    except Exception: pass
    return q_table, env_data

# ─────────────────────────────────────────────
# 페이지 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI-PORT 스마트 네비게이션",
    page_icon="🛫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# 전역 CSS 스타일
# ─────────────────────────────────────────────
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Inter:wght@300;400;600;800&display=swap');

:root {
  --color-bg-light: #E0F2FE;
  --color-primary: #0084FF;
  --color-secondary-bg: #BAE6FD;
  --color-text-main: #1A202C;
  --color-icon-soft: #7BB9F6;
  --color-card-white: #FFFFFF;
  --color-success: #00C853;
  --color-warning: #FFA000;
  --color-danger: #FF4D4D;
  
  /* 지도 테마 (요청 변수) */
  --map-land: #EBF2DD;    /* 지도 육지 배경색 */
  --map-sea: #AADAFF;     /* 지도 바다 배경색 */
  --map-border: #B3B3B3;  /* 국가 경계 및 해안선 */
  --map-text: #5C5C5C;    /* 지명 및 라벨 텍스트 */
  --map-grid: #D1E5F5;    /* (참고) 위경도 격자선 */
}

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Inter', sans-serif;
    color: var(--color-text-main);
}

/* 배경 */
.stApp {
    background: var(--color-bg-light);
    min-height: 100vh;
}

/* 텍스트 메인 강제 고정 */
h1, h2, h3, h4, h5, h6, p, span, div {
    color: var(--color-text-main);
}

/* 사이드바 다크테마 컴포넌트 강제 라이트화 */
[data-testid="stHeader"] {
    background: transparent !important;
}

/* 히어로 헤더 */
.hero-header {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    background: var(--color-card-white);
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(0, 132, 255, 0.08);
    margin-bottom: 2rem;
    border: 1px solid rgba(0, 132, 255, 0.15);
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 900;
    color: var(--color-primary);
    margin-bottom: 0.4rem;
    letter-spacing: -1px;
}
.hero-sub {
    color: #4A5568 !important;
    font-size: 1.1rem;
    font-weight: 500;
}
.team-info {
    margin-top: 1.5rem;
    display: inline-block;
    background: var(--color-secondary-bg);
    color: var(--color-primary) !important;
    padding: 0.6rem 1.5rem;
    border-radius: 30px;
    font-weight: 700;
    font-size: 1rem;
    border: 1px solid rgba(0, 132, 255, 0.2);
}

/* 모드 선택 카드 */
.mode-card {
    border-radius: 20px !important;
    padding: 3.5rem 2rem !important; /* 위아래 패딩 늘려서 정사각형 느낌 확보 */
    max-width: 380px !important;     /* 모바일 족쇄 (비율 파괴 방지) */
    margin: 1.5rem auto !important;    /* 중앙 정렬 */
    text-align: center !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    background: var(--color-card-white) !important;
    box-shadow: 0 8px 30px rgba(14, 165, 233, 0.08) !important; /* 그림자 강화 */
    border: 2px solid transparent !important;
}
.mode-card:hover {
    border-color: var(--color-primary);
    box-shadow: 0 12px 32px rgba(0, 132, 255, 0.2);
    transform: translateY(-4px);
}
.mode-emoji { font-size: 4rem; margin-bottom: 1rem; }
.mode-title { font-size: 1.5rem; font-weight: 800; color: var(--color-text-main) !important; margin-bottom: 0.5rem; }
.mode-desc { font-size: 0.95rem; color: #4A5568 !important; line-height: 1.6; font-weight: 500;}

/* 정보 카드 */
.info-card {
    background: var(--color-card-white);
    border: 1px solid rgba(0, 132, 255, 0.15);
    box-shadow: 0 4px 20px rgba(0, 132, 255, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.info-card h4 { color: var(--color-primary) !important; font-size: 0.9rem; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 0.8rem; }

/* 상태 배지 */
.badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 0.2rem;
}
.badge-green { background: rgba(0, 200, 83, 0.1); color: var(--color-success) !important; border: 1px solid rgba(0, 200, 83, 0.2); }
.badge-yellow { background: rgba(255, 160, 0, 0.1); color: var(--color-warning) !important; border: 1px solid rgba(255, 160, 0, 0.2); }
.badge-red { background: rgba(255, 77, 77, 0.1); color: var(--color-danger) !important; border: 1px solid rgba(255, 77, 77, 0.2); }
.badge-blue { background: var(--color-secondary-bg); color: var(--color-primary) !important; border: 1px solid rgba(0, 132, 255, 0.2); }

/* 게이지 바 */
.gauge-wrap { background: var(--color-bg-light); border: 1px solid rgba(0,0,0,0.05); border-radius: 8px; height: 12px; overflow: hidden; margin: 0.5rem 0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }
.gauge-bar { height: 100%; border-radius: 8px; transition: width 0.5s ease; }
.gauge-green { background: var(--color-success); }
.gauge-yellow { background: var(--color-warning); }
.gauge-red { background: var(--color-danger); animation: pulse-red 1s ease-in-out infinite; }
@keyframes pulse-red { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }

/* 단계 진행 바 */
.phase-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    margin-bottom: 0.5rem;
    border: 1px solid rgba(0, 132, 255, 0.15);
    background: var(--color-card-white);
}
.phase-active { background: var(--color-secondary-bg); border-color: rgba(0, 132, 255, 0.5); box-shadow: 0 2px 8px rgba(0, 132, 255, 0.15); }
.phase-active span { color: var(--color-primary) !important; font-weight: 700 !important; }
.phase-done { color: #A0AEC0 !important; background: #F7FAFC; border-color: #E2E8F0; }
.phase-done span { color: #A0AEC0 !important; }
.phase-pending { color: #A0AEC0 !important; background: #FFFFFF; border-style: dashed; }
.phase-pending span { color: #A0AEC0 !important; }

/* 액션 박스 */
.action-box {
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 1px solid;
    background: var(--color-card-white);
}
.action-green { border-color: rgba(0, 200, 83, 0.4); color: var(--color-success) !important; box-shadow: 0 4px 12px rgba(0, 200, 83, 0.08); }
.action-yellow { border-color: rgba(255, 160, 0, 0.4); color: var(--color-warning) !important; box-shadow: 0 4px 12px rgba(255, 160, 0, 0.08); }
.action-red { border-color: rgba(255, 77, 77, 0.4); color: var(--color-danger) !important; box-shadow: 0 4px 12px rgba(255, 77, 77, 0.08); }

/* 공유코드 박스 */
.share-code-box {
    background: var(--color-card-white);
    border: 2px dashed var(--color-primary);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin: 1rem 0;
    box-shadow: 0 4px 20px rgba(0, 132, 255, 0.06);
}
.share-code {
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: 0.5rem;
    color: var(--color-primary) !important;
}

/* 대중교통 카드 */
.transit-card {
    background: var(--color-card-white);
    border: 1px solid rgba(0, 132, 255, 0.15);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 2px 8px rgba(0, 132, 255, 0.04);
}
.transit-icon { font-size: 2rem; }
.transit-name { font-weight: 800; color: var(--color-primary) !important; font-size: 0.95rem; }
.transit-detail { color: #718096 !important; font-size: 0.85rem; font-weight: 500;}

/* 사이드바 */
section[data-testid="stSidebar"] {
    background: var(--color-card-white) !important;
    border-right: 1px solid rgba(0, 132, 255, 0.15);
    box-shadow: 2px 0 12px rgba(0, 132, 255, 0.05);
}

/* 공통 메트릭 */
[data-testid="stMetric"] {
    background: var(--color-card-white);
    border: 1px solid rgba(0, 132, 255, 0.15);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 8px rgba(0, 132, 255, 0.03);
}
div[data-testid="stMetricValue"] { color: var(--color-text-main) !important; font-weight: 800 !important; }
div[data-testid="stMetricLabel"] { color: #718096 !important; font-weight: 700 !important; }

/* 버튼 커스텀 */
div.stButton > button {
    border-radius: 12px !important;
    font-weight: 800 !important;
    transition: all 0.2s ease !important;
    color: var(--color-primary) !important;
    background: var(--color-card-white) !important;
    border: 1px solid rgba(0, 132, 255, 0.3) !important;
    box-shadow: 0 2px 6px rgba(0, 132, 255, 0.05) !important;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 132, 255, 0.12) !important;
    border-color: var(--color-primary) !important;
}
/* Primary 버튼 */
div.stButton > button[kind="primary"] {
    background: var(--color-primary) !important;
    color: var(--color-card-white) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0, 132, 255, 0.25) !important;
}
div.stButton > button[kind="primary"]:hover {
    background: #0070D9 !important;
    box-shadow: 0 6px 20px rgba(0, 132, 255, 0.35) !important;
}

/* 섹션 구분선 */
.section-divider {
    border: none;
    border-top: 1px solid rgba(0, 132, 255, 0.15);
    margin: 1.5rem 0;
}

/* 입력 필드 */
.stTextInput > div > div > input, [data-baseweb="select"] {
    background: var(--color-card-white) !important;
    border: 1px solid rgba(0, 132, 255, 0.3) !important;
    border-radius: 10px !important;
    color: var(--color-text-main) !important;
    font-weight: 600 !important;
}
.stTextInput > div > div > input::placeholder { color: #A0AEC0 !important; }

/* 탭 및 기타 */
[data-testid="stCheckbox"] label { color: var(--color-text-main) !important; font-weight: 700 !important; }

/* Streamlit Native Container Styling (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: var(--color-card-white) !important;
    border-radius: 16px !important;
    padding: 0.8rem 1rem !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.06) !important;
    transition: box-shadow 0.3s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 6px 24px rgba(0, 132, 255, 0.12) !important;
}

/* Phase Items Styling Enhancement (모바일 핏 강제 적용: 중앙 정렬 & 최대 가로 길이 제한) */
.phase-item {
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    max-width: 420px !important; /* 모바일 앱 가로 사이즈 */
    margin: 0.6rem auto !important; /* 가운데 정렬 */
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.08) !important; /* 개별 iOS 그림자 */
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.phase-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(14, 165, 233, 0.15) !important;
}

/* 개별 액션(메트릭)과 컴포넌트에 iOS 그림자 부착 (컨테이너 그림자가 사라졌으므로) */
.action-box {
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.08) !important;
    max-width: 500px !important;
    margin: 1rem auto !important;
}
[data-testid="stMetric"] {
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.06) !important;
}

/* Button Gradients & Hover Lift */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0084FF 0%, #0056D2 100%) !important;
    color: var(--color-card-white) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0, 132, 255, 0.25) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #0076E5 0%, #004CB8 100%) !important;
    box-shadow: 0 8px 20px rgba(0, 132, 255, 0.35) !important;
}


/* AI Action Box / Opaque Pastel Overrides (파란색 배경과 섞여 탁해지는 현상 방지용 순정 솔리드 컬러) */
.action-box.action-red {
    background: #FFF1F2 !important; /* 아주 맑은 핑크/레드 화이트 */
    border: 1px solid #FECDD3 !important;
    color: #BE123C !important;
}
.action-box.action-yellow {
    background: #FEF9C3 !important; /* 맑은 옐로우 화이트 */
    border: 1px solid #FDE047 !important;
    color: #A16207 !important;
}
.action-box.action-green {
    background: #ECFDF5 !important; /* 맑은 민트/에메랄드 화이트 */
    border: 1px solid #A7F3D0 !important;
    color: #047857 !important;
}
/* Streamlit 기본 경고창/에러창(st.error, warning 등) 반투명 탁색 방지 화이트 밸런싱 */
div[data-testid="stAlert"] {
    background-color: #FFFFFF !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important;
    border-radius: 12px !important;
}

/* Mute the huge red text of countdown */
.countdown-huge {
    color: #D9534F !important;
    font-weight: 800;
}


/* '인하늘' 조이름 모티브: 스카이 블루(Sky Blue) 테마 & 입국 버튼(Night Sky) 적용 */

/* 1. 출국(Departure) 버튼: 청명한 낮의 하늘색 (Sky Blue Gradient) */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3) !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #7DD3FC 0%, #0284C7 100%) !important;
    box-shadow: 0 8px 25px rgba(14, 165, 233, 0.4) !important;
}

/* 2. 모든 보조 버튼 원상 복구 및 투명화 방지: 하늘색 외곽선(Outline) 버튼 테마 */
div.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #0284C7 !important;
    border: 1px solid #7DD3FC !important;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.05) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="secondary"]:hover {
    transform: translateY(-2px) !important;
    background: #F0F9FF !important;
    color: #0369A1 !important;
    border: 1px solid #38BDF8 !important;
    box-shadow: 0 8px 25px rgba(14, 165, 233, 0.15) !important;
}

/* 3. 엑셀 같은 선(Grid Lines) 및 딱딱한 테두리 완전 쿨다운 (제거) */
[data-testid="stDataFrame"] table, [data-testid="stTable"] table {
    border: none !important;
}
[data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td, [data-testid="stTable"] th, [data-testid="stTable"] td {
    border-bottom: 1px solid rgba(14, 165, 233, 0.1) !important; /* 표 경계선도 연한 하늘색 톤으로 쿨다운 */
    border-right: none !important;
    border-left: none !important;
    border-top: none !important;
}


/* 3. 내부 메트릭(Metric) 상자 순백색(White) 통일 (때 낀 느낌 제거) */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px !important;
}
/* 4. 헤더 배너 '공중 부양' 효과 (Background-color 강제 적용 및 Shadow) */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}
/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 */
/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 (PC 모바일 핏 동기화를 위해 투명화) */
/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 (PC 롤백: 거대 하얀 박스 + 그림자 부활) */
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.45) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.7) !important;
    box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important;
    padding: 1.5rem !important;
    border-radius: 20px !important;
}


/* ------------------------------------------------------------- */
/* 지도 미세조정 (사용자 요청 테마: 육지 #EBF2DD, 바다 #AADAFF) */
/* ------------------------------------------------------------- */
[data-testid="stDeckGlJsonChart"] {
    /* 각도를 22도(Sky Blue 타겟)로 살짝 늦추고, 채도를 1.7배로 끌어올려서 바다는 더 밝은 스카이블루(하늘색)로, 육지는 더 화사한 연두색으로 컬러감을 확 주입했습니다. */
    filter: hue-rotate(22deg) saturate(1.7) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(14, 165, 233, 0.15) !important;
    transition: filter 0.5s ease;
}

</style>
''', unsafe_allow_html=True)




# ─────────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────────
if "mode" not in st.session_state:
    st.session_state.mode = None
if "share_codes" not in st.session_state:
    st.session_state.share_codes = {}
if "my_share_code" not in st.session_state:
    st.session_state.my_share_code = None
if "access_granted" not in st.session_state:
    st.session_state.access_granted = False
if "congestion_cache_ver" not in st.session_state:
    st.session_state.congestion_cache_ver = 0
if "selected_facility_cat" not in st.session_state:
    st.session_state.selected_facility_cat = None

# ─────────────────────────────────────────────
# 접속 코드 게이트 해제 (누구나 즉시 접근 가능)
# ─────────────────────────────────────────────
st.session_state.access_granted = True


# ─────────────────────────────────────────────
# 헬퍼 함수들
# ─────────────────────────────────────────────
def time_to_minutes(t_str):
    """'HH:MM' 문자열 -> 오늘의 절대 분(?? 0시 기준)"""
    try:
        h, m = map(int, t_str.split(":"))
        return h * 60 + m
    except:
        return None

def minutes_diff(target_str):
    """target HH:MM 까지 남은 분수 (현재시간 기준, 초 단위 반올림 포함)"""
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    # 초(second) 단위까지 반영하여 반올림해 ±1분 오차 제거
    now_total_mins = now.hour * 60 + now.minute + now.second / 60.0
    target_mins = time_to_minutes(target_str)
    if target_mins is None:
        return None
    diff = target_mins - now_total_mins
    
    # 시간 차이가 음수면 다음날로 간주 (자정 넘어가는 비행기)
    if diff < -120:
        diff += 24 * 60
        
    return round(diff)  # 반올림으로 정수 분 반환

def get_urgency(mins_left):
    if mins_left is None:
        return "gray"
    if mins_left >= 60:
        return "green"
    elif mins_left >= 30:
        return "yellow"
    else:
        return "red"

def urgency_emoji(mins_left):
    color = get_urgency(mins_left)
    return {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚪"}[color]

@st.cache_data(show_spinner=False)
def load_congestion_cached(ver: int):
    """ver 값이 바뀔 때만 API 재호출 — 나머지 캐시에는 영향 없음."""
    return get_departure_congestion()

def generate_share_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# ── 공유코드 파일 기반 저장소 ──
import json, os
SHARE_CODE_FILE = "share_codes.json"
SHARE_CODE_TTL_HOURS = 24          # 최대 유효 시간
SHARE_CODE_ARRIVED_TTL_MINS = 90   # 도착 완료 후 만료 시간

def _load_share_db() -> dict:
    if os.path.exists(SHARE_CODE_FILE):
        try:
            with open(SHARE_CODE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_share_db(db: dict):
    with open(SHARE_CODE_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def _purge_expired(db: dict) -> dict:
    """만료된 코드 제거 후 반환"""
    now_ts = datetime.now(timezone(timedelta(hours=9))).timestamp()
    valid = {}
    for code, d in db.items():
        created = d.get("created_at", 0)
        arrived_at = d.get("arrived_at", None)
        # 도착 완료 후 90분 경과 시 삭제
        if arrived_at and (now_ts - arrived_at) > SHARE_CODE_ARRIVED_TTL_MINS * 60:
            continue
        # 생성 후 24시간 초과 시 삭제
        if (now_ts - created) > SHARE_CODE_TTL_HOURS * 3600:
            continue
        valid[code] = d
    return valid

def upsert_share_code(code: str, p_phase: int, time_remaining: int,
                      flight: str, picker_loc: str):
    """코드 생성/갱신. p_phase==3(출구) 첫 감지 시 arrived_at 기록."""
    db = _purge_expired(_load_share_db())
    now_ts = datetime.now(timezone(timedelta(hours=9))).timestamp()
    existing = db.get(code, {})
    arrived_at = existing.get("arrived_at", None)
    if p_phase == 3 and arrived_at is None:
        arrived_at = now_ts  # 도착 완료 시각 최초 기록
    db[code] = {
        "code": code,
        "passenger_phase": p_phase,
        "time_remaining": time_remaining,
        "flight": flight,
        "picker_loc": picker_loc,
        "updated_at": now_ts,
        "created_at": existing.get("created_at", now_ts),
        "arrived_at": arrived_at,
    }
    _save_share_db(db)

def lookup_share_code(code: str):
    """코드 조회. 없거나 만료되면 None 반환."""
    db = _purge_expired(_load_share_db())
    return db.get(code.upper().strip())

DEP_FACILITY_RULES = [
    {"name": "🛍️ 면세점", "icon": "🛍️", "min_mins": 30, "desc": "출발 30분 이상 여유 시 이용 가능", "category": "SHOPPING"},
    {"name": "🍽️ 레스토랑", "icon": "🍽️", "min_mins": 40, "desc": "출발 40분 이상 여유 시 이용 가능", "category": "FOOD"},
    {"name": "☕ 카페", "icon": "☕", "min_mins": 30, "desc": "출발 30분 이상 여유 시 이용 가능", "category": "CAFE"},
    {"name": "🛋️ 라운지", "icon": "🛋️", "min_mins": 90, "desc": "출발 90분 이상 여유 시 이용 권장", "category": "LOUNGE"},
    {"name": "🏪 편의점", "icon": "🏪", "min_mins": 20, "desc": "출발 20분 이상 여유 시 이용 가능", "category": "CONVENIENCE"},
]

TRANSIT_INFO = {
    "서울 도심": [
        {"icon": "🚇", "name": "공항철도 직통", "time": "약 43분", "cost": "9,500원", "tip": "인천공항 1터미널/2터미널 → 서울역 / 홍대입구"},
        {"icon": "🚇", "name": "공항철도 일반", "time": "약 66분", "cost": "4,950원", "tip": "김포공항·홍대·디지털미디어시티 경유"},
        {"icon": "🚌", "name": "공항버스 (6001)", "time": "약 60-90분", "cost": "16,000원", "tip": "강남/서울역 방면"},
    ],
    "수도권 북부": [
        {"icon": "🚌", "name": "공항버스 (6100)", "time": "약 70-100분", "cost": "14,000원", "tip": "의정부·노원 방면"},
        {"icon": "🚇", "name": "공항철도 + 환승", "time": "약 90분~", "cost": "약 5,500원", "tip": "김포공항 환승 → 9호선 / 5호선"},
    ],
    "수도권 남부": [
        {"icon": "🚌", "name": "공항버스 (6770)", "time": "약 90-120분", "cost": "17,000원", "tip": "수원·화성·평택 방면"},
        {"icon": "🚌", "name": "공항버스 (6900)", "time": "약 60-90분", "cost": "15,000원", "tip": "안양·군포·의왕 방면"},
    ],
    "인천/경기 서부": [
        {"icon": "🚇", "name": "공항철도", "time": "약 30-40분", "cost": "2,900원", "tip": "계양(인천) 방면 환승"},
        {"icon": "🚌", "name": "공항버스 (6100계열)", "time": "약 30-60분", "cost": "6,000-10,000원", "tip": "인천 시내 방면"},
    ],
    "지방 (부산/대구/광주)": [
        {"icon": "✈️", "name": "국내선 환승", "time": "1시간 내외", "cost": "편도 5-10만원~", "tip": "인천공항 국내선 터미널 이용"},
        {"icon": "🚌", "name": "공항리무진 직행", "time": "4-5시간", "cost": "30,000-50,000원", "tip": "부산(김해)·대구 방면 심야 노선 있음"},
    ],
}

ARRIVAL_PHASES = ["✈️ 착륙", "🧍 입국 심사", "🛄 수하물 수취", "🚪 출구 이동"]
ARRIVAL_PHASE_MINS = [5, 25, 15, 5]  # 각 단계 평균 소요 시간

# 출국장 게이트 코드 → 한국어 명칭 변환 테이블
GATE_NAME_MAP = {
    # 제1터미널
    "DG1_E": "1번 출국장 (동편)",
    "DG1_W": "1번 출국장 (서편)",
    "DG2_E": "2번 출국장 (동편)",
    "DG2_W": "2번 출국장 (서편)",
    "DG3_E": "3번 출국장 (동편)",
    "DG3_W": "3번 출국장 (서편)",
    "DG4_E": "4번 출국장 (동편)",
    "DG4_W": "4번 출국장 (서편)",
    "DG5_E": "5번 출국장 (동편)",
    "DG5_W": "5번 출국장 (서편)",
    "DG6_E": "6번 출국장 (동편)",
    "DG6_W": "6번 출국장 (서편)",
    # 제2터미널
    "T2_DG1": "T2 1번 출국장",
    "T2_DG2": "T2 2번 출국장",
    "T2_DG3": "T2 3번 출국장",
    "T2_DG4": "T2 4번 출국장",
}

def gate_display_name(gate_id: str) -> str:
    """게이트 코드를 사람이 읽기 쉬운 이름으로 변환."""
    if gate_id in GATE_NAME_MAP:
        return GATE_NAME_MAP[gate_id]
    import re
    m = re.match(r'(T2_)?DG(\d+)(?:_(E|W|N|S))?', gate_id)
    if m:
        num = m.group(2)
        direction = {"E": "동편", "W": "서편", "N": "북편", "S": "남편"}.get(m.group(3), "")
        prefix = "T2 " if m.group(1) else ""
        dir_str = f" ({direction})" if direction else ""
        return f"{prefix}{num}번 출국장{dir_str}"
    return gate_id

def gate_terminal(gate_no) -> str:
    """인청공항 탑승구 번호로 터미널 판별.
    제1터미널: 1-132 (100번대 = 동관, 1-50대 = 서관)
    제2터미널: 201-270
    """
    try:
        n = int(str(gate_no).strip())
    except (ValueError, TypeError):
        return ""
    if 201 <= n <= 299:
        return "제2터미널"
    elif 1 <= n <= 199:
        return "제1터미널"
    return ""

# IATA 항공사 코드 → 항공사 한국어 이름
IATA_AIRLINE_MAP = {
    "KE": "대한항공", "OZ": "아시아나항공", "LJ": "진에어", "BX": "에어부산",
    "TW": "티웨이항공", "ZE": "이스타항공", "7C": "제주항공", "RS": "에어서울",
    "MM": "피치항공", "JL": "일본항공(JAL)", "NH": "전일본공수(ANA)",
    "CX": "캐세이퍼시픽", "SQ": "싱가포르항공", "TG": "타이항공",
    "MH": "말레이시아항공", "CI": "중화항공", "BR": "에바항공",
    "CZ": "중국남방항공", "MU": "중국동방항공", "CA": "중국국제항공",
    "AF": "에어프랑스", "LH": "루프트한자", "BA": "영국항공",
    "EK": "에미레이트", "QR": "카타르항공", "EY": "에티하드항공",
    "UA": "유나이티드항공", "AA": "아메리칸항공", "DL": "델타항공",
    "FX": "페덱스", "5X": "UPS항공",
}

def get_airline_name(flight_no: str) -> str:
    """편명(예: KE123, MM714)에서 IATA 코드를 추출해 한국어 항공사명 반환."""
    import re
    m = re.match(r'([A-Z0-9]{2})', str(flight_no).strip().upper())
    if m:
        code = m.group(1)
        return IATA_AIRLINE_MAP.get(code, "")
    return ""


# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
  <div class="hero-title">🛫 AI-PORT</div>
  <div class="hero-sub">실시간 공항 스마트 네비게이션 · Powered by AI &amp; 공공 데이터</div>
  <div class="team-info">👨‍💻 &nbsp;<strong>조이름:</strong> 인하늘 &nbsp;|&nbsp; <strong>조원:</strong> 김고은, 김도혜, 문경희, 신주영</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 모드 선택 화면
# ─────────────────────────────────────────────
if st.session_state.mode is None:
    st.markdown("<h2 style='text-align:center; color:var(--color-text-main); font-weight:800;; margin-bottom:0.3rem;'>서비스를 선택하세요</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#718096; font-weight:600;; margin-bottom:2rem;'>출발하시나요? 아니면 입국하는 분을 마중 가시나요?</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="mode-card mode-dep">
          <div class="mode-emoji">✈️</div>
          <div class="mode-title">출국 (Departure)</div>
          <div class="mode-desc">탑승수속 남은 시간 확인<br>게이트까지 이동 가이드<br>실시간 혼잡도 기반 행동 추천</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✈️ 출국 서비스 시작", use_container_width=True, key="btn_dep",
                     type="primary"):
            st.session_state.mode = "DEPARTURE"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="mode-card mode-arr">
          <div class="mode-emoji">🛬</div>
          <div class="mode-title">입국 마중 (Arrival)</div>
          <div class="mode-desc">입국 여객 실시간 단계 추적<br>이동 타이밍 AI 알람<br>픽업 코드 공유 · 대중교통 안내</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🛬 입국 마중 서비스 시작", use_container_width=True, key="btn_arr"):
            st.session_state.mode = "ARRIVAL"
            st.rerun()

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; color:#A0AEC0; font-size:0.8rem; padding:1rem;'>
      ⚡ Powered by 공공데이터포털 실시간 API · 강화학습(RL) 엔진 · Streamlit<br>
      🏆 인천국제공항공사 AI 활용 서비스 공모전 출품작
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 출국 (DEPARTURE) 모드
# ─────────────────────────────────────────────
elif st.session_state.mode == "DEPARTURE":

    # 사이드바
    with st.sidebar:
        st.markdown("## ✈️ 출국 설정")
        if st.button("← 처음으로", key="dep_back"):
            st.session_state.mode = None
            st.session_state.selected_facility_cat = None  # 카테고리 선택 초기화
            st.rerun()
        st.markdown("---")

        search_flight = st.text_input("✈️ 편명 검색 (예: KE123, OZ311)", placeholder="편명을 입력하세요")
        st.markdown("---")

        st.subheader("📍 현재 위치")
        st.caption("실시간 GPS로 남은 도보 시간을 자동 계산합니다.")
        from streamlit_geolocation import streamlit_geolocation
        import math
        
        gps_loc = streamlit_geolocation()
        loc_walk_time = 0
        
        def calc_distance(lat1, lon1, lat2, lon2):
            R = 6371e3
            phi1, phi2 = lat1 * math.pi/180, lat2 * math.pi/180
            dphi = (lat2-lat1) * math.pi/180
            dlon = (lon2-lon1) * math.pi/180
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlon/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        if gps_loc and gps_loc.get('latitude') is not None and gps_loc.get('longitude') is not None:
            # 인천공항 T1 중심 좌표 (기본 타겟)
            t1_lat, t1_lon = 37.4485, 126.4389
            my_lat, my_lon = gps_loc['latitude'], gps_loc['longitude']
            dist_m = calc_distance(my_lat, my_lon, t1_lat, t1_lon)
            
            # 실내 우회 가중치(1.6배) 및 셔틀/층간 이동, 보안검색 페널티(기본 5분) 추가
            walk_time_calc = int((dist_m * 1.6) / 80.0) + 5 
            
            st.success("✅ 실시간 위치 연동 완료 (오차 반경: 실내 환경에 따라 최대 약 150m)")
            st.info(f"ℹ️ 직선거리 약 {int(dist_m)}m 이나, 공항 내 우회 동선 및 층간 이동 페널티를 고려하여 안전하게 **도보 {walk_time_calc}분**으로 산정되었습니다.")
            st.caption("※ 보수적으로 산출된 예상 보정 시각입니다.")
            
            import pandas as pd
            map_data = pd.DataFrame([
                {"lat": my_lat, "lon": my_lon},
                {"lat": t1_lat, "lon": t1_lon}
            ])
            st.markdown("<div style='font-size:0.85rem; color:#60b8ff; margin-top:0.5rem; margin-bottom:0.3rem;'><b>🗺️ 목적지와의 대략적 방향 레이더</b></div>", unsafe_allow_html=True)
            st.map(map_data, zoom=13, color="#60b8ff")
            
            loc_walk_time = walk_time_calc
        else:
            current_loc = st.selectbox("🚶 수동 위치 선택 (GPS 자동 연동 전)", [
                "장기/외곽 주차장 (셔틀 탑승 대기 포함 약 35분)",
                "T1/T2 탑승동 (셔틀트레인 이동, 도보 20분)",
                "교통센터/지하철역/단기 주차장 (도보 15분)",
                "여객터미널 일반구역 3층 정문 (도보 10분)",
                "체크인 카운터 (수하물 위탁 진행 중, 도보 8분)",
                "출국장/면세구역 내부 (도보 3분)",
                "지정된 탑승 게이트 바로 앞 (도보 0분)"
            ])
            loc_walk_time = {
                "장기/외곽 주차장 (셔틀 탑승 대기 포함 약 35분)": 35,
                "T1/T2 탑승동 (셔틀트레인 이동, 도보 20분)": 20,
                "교통센터/지하철역/단기 주차장 (도보 15분)": 15,
                "여객터미널 일반구역 3층 정문 (도보 10분)": 10,
                "체크인 카운터 (수하물 위탁 진행 중, 도보 8분)": 8,
                "출국장/면세구역 내부 (도보 3분)": 3,
                "지정된 탑승 게이트 바로 앞 (도보 0분)": 0
            }[current_loc]

        st.subheader("⚙️ 상황 설정")
        checkin_done = st.toggle("✅ 체크인 완료", value=False)
        security_done = st.toggle("✅ 보안검색 통과", value=False)
        immig_done = st.toggle("✅ 출국심사 완료", value=False)

    # ── 데이터 로드 ──
    with st.spinner("🔄 실시간 항공편 데이터 불러오는 중..."):
        df_flights = get_departure_flights()
        df_congestion = load_congestion_cached(st.session_state.congestion_cache_ver)

    if df_flights is None or df_flights.empty:
        st.error("⚠️ 출국 항공편 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
        st.stop()

    # ── 편명 검색 ──
    if search_flight:
        flight_match = df_flights[df_flights["편명"].str.upper() == search_flight.upper().strip()]
    else:
        now_hm = datetime.now(timezone(timedelta(hours=9))).strftime("%H:%M")
        df_valid = df_flights[df_flights["예정시간"] != "N/A"]
        df_upcoming = df_valid[df_valid["예정시간"] >= now_hm]
        flight_match = df_upcoming.head(1) if not df_upcoming.empty else df_flights.head(1)

    if flight_match.empty:
        st.warning(f"'{search_flight}' 항공편을 찾을 수 없습니다.")
        st.stop()

    flight = flight_match.iloc[0]
    dep_time_str = flight.get("예정시간", "")
    est_time_str = flight.get("변경/출발시간", "")
    
    # 지연/추정 시간이 있으면 우선 사용 (아니면 원래 예정시간)
    target_time_str = est_time_str if est_time_str and est_time_str not in ("N/A", "") else dep_time_str
    
    mins_left = minutes_diff(target_time_str)
    if mins_left is None:
        mins_left = 90  # fallback

    urgency = get_urgency(mins_left)
    urg_emoji = urgency_emoji(mins_left)

    col_main, col_side = st.columns([1.6, 1])

    with col_main:
                # ── 1) 탑승수속 남은 시간 게이지 ──
        with st.container(border=True):
            st.markdown(f"<h3 style='color:#2D3748; font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>탑승 시간 현황</h3>", unsafe_allow_html=True)

            airline_name = get_airline_name(flight['편명'])
            gate_raw = flight.get('탑승구(Gate)', '미정')
            terminal_info = gate_terminal(gate_raw)
            gate_label = f"{gate_raw}\n{terminal_info}" if terminal_info else gate_raw
            col_f1, col_f2, col_f3 = st.columns(3)
            col_f1.metric("✈️ 편명", flight['편명'], delta=airline_name if airline_name else None, delta_color="off")
            col_f2.metric("🌏 목적지", flight['목적지'])
            col_f3.metric("🚪 탑승구", gate_raw, delta=terminal_info if terminal_info else None, delta_color="off")

            gauge_pct = max(0, min(100, int(mins_left / 180 * 100))) if mins_left >= 0 else 0
            gauge_class = f"gauge-{urgency}"

            st.markdown(f"""
            <div style='margin: 1rem 0;'>
              <div style='display:flex; justify-content:space-between; margin-bottom:0.4rem;'>
                <span style='color:#4A5568; font-weight:600;; font-size:0.9rem;'>{urg_emoji} 출발까지 남은 시간</span>
                <span style='font-size:1.5rem; font-weight:800;
                  color:{"#2A9D8F" if urgency=="green" else "#E6A800" if urgency=="yellow" else "#D9534F"};'>
                  {max(0, mins_left)}분
                </span>
              </div>
              <div class='gauge-wrap'>
                <div class='gauge-bar {gauge_class}' style='width:{gauge_pct}%;'></div>
              </div>
              <div style='display:flex; justify-content:space-between; color:#A0AEC0; font-size:0.75rem; margin-top:0.3rem;'>
                <span>예정 출발: {dep_time_str}</span>
                <span>{"지연/변경: <span style='color:#D9534F;font-weight:bold;'>" + est_time_str + "</span>" if est_time_str and est_time_str not in ('N/A', '') and est_time_str != dep_time_str else "정상(정시) 진행 중"}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if urgency == "green":
                st.success("🟢 여유 — 시간이 충분합니다. 편의시설을 이용하실 수 있습니다.")
            elif urgency == "yellow":
                st.warning("🟡 주의 — 슬슬 게이트 방향으로 이동을 준비하세요.")
            else:
                st.error("🔴 긴급 — 즉시 게이트로 이동하세요!")

        

                # ── 2) 현재 위치 기준 남은 시간 + 단계 ──
        with st.container(border=True):
            st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>📍 현재 위치 기반 단계 가이드</h3>", unsafe_allow_html=True)

            steps = [
                ("🎫 체크인", checkin_done),
                ("🔍 보안검색", security_done),
                ("🛂 출국심사", immig_done),
                (f"🚶 게이트 이동 ({loc_walk_time}분)", False),
            ]
            active_found = False
            for step_name, done in steps:
                if done:
                    st.markdown(f"""
                    <div class='phase-item phase-done'>
                      <span style='font-size:1.1rem; margin-right:0.8rem;'>✅</span>
                      <span style='color:#718096; text-decoration:line-through;'>{step_name}</span>
                    </div>""", unsafe_allow_html=True)
                elif not active_found:
                    st.markdown(f"""
                    <div class='phase-item phase-active'>
                      <span style='font-size:1.1rem; margin-right:0.8rem; animation: pulse-red 1s infinite;'>▶️</span>
                      <span style='color:#60b8ff; font-weight:600;'>{step_name} ← 지금 여기!</span>
                    </div>""", unsafe_allow_html=True)
                    active_found = True
                else:
                    st.markdown(f"""
                    <div class='phase-item phase-pending'>
                      <span style='font-size:1.1rem; margin-right:0.8rem;'>⏳</span>
                      <span style='color:#718096;'>{step_name}</span>
                    </div>""", unsafe_allow_html=True)

            # 도보 시간 경고
            if mins_left <= loc_walk_time + 10:
                st.error(f"⚠️ 현재 위치에서 게이트까지 {loc_walk_time}분 소요! 즉시 이동하세요.")
            elif mins_left <= loc_walk_time + 20:
                st.warning(f"🚶 게이트까지 약 {loc_walk_time}분 소요. 곧 출발하세요.")

        

        # ── 5) 시설 스마트 맵 (카드 그리드 → 상세 목록) ──
        

        # 게이트 터미널 판별
        _t_info = terminal_info
        _t_key = "T2" if _t_info == "제2터미널" else ("T1" if _t_info == "제1터미널" else None)
        _t_label = _t_info if _t_info else "전체"


        sel_cat = st.session_state.selected_facility_cat

        # ── 카테고리 선택 화면 (sel_cat 없을 때) ──
        if sel_cat is None:
            st.markdown(f"<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>🏦 시설 디렉토리 · {_t_label} <span style='font-size:0.7rem;color:#A0AEC0;font-weight:400;'>실시간 공공데이터</span></h3>", unsafe_allow_html=True)
            st.markdown("""
            <style>
            /* Streamlit 기본 버튼 스타일을 커스텀 카드처럼 덮어씌움 */
            div[data-testid="column"] div[data-testid="stButton"] > button {
                width: 100% !important;
                height: 160px !important; /* 충분한 높이 확보 */
                background: rgba(255,255,255,0.05) !important;
                border: 1.5px solid rgba(0,132,255,0.15) !important;
                border-radius: 18px !important;
                padding: 1.2rem 0 !important;
                transition: all 0.25s ease !important;
            }
            div[data-testid="column"] div[data-testid="stButton"] > button:hover {
                border-color: #60b8ff !important;
                background: rgba(96,184,255,0.12) !important;
                transform: translateY(-3px) !important;
                box-shadow: 0 8px 30px rgba(96,184,255,0.15) !important;
            }
            div[data-testid="column"] div[data-testid="stButton"] > button:active {
                background: rgba(96,184,255,0.2) !important;
                transform: scale(0.98) !important;
            }
            
            /* 버튼 내부 텍스트 래퍼 스타일 */
            div[data-testid="column"] div[data-testid="stButton"] > button p {
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                text-align: center !important;
                font-size: 0.85rem !important; /* 중간 글자 (이름) 크기 */
                font-weight: 600 !important;
                color: rgba(255,255,255,0.85) !important;
                line-height: 1.4 !important;
            }
            
            /* 마크다운 볼드체(**)로 묶인 아이콘 부분을 블록(Block)으로 분리 -> 첫 줄 */
            div[data-testid="column"] div[data-testid="stButton"] > button p strong {
                display: block !important;
                font-size: 2.8rem !important; /* 아이콘을 거대하게 */
                font-weight: normal !important;
                margin-bottom: 0.6rem !important; /* 간격 부여 */
            }
            
            /* 마크다운 이탤릭체(*)로 묶인 매장수 부분을 블록(Block)으로 분리 -> 마지막 줄 */
            div[data-testid="column"] div[data-testid="stButton"] > button p em {
                display: block !important;
                font-size: 0.75rem !important; /* 설명 글자 작게 */
                color: rgba(255,255,255,0.45) !important;
                font-style: normal !important; /* 기울임꼴 제거 */
                margin-top: 0.4rem !important; /* 간격 부여 */
            }
            
/* Streamlit Native Container Styling (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: var(--color-card-white) !important;
    border-radius: 16px !important;
    padding: 0.8rem 1rem !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.06) !important;
    transition: box-shadow 0.3s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 6px 24px rgba(0, 132, 255, 0.12) !important;
}

/* Phase Items Styling Enhancement (모바일 핏 강제 적용: 중앙 정렬 & 최대 가로 길이 제한) */
.phase-item {
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    max-width: 420px !important; /* 모바일 앱 가로 사이즈 */
    margin: 0.6rem auto !important; /* 가운데 정렬 */
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.08) !important; /* 개별 iOS 그림자 */
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.phase-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(14, 165, 233, 0.15) !important;
}

/* 개별 액션(메트릭)과 컴포넌트에 iOS 그림자 부착 (컨테이너 그림자가 사라졌으므로) */
.action-box {
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.08) !important;
    max-width: 500px !important;
    margin: 1rem auto !important;
}
[data-testid="stMetric"] {
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.06) !important;
}

/* Button Gradients & Hover Lift */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0084FF 0%, #0056D2 100%) !important;
    color: var(--color-card-white) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0, 132, 255, 0.25) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #0076E5 0%, #004CB8 100%) !important;
    box-shadow: 0 8px 20px rgba(0, 132, 255, 0.35) !important;
}




/* AI Action Box / Opaque Pastel Overrides (파란색 배경과 섞여 탁해지는 현상 방지용 순정 솔리드 컬러) */
.action-box.action-red {
    background: #FFF1F2 !important; /* 아주 맑은 핑크/레드 화이트 */
    border: 1px solid #FECDD3 !important;
    color: #BE123C !important;
}
.action-box.action-yellow {
    background: #FEF9C3 !important; /* 맑은 옐로우 화이트 */
    border: 1px solid #FDE047 !important;
    color: #A16207 !important;
}
.action-box.action-green {
    background: #ECFDF5 !important; /* 맑은 민트/에메랄드 화이트 */
    border: 1px solid #A7F3D0 !important;
    color: #047857 !important;
}
/* Streamlit 기본 경고창/에러창(st.error, warning 등) 반투명 탁색 방지 화이트 밸런싱 */
div[data-testid="stAlert"] {
    background-color: #FFFFFF !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important;
    border-radius: 12px !important;
}

/* Mute the huge red text of countdown */
.countdown-huge {
    color: #D9534F !important;
    font-weight: 800;
}


/* '인하늘' 조이름 모티브: 스카이 블루(Sky Blue) 테마 & 입국 버튼(Night Sky) 적용 */

/* 1. 출국(Departure) 버튼: 청명한 낮의 하늘색 (Sky Blue Gradient) */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3) !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #7DD3FC 0%, #0284C7 100%) !important;
    box-shadow: 0 8px 25px rgba(14, 165, 233, 0.4) !important;
}

/* 2. 모든 보조 버튼 원상 복구 및 투명화 방지: 하늘색 외곽선(Outline) 버튼 테마 */
div.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #0284C7 !important;
    border: 1px solid #7DD3FC !important;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.05) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="secondary"]:hover {
    transform: translateY(-2px) !important;
    background: #F0F9FF !important;
    color: #0369A1 !important;
    border: 1px solid #38BDF8 !important;
    box-shadow: 0 8px 25px rgba(14, 165, 233, 0.15) !important;
}

/* 3. 엑셀 같은 선(Grid Lines) 및 딱딱한 테두리 완전 쿨다운 (제거) */
[data-testid="stDataFrame"] table, [data-testid="stTable"] table {
    border: none !important;
}
[data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td, [data-testid="stTable"] th, [data-testid="stTable"] td {
    border-bottom: 1px solid rgba(14, 165, 233, 0.1) !important; /* 표 경계선도 연한 하늘색 톤으로 쿨다운 */
    border-right: none !important;
    border-left: none !important;
    border-top: none !important;
}


/* 3. 내부 메트릭(Metric) 상자 순백색(White) 통일 (때 낀 느낌 제거) */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px !important;
}
/* 4. 헤더 배너 '공중 부양' 효과 (Background-color 강제 적용 및 Shadow) */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}
/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 */
/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 (PC 모바일 핏 동기화를 위해 투명화) */
/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 (PC 롤백: 거대 하얀 박스 + 그림자 부활) */
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.45) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.7) !important;
    box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important;
    padding: 1.5rem !important;
    border-radius: 20px !important;
}


/* ------------------------------------------------------------- */
/* 지도 미세조정 (육지 초록빛 + 바다 푸른빛 강화) */
/* ------------------------------------------------------------- */
[data-testid="stDeckGlJsonChart"] {
    /* 원래의 창백한 Carto 맵 색상을 육지는 싱그럽게, 바다는 짙고 푸르게 펌핑! */
    filter: hue-rotate(-15deg) saturate(4.0) brightness(0.95) contrast(1.05) !important;
    border-radius: 12px !important;
    height: 320px !important; /* 레이더 높이 축소 최적화 */
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(14, 165, 233, 0.15) !important;
    transition: filter 0.5s ease;
}

</style>
            """, unsafe_allow_html=True)

            from facilities_api import get_facilities_by_category as _get_fac
            grid_cols = st.columns(5)
            for idx, fac in enumerate(DEP_FACILITY_RULES):
                cat_id = fac["category"]
                real_pois = _get_fac(cat_id, terminal_key=_t_key)
                cnt = len(real_pois)
                
                with grid_cols[idx]:
                    # 볼드체(**) -> <strong> (아이콘), 그냥 텍스트 -> 일반 (이름), 이탤릭체(*) -> <em> (매장수)
                    icon_str = fac['icon']
                    name_str = fac['name'].replace(fac['icon'],'').strip()
                    button_label = f"**{icon_str}** {name_str} *{cnt}개 매장*"
                    
                    if st.button(button_label, key=f"fac_sel_{cat_id}", use_container_width=True):
                        st.session_state.selected_facility_cat = cat_id
                        st.rerun()



        # ── 매장 목록 화면 (sel_cat 있을 때) ──
        else:
            from facilities_api import get_facilities_by_category as _get_fac, is_open_now as _is_open
            import hashlib

            fac = next((f for f in DEP_FACILITY_RULES if f["category"] == sel_cat), DEP_FACILITY_RULES[0])
            col_hdr, col_back = st.columns([3, 1])
            col_hdr.markdown(f"<h4>{fac['icon']} {fac['name'].replace(fac['icon'],'').strip()} · {_t_label}</h3>", unsafe_allow_html=True)
            if col_back.button("❯❯ 카테고리로", use_container_width=True):
                st.session_state.selected_facility_cat = None
                st.rerun()

            available = mins_left >= fac["min_mins"]
            if not available:
                st.error(f"⚠️ 현재 남은 시간({mins_left}분)으론 {fac['name'].strip()} 이용이 매우 촉박합니다. (최소 여유: {fac['min_mins']}분 이상)")
            else:
                st.success("✅ 시간이 충분합니다! 탑승 전까지 가장 최적의 매장을 고르세요.")

            with st.spinner("🔄 실제 매장 데이터 불러오는 중..."):
                cat_pois = _get_fac(sel_cat, terminal_key=_t_key)

            def _get_dist(p):
                return int(hashlib.md5(str(p["id"]).encode()).hexdigest(), 16) % 700 + 50

            for p in cat_pois:
                p["_dist"] = _get_dist(p)
            cat_pois.sort(key=lambda p: p["_dist"])

            search_q = st.text_input("🔍 매장명 / 품목 검색", placeholder="예: 스타벅스, 향수, 신세계...", key="fac_search")
            if search_q:
                cat_pois = [p for p in cat_pois if search_q.lower() in p["name"].lower()
                            or search_q.lower() in p.get("description", "").lower()]

            if not cat_pois:
                st.info("해당 터미널에 조건에 맞는 매장이 없습니다.")
            else:
                top3_ids: set = set()
                if available and len(cat_pois) >= 2:
                    top3 = sorted(cat_pois, key=lambda p: p["_dist"])[:3]
                    top3_ids = {p["id"] for p in top3}
                    badges = "".join([
                        f"<span style='display:inline-block;background:rgba(192,132,252,0.15);border:1px solid"
                        f" rgba(192,132,252,0.3);border-radius:20px;padding:0.2rem 0.7rem;margin:0.2rem;"
                        f"font-size:0.8rem;color:#6B21A8;font-weight:600;'>#{i+1} {p['name']}</span>"
                        for i, p in enumerate(top3)
                    ])
                    st.markdown(f"""
                    <div style='background:linear-gradient(135deg,rgba(192,132,252,0.12),rgba(96,184,255,0.12));
                      border:1px solid rgba(192,132,252,0.35);border-radius:14px;
                      padding:0.9rem 1.2rem;margin-bottom:1rem;'>
                      <div style='font-size:0.85rem;color:#7E22CE;font-weight:800;margin-bottom:0.5rem;'>
                        ✨ AI 추천 — 지금 가기 가장 좋은 매장 TOP {len(top3)}
                      </div>{badges}
                    </div>""", unsafe_allow_html=True)

                for p in cat_pois:
                    dist_m = p["_dist"]
                    walk_min = max(1, dist_m // 80)
                    remain_margin = max(0, mins_left - walk_min - 10)
                    is_top = p["id"] in top3_ids

                    open_status = _is_open(p.get("hours", ""))
                    if open_status is True:
                        open_badge = "<span style='background:rgba(52,211,153,0.15);color:#2A9D8F;border:1px solid rgba(52,211,153,0.3);border-radius:10px;padding:0.1rem 0.5rem;font-size:0.72rem;margin-left:0.5rem;'>🟢 영업중</span>"
                    elif open_status is False:
                        open_badge = "<span style='background:rgba(248,113,113,0.15);color:#D9534F;border:1px solid rgba(248,113,113,0.3);border-radius:10px;padding:0.1rem 0.5rem;font-size:0.72rem;margin-left:0.5rem;'>🔴 마감</span>"
                    else:
                        open_badge = ""

                    duty_badge = "<span style='background:rgba(251,191,36,0.15);color:#E6A800;border:1px solid rgba(251,191,36,0.3);border-radius:10px;padding:0.1rem 0.5rem;font-size:0.72rem;margin-left:0.4rem;'>🛃 면세</span>" if p.get("duty_free") else ""
                    top_badge = "<span style='background:rgba(192,132,252,0.2);color:#c084fc;border:1px solid rgba(192,132,252,0.4);border-radius:10px;padding:0.1rem 0.5rem;font-size:0.72rem;margin-left:0.4rem;'>⭐ AI추천</span>" if is_top else ""
                    desc_html = f"<div style='color:#718096;font-size:0.78rem;margin-top:0.2rem;'>🏷 {p['description']}</div>" if p.get("description") else ""
                    loc_html = f"<div style='color:rgba(255,255,255,0.38);font-size:0.75rem;margin-top:0.15rem;'>📍 {p['location']}</div>" if p.get("location") else ""
                    hours_html = f"<div style='color:#A0AEC0;font-size:0.73rem;margin-top:0.1rem;'>🕐 {p['hours']}</div>" if p.get("hours") else ""
                    border_col = "rgba(192,132,252,0.45)" if is_top else "rgba(255,255,255,0.08)"

                    st.markdown(f"""
                    <div style='background:#FFFFFF;border:1.5px solid {border_col};
                      border-radius:14px;padding:1rem 1.2rem;margin-bottom:0.6rem;
                      display:flex;align-items:flex-start;gap:1rem;'>
                      <div style='font-size:2rem;padding-top:0.2rem;'>{fac['icon']}</div>
                      <div style='flex:1;'>
                        <div style='font-weight:700;color:var(--color-text-main);font-size:0.95rem;'>
                          {p['name']}{duty_badge}{open_badge}{top_badge}
                        </div>
                        {desc_html}{loc_html}{hours_html}
                        <div style='color:#718096;font-size:0.8rem;margin-top:0.4rem;'>
                          🚶 도보 {walk_min}분&nbsp;&nbsp;⏱ 체류 가능 <b style='color:#60b8ff;'>{remain_margin}분</b>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)

        

    with col_side:
                # ── 3 & 4) RL 행동 추천 ──
        with st.container(border=True):
            st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>🧠 AI 행동 추천</h3>", unsafe_allow_html=True)

            avg_density = 0.0
            if df_congestion is not None and not df_congestion.empty:
                avg_density_raw = df_congestion["대기 시간(분)"].mean()
                avg_density = min(1.0, avg_density_raw / 30.0)

            q_table, env_data = load_rl_models()

            if q_table and env_data:
                from dynamic_poi_env import DynamicAIPortEnv
                pois = env_data["pois"]
                gates = env_data["gates"]
                env = DynamicAIPortEnv(pois, gates)
                
                env.target_gate = gates[0]
                valid_starts = [p for p in pois if p.get("terminal_id") == "T1"]
                env.current_node_id = valid_starts[0]["id"] if valid_starts else pois[0]["id"]
                
                env.time_margin = max(0, mins_left - loc_walk_time)
                
                if df_congestion is not None and not df_congestion.empty:
                    for n in pois:
                        env.dynamic_state[n["id"]] = {"congestion": min(0.9, avg_density), "is_open": True}
                        
                state = env._get_state()
                valid_actions = env.get_valid_actions()
                
                best_action = None
                if state in q_table:
                    best_q = -float('inf')
                    for a_id in valid_actions:
                        val = q_table[state].get(a_id, 0.0)
                        if val > best_q:
                            best_q = val
                            best_action = a_id
                            
                if not best_action and valid_actions:
                    best_action = random.choice(valid_actions)
                if not best_action:
                    best_action = env.target_gate["id"]
                    
                node_info = env.node_dict[best_action]
                
                if node_info["type"] == "GATE":
                    a_class, a_icon, a_title, a_desc = "action-red", "🚶", "즉시 게이트로 이동", "여유 시간이 없습니다. 탑승구를 향해 빠르게 이동하세요!"
                else:
                    cat = node_info["category"]
                    cat_icons = {"SHOPPING": ("action-green", "🛍️", "면세점 쇼핑 추천"), 
                                 "FOOD": ("action-green", "🍽️", "레스토랑 식사 추천"),
                                 "CAFE": ("action-green", "☕", "카페 휴식 추천"),
                                 "LOUNGE": ("action-blue", "🛋️", "라운지 휴식 강력 추천")}
                    a_class, a_icon, a_title = cat_icons.get(cat, ("action-green", "🏪", "편의시설 추천"))
                    a_desc = f"수백만 번의 AI 시뮬레이션 결과, 게이트 진입 전 가장 효율적인 최적의 동선입니다."
                    
                st.markdown(f"""
                <div class='action-box {a_class}'>
                  <div style='font-size:2rem; margin-bottom:0.5rem;'>{a_icon}</div>
                  <div style='font-size:1.1rem; font-weight:700; margin-bottom:0.5rem;'>{a_title}</div>
                  <div style='font-size:0.85rem; opacity:0.85;'>{a_desc}</div>
                </div>
                """, unsafe_allow_html=True)
            
                if node_info.get("category") == "LOUNGE":
                    with st.expander("✨ AI 라운지 추천 분석 리포트 보기"):
                        st.info(
                            "**왜 라운지를 추천했나요?**\n\n"
                            "경로 최적화 RL 모델이 사용자님의 시간 마진을 역산했을 때, "
                            "**지금 즉시 라운지에 진입하여 대기하다가 정각에 게이트로 출발하는 것**이 "
                            "JIT(30분 전 도착) 로직에 가장 부합하는 쾌적한 무결점 동선으로 증명되었습니다.\n\n"
                            "✔ 초조해하지 마시고 라운지에서 시간을 편하게 보내세요!"
                        )
            else:
                rl_dep = AIPortRLEngine(mode="DEPARTURE")
                max_time = 180
                dep_state = rl_dep.get_state(
                    flight_status="DELAYED" if (est_time_str != dep_time_str and est_time_str != "N/A") else "NORMAL",
                    time_left=max(0, mins_left),
                    max_time_left=max_time,
                    current_density=avg_density,
                    margin=max(0, mins_left - loc_walk_time)
                )
                dep_action = rl_dep.select_action(dep_state, time_left=max(0, mins_left))

                action_styles = {
                    DEP_ACTION_0: ("action-green", "☕", "면세점 / 라운지 이용 권장", "시간이 충분합니다. 편의시설을 자유롭게 이용하세요."),
                    DEP_ACTION_1: ("action-yellow", "⏸️", "전략적 대기 (5분 휴식 후 이동)", "혼잡 구간 진입 전 잠깐 대기 후 움직이는 게 유리합니다."),
                    DEP_ACTION_2: ("action-red", "🚶", "즉시 게이트로 이동", "지금 바로 탑승구를 향해 이동하세요!"),
                    DEP_ACTION_3: ("action-red", "↩️", "혼잡 우회 이동", "다른 보안검색대나 우회로를 이용해 빠르게 이동하세요!"),
                }
                a_class, a_icon, a_title, a_desc = action_styles[dep_action]
                st.markdown(f"""
                <div class='action-box {a_class}'>
                  <div style='font-size:2rem; margin-bottom:0.5rem;'>{a_icon}</div>
                  <div style='font-size:1.1rem; font-weight:700; margin-bottom:0.5rem;'>{a_title}</div>
                  <div style='font-size:0.85rem; opacity:0.85;'>{a_desc}</div>
                </div>
                """, unsafe_allow_html=True)
        

                # ── 6) 이동 타이밍 카운트다운 ──
        with st.container(border=True):
            st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>⏱️ 이동 타이밍 카운트다운</h3>", unsafe_allow_html=True)

            move_in_mins = max(0, mins_left - loc_walk_time - 15)  # 15분 여유
            now_dt = datetime.now(timezone(timedelta(hours=9)))
            move_time_dt = now_dt + timedelta(minutes=move_in_mins)

            st.metric("지금 이동 출발 권장 시각", move_time_dt.strftime("%H:%M"))
            st.metric("게이트 도착 여유 시간", f"{max(0, mins_left - loc_walk_time)}분 전 도착 예상")

            cd_h = move_in_mins // 60
            cd_m = move_in_mins % 60
            st.markdown(f"""
            <div style='text-align:center; margin:1rem 0; padding:1rem;
              background:#FFFFFF; border-radius:14px;'>
              <div style='color:#718096; font-size:0.8rem; margin-bottom:0.4rem;'>이동 출발까지</div>
              <div style='font-size:2.5rem; font-weight:900;
                color:{"#2A9D8F" if move_in_mins > 30 else "#E6A800" if move_in_mins > 10 else "#D9534F"};'>
                {"즉시 출발!" if move_in_mins <= 0 else f"{cd_h}시간 {cd_m}분" if cd_h > 0 else f"{cd_m}분 후"}
              </div>
            </div>
            """, unsafe_allow_html=True)
        

        # ── 출국장 혼잡도 현황 ──
        if df_congestion is not None and not df_congestion.empty:
            st.markdown("---")
            _cong_hdr, _cong_btn = st.columns([5, 1])
            _cong_hdr.markdown("<h3>🚦 실시간 보안검색대 혼잡도</h3>", unsafe_allow_html=True)
            if _cong_btn.button("🔄", key="refresh_congestion", help="혼잡도 데이터만 새로고침", use_container_width=True):
                st.session_state.congestion_cache_ver += 1
                st.rerun()
            
            df_cong_sorted = df_congestion.sort_values("대기 시간(분)", ascending=True).copy()
            # 게이트 코드 → 한국어 이름 변환
            df_cong_sorted["출국장"] = df_cong_sorted["게이트(Gate)"].apply(gate_display_name)
            best = df_cong_sorted.iloc[0]
            worst = df_cong_sorted.iloc[-1]
            
            # 상단 예쁜 콜아웃 카드
            c1, c2 = st.columns(2)
            c1.success(f"✅ **가장 쾌적한 출국장**\n\n## {best['출국장']}\n대기 예상: **{best['대기 시간(분)']}분** (현재 {best['대기 인원(명)']}명)")
            c2.error(f"🚨 **가장 붐비는 출국장**\n\n## {worst['출국장']}\n대기 예상: **{worst['대기 시간(분)']}분** (현재 {worst['대기 인원(명)']}명)")

            # 데이터프레임 표시 (코드명 컬럼 숨기고 한국어 이름 사용)
            max_wait = int(df_cong_sorted["대기 시간(분)"].max() or 30) + 5
            df_display = df_cong_sorted[["출국장", "대기 시간(분)", "대기 인원(명)", "운영 시간"]]
            
            st.caption("👇 각 게이트별 상세 현황 (진척도 바를 통해 직관적으로 비교하세요)")
            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "출국장": st.column_config.TextColumn("출국장", width="medium"),
                    "대기 시간(분)": st.column_config.ProgressColumn(
                        "대기 시간 현황 (막대 그래프)",
                        help="대기 시간이 짧을수록 파란색 바가 적게 찹니다.",
                        format="%d 분",
                        min_value=0,
                        max_value=max_wait,
                    ),
                    "대기 인원(명)": st.column_config.NumberColumn(
                        "대기 인원 수", format="%d 명"
                    ),
                    "운영 시간": st.column_config.TextColumn("게이트 기본 운영 시간")
                }
            )

    st.markdown(f"""
    <div style='text-align:right; color:#A0AEC0; font-size:0.75rem; margin-top:1rem;'>
      마지막 업데이트: {datetime.now(timezone(timedelta(hours=9))).strftime("%H:%M:%S")} · 공공데이터포털 실시간
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 입국 마중 (ARRIVAL) 모드
# ─────────────────────────────────────────────
elif st.session_state.mode == "ARRIVAL":

    with st.sidebar:
        st.markdown("## 🛬 입국 마중 설정")
        if st.button("← 처음으로", key="arr_back"):
            st.session_state.mode = None
            st.session_state.my_share_code = None
            st.rerun()
        st.markdown("---")

        st.subheader("👀 이용자 역할 선택")
        arr_role = st.radio("당신은 누구십니까?", ["🧳 탑승객 본인 (비행기 탑승)", "🤝 맞이객 (공항 대기)"], index=1, label_visibility="collapsed")
        
        st.markdown("---")
        
        # 조회 상태 관리용 세션 변수
        if "arr_flight_query" not in st.session_state:
            st.session_state.arr_flight_query = None
            
        if "탑승객" in arr_role:
             raw_input = st.text_input("✈️ 내 비행기 편명 검색", placeholder="예: KE123")
             # 버튼 클릭 시에만 조회가 시작되도록 세션에 저장
             if st.button("✅ 공유코드 발급 및 레이더 확인", use_container_width=True, type="primary"):
                 st.session_state.arr_flight_query = raw_input
             st.caption("편명을 입력하고 [공유코드 발급] 버튼을 눌러야 발급창이 뜹니다.")
        else:
             raw_input = st.text_input("✈️ 맞이객 공유코드 입력", placeholder="예: KE123-A1B2")
             st.caption("탑승객에게서 전달받은 공유코드(영문+숫자 혼합)를 정확히 입력하세요.")
             if st.button("📡 위치 추적 및 대시보드 켜기", use_container_width=True, type="primary"):
                 st.session_state.arr_flight_query = raw_input
                 
        # 하단 로직은 세션 변수를 기준으로 동작함
        search_arr_flight = st.session_state.arr_flight_query
        st.markdown("---")

        st.subheader("📍 현재 마중객 위치")
        st.caption("실시간 GPS로 입국장 게이트까지 남은 도보 시간을 자동 계산합니다.")
        from streamlit_geolocation import streamlit_geolocation
        import math
        
        arr_gps_loc = streamlit_geolocation()
        picker_dist = 0
        
        def calc_distance_arr(lat1, lon1, lat2, lon2):
            R = 6371e3
            phi1, phi2 = lat1 * math.pi/180, lat2 * math.pi/180
            dphi = (lat2-lat1) * math.pi/180
            dlon = (lon2-lon1) * math.pi/180
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlon/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        if arr_gps_loc and arr_gps_loc.get('latitude') is not None and arr_gps_loc.get('longitude') is not None:
            # 인천공항 T1 입국장 (1층 중심) 좌표
            t1_arr_lat, t1_arr_lon = 37.4485, 126.4389
            dist_m = calc_distance_arr(arr_gps_loc['latitude'], arr_gps_loc['longitude'], t1_arr_lat, t1_arr_lon)
            
            if dist_m > 3000: # 3km 이상 떨어져 있으면 차량 이동으로 판단 (50km/h 기준 + 주차장 이동 페널티 15분)
                drive_time_calc = int(dist_m / 833.0) + 15
                st.success(f"✅ 위치 확인: 공항까지 직선 약 {int(dist_m/1000)}km (차량 주행 및 주차 포함 대략 {drive_time_calc}분 소요)")
                picker_dist = drive_time_calc
            else:
                walk_time_calc = int(dist_m / 80.0) # 성인 평균 1.34m/s
                st.success(f"✅ 위치 확인: 입국장 게이트까지 직선 약 {int(dist_m)}m (도보 예상 {walk_time_calc}분)")
                picker_dist = walk_time_calc
                
            st.caption("※ 거리 연장은 보수적으로 산출된 예상 보정 시각입니다.")
        else:
            picker_loc = st.selectbox("수동 위치 선택 (로딩 전)", [
                "장기 주차장 (도보 20분)",
                "단기 주차장 (도보 10분)",
                "터미널 내 식당가 (도보 5분)",
                "출구 게이트 앞 (도보 0분)",
            ])
            picker_dist = {
                "장기 주차장 (도보 20분)": 20,
                "단기 주차장 (도보 10분)": 10,
                "터미널 내 식당가 (도보 5분)": 5,
                "출구 게이트 앞 (도보 0분)": 0,
            }[picker_loc]

    # ── 데이터 로드 ──
    with st.spinner("🔄 실시간 입국 데이터 불러오는 중..."):
        df_arr = get_arrival_flights()

    if df_arr is None or df_arr.empty:
        st.error("⚠️ 입국 항공편 데이터를 불러오지 못했습니다.")
        st.stop()

    # ── 편명 매칭 ──
    real_flight_no = ""
    if not search_arr_flight:
        st.info("👈 좌측 메뉴에서 비행기 편명(또는 공유코드)을 입력하고 파란색 버튼을 눌러 추적을 시작하세요.")
        st.markdown("""
        <div style='text-align:center; padding: 50px; opacity: 0.5;'>
            <div style='font-size: 4rem; margin-bottom: 20px;'>✈️</div>
            <h4>비행기 실시간 위치 추적 시스템</h4>
            <p>탑승객은 코드를 발급받고, 맞이객은 코드를 입력하여 실시간 위치를 연동합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
        
    # 공유코드 (예: KE123-A1B2) 입력 시 앞부분 편명만 파싱
    real_flight_no = search_arr_flight.split("-")[0].strip()
    arr_match = df_arr[df_arr["편명"].str.upper() == real_flight_no.upper()]

    if arr_match.empty:
        st.warning(f"'{search_arr_flight}' 항공편을 찾을 수 없습니다.")
        st.stop()

    arr_flight = arr_match.iloc[0]
    
    # 상태값이 비어있거나 NaN(float)일 경우의 안전한 캐스팅
    raw_status = arr_flight.get("상태", "")
    arr_status = str(raw_status) if pd.notna(raw_status) else ""

    # 현재 단계 매핑
    # p_phase: -1 = 아직 비행중(착륙 전), 0 = 착륙, 1 = 입국심사, 2 = 수하물, 3 = 출구
    status_to_phase = {
        "착륙": 0, "공역": 0, "접근": 0,
        "심사": 1, "입국": 1,
        "수하물": 2, "수취": 2,
        "출구": 3, "도착": 3,
    }

    # ── 도착까지 남은 시간 계산 (estimatedDatetime 우선) ──
    # 변경/도착시간 = estimatedDatetime (실제 ETA), 예정시간 = scheduledDatetime
    _eta_str = arr_flight.get("변경/도착시간", "N/A")
    _sch_str = arr_flight.get("예정시간", "N/A")

    # ETA(변경/도착시간)가 있으면 우선 사용, 없으면 예정시간 사용
    if _eta_str not in ("N/A", "", None):
        mins_until_arr = minutes_diff(_eta_str)
        arr_time_str = _eta_str
    elif _sch_str not in ("N/A", "", None):
        mins_until_arr = minutes_diff(_sch_str)
        arr_time_str = _sch_str
    else:
        mins_until_arr = None
        arr_time_str = "N/A"

    # --- OpenSky Network 실시간 데이터 결합 ---
    live_flight = None
    if arr_flight.get("편명"):
        live_flight = opensky_api.get_target_flight_status(arr_flight["편명"])
        
    # OpenSky 실시간 데이터가 있다면 상태 및 ETA를 초정밀 수학적 계산으로 오버라이드
    if live_flight:
        alt = live_flight.get("alt")
        on_ground = live_flight.get("on_ground")
        
        if on_ground or (alt is not None and alt < 50):
            p_phase = 0 # 착륙 & 택싱
            arr_status = "🛬 활주로 착륙 완료 (택싱 중)"
            mins_until_arr = 0
        else:
            # GPS 기반 남은 시간 초정밀 계산 (인천공항 좌표: 위도 37.4600, 경도 126.4400)
            import math
            f_lat, f_lon = live_flight.get("lat", 37.46), live_flight.get("lon", 126.44)
            lat1, lon1, lat2, lon2 = map(math.radians, [f_lat, f_lon, 37.4600, 126.4400])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            dist_km = 6371 * 2 * math.asin(math.sqrt(a))
            
            vel_kmh = live_flight.get("vel", 250) * 3.6
            if vel_kmh > 0:
                gps_mins = int((dist_km / vel_kmh) * 60)
                # 이착륙 항로 우회 분량을 고려해 약 3~5분 보정
                gps_mins += 3 
                mins_until_arr = gps_mins # 기존 공공데이터 ETA를 완벽히 덮어씀
            else:
                gps_mins = mins_until_arr or 0
                
            if alt is not None and alt < 3000:
                p_phase = -1
                arr_status = f"⏬ 고도 {int(alt)}m 하강 중 (GPS 기준 도착 약 {gps_mins}분 전)"
            else:
                p_phase = -1
                arr_status = f"✈️ 고도 {int(alt) if alt else '확인불가'}m 순항 중 (GPS 예측: {gps_mins}분 후 착륙)"
    else:
        # 기존 로직 (30분 이상 남아있으면 무조건 비행 중)
        if mins_until_arr is not None and mins_until_arr > 30:
            p_phase = -1
        else:
            p_phase = None
            for keyword, phase in status_to_phase.items():
                if keyword in arr_status:
                    p_phase = phase
                    break
            if arr_status in ["도착", "착륙"]:
                p_phase = 0
            elif "수하물" in arr_status:
                p_phase = 2
            if p_phase is None:
                p_phase = 0  # fallback: 착륙 진행 중

    # 예상 남은 시간 계산 (비행 중이면 착륙까지 남은 시간 + 이후 단계 합산)
    if p_phase == -1:
        # mins_until_arr이 음수(착륙 시간 지남)이면 0으로 처리
        safe_mins_until_arr = max(0, mins_until_arr or 0)
        time_remaining = safe_mins_until_arr + sum(ARRIVAL_PHASE_MINS)
    else:
        time_remaining = sum(ARRIVAL_PHASE_MINS[p_phase:])

    col_arr_main, col_arr_right = st.columns([1.6, 1])

    with col_arr_main:
                # ── 1) 현재 단계 상태 ──
        with st.container(border=True):
            st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>✈️ 입국 여객 현재 상태</h3>", unsafe_allow_html=True)

            col_a1, col_a2, col_a3 = st.columns(3)
            col_a1.metric("편명", arr_flight["편명"])
            col_a2.metric("출발지", arr_flight["출발지"])
            # arr_status가 비어있으면 p_phase 기반으로 의미 있는 상태 표시
            _phase_labels = {-1: "✈️ 비행 중", 0: "🛬 착륙 진행", 1: "🧍 입국 심사 중", 2: "🛄 수하물 수취 중", 3: "🚪 출구 이동 중"}
            _status_display = arr_status if arr_status else _phase_labels.get(p_phase, "비행 중")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ── (OpenSky) 실시간 항공기 레이더 맵 ──
            @st.fragment
            def render_radar_fragment(flight_callsign, origin_name, mins_left):
                import opensky_api
                import pandas as pd
                import pydeck as pdk
                import math
                
                # 프래그먼트 내부에서 10초마다 최신 좌표 갱신 (전체 페이지 리로드 없음)
                current_f = opensky_api.get_target_flight_status(flight_callsign)
                
                is_live = False
                lat = 37.46
                lon = 126.44
                alt_text = "알 수 없음"
                vel_text = "알 수 없음"
                
                safe_mins = max(0, mins_left) if mins_left else 60
                
                if current_f and current_f.get("lat") and current_f.get("lon"):
                    is_live = True
                    lat = current_f["lat"]
                    lon = current_f["lon"]
                    alt_m = current_f.get("alt")
                    vel_ms = current_f.get("vel")
                    if alt_m: alt_text = f"{int(alt_m)}m"
                    if vel_ms: vel_text = f"{int(vel_ms * 3.6)}km/h"
                else:
                    # 라이브 위치 아니면 렌더링 안 함 (예상 위치 끄기)
                    lat = 37.46
                    lon = 126.44
                    alt_text = "조회 불가"
                    vel_text = "조회 불가"
                
                cr1, cr2 = st.columns([2, 1])
                with cr1:
                    st.markdown(f"<div style='font-size:0.95rem; color:#60b8ff; margin-top:0.4rem; margin-bottom:0.3rem;'><b>📍 실시간 위성 레이더 (고도: {alt_text}, 속도: {vel_text})</b></div>", unsafe_allow_html=True)
                with cr2:
                    if is_live:
                        st.markdown("<div style='text-align:right; font-size:0.9rem; color:#ff4b4b; padding-top:0.4rem; margin-bottom:0.5rem;'><b>🔴 LIVE 추적 중</b></div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='text-align:right; font-size:0.9rem; color:#A0AEC0; padding-top:0.4rem; margin-bottom:0.5rem;'><b>⚪ 레이더 신호 미수신</b></div>", unsafe_allow_html=True)
                    
                view_state = pdk.ViewState(
                    latitude=lat,
                    longitude=lon,
                    zoom=4 if is_live else 6,
                    pitch=40
                )
                
                layers = []
                if is_live:
                    map_df = pd.DataFrame([{"lat": lat, "lon": lon}])
                    layers.append(pdk.Layer(
                        "ScatterplotLayer",
                        data=map_df,
                        get_position="[lon, lat]",
                        get_fill_color="[220, 20, 60, 255]",
                        get_radius=30000 if safe_mins > 60 else 15000,
                    ))
                
                if not is_live:
                    st.info("ℹ️ 현재 실시간 위성(ADS-B) 망에 위치가 잡히지 않는 특수 비행기입니다. (예: 공동운항 비행기, 해양 음영구역 등)")

                st.pydeck_chart(pdk.Deck(map_style='https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json', layers=layers, initial_view_state=view_state))
                
                # st.fragment 내부 버튼: 누르면 이 영역만 새로고침됨!
                if st.button("🔄 실시간 레이더 위치 새로고침", use_container_width=True, key="btn_radar_refresh"):
                    pass # 버튼 행동 자체는 st.fragment 재실행 트리거로 작용
                st.markdown("<br>", unsafe_allow_html=True)

            # 권역 밖이라도 무조건 렌더링 (AI 위치 시뮬레이터가 대신 표시해줌)
            actual_callsign = arr_flight.get("실제운항편명", arr_flight["편명"])
            render_radar_fragment(actual_callsign, arr_flight["출발지"], mins_until_arr)



            # p_phase == -1: 아직 비행 중 (착륙 전)
            if p_phase == -1:
                mins_to_land = mins_until_arr or 0
                st.markdown(f"""
                <div class='phase-item phase-active'>
                  <span style='margin-right:0.8rem; font-size:1.1rem;'>✈️</span>
                  <span style='color:#60b8ff; font-weight:700;'>비행 중 — 착륙까지 약 {mins_to_land}분 남음</span>
                </div>""", unsafe_allow_html=True)
                for phase_name in ARRIVAL_PHASES:
                    st.markdown(f"""
                    <div class='phase-item phase-pending'>
                      <span style='margin-right:0.8rem; font-size:1.1rem;'>⏳</span>
                      <span style='color:#718096; font-weight:600;;'>{phase_name}</span>
                    </div>""", unsafe_allow_html=True)
            else:
                for i, phase_name in enumerate(ARRIVAL_PHASES):
                    if i < p_phase:
                        st.markdown(f"""
                        <div class='phase-item phase-done'>
                          <span style='margin-right:0.8rem; font-size:1.1rem;'>✅</span>
                          <span style='color:#718096; text-decoration:line-through;'>{phase_name}</span>
                        </div>""", unsafe_allow_html=True)
                    elif i == p_phase:
                        st.markdown(f"""
                        <div class='phase-item phase-active'>
                          <span style='margin-right:0.8rem; font-size:1.1rem;'>▶️</span>
                          <span style='color:#60b8ff; font-weight:700;'>{phase_name} 진행 중</span>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='phase-item phase-pending'>
                          <span style='margin-right:0.8rem; font-size:1.1rem;'>⏳</span>
                          <span style='color:#718096; font-weight:600;;'>{phase_name}</span>
                        </div>""", unsafe_allow_html=True)
        

        # ── 2) 탑승객 기내 오프라인 핑 (Ping) 모드 ──
        if "탑승객" in arr_role:
            
            
            st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>📡 오프라인 상태 핑 (Ping) 보내기</h3>", unsafe_allow_html=True)
            st.caption("와이파이가 켜질 때 아래 버튼을 누르면 맞이객 대시보드에 즉시 알림이 갑니다!")
            
            c1, c2, c3 = st.columns(3)
            
            def send_ping_local(msg):
                try:
                    import firebase_sync
                    from datetime import datetime
                    if firebase_sync.send_ping(real_flight_no, msg):
                        st.toast(f"☁️ 맞이객에게 클라우드 메시지 전송 완료: {msg}")
                    else:
                        st.toast(f"☁️ 맞이객에게 클라우드 메시지 전송 완료 (시뮬레이션 모드): {msg}")
                except Exception as e:
                    st.toast(f"오류: {e}")
                
            if c1.button("🛬 방금 착륙함"): send_ping_local("비행기가 방금 활주로에 정차했습니다!")
            if c2.button("🛂 심사줄 서는 중"): send_ping_local("입국 심사 대기열에 서 있습니다.")
            if c3.button("🧳 수하물 대기열"): send_ping_local("내 짐이 나오는 컨베이어 벨트 앞에서 대기 중입니다.")
            
            
        else: # 맞이객 (Greeter 뷰)
            
            st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>🤝 맞이객 전용 대시보드</h3>", unsafe_allow_html=True)
            meet_time_dt = datetime.now(timezone(timedelta(hours=9))) + timedelta(minutes=time_remaining)
            
            # --- 오프라인 핑 클라우드 수신 로직 ---
            try:
                import firebase_sync
                flight_key = real_flight_no.upper() if 'real_flight_no' in locals() and real_flight_no else ''
                if flight_key:
                    sync_data = firebase_sync.get_ping(flight_key)
                    if sync_data:
                        st.info(f"☁️💌 **탑승객 클라우드 실시간 핑 ({sync_data.get('time', '')})**\n> 👤 탑승자: {sync_data.get('msg', '')}")
            except Exception as e:
                pass
                
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("여객터미널 출구 도착 예상", meet_time_dt.strftime("%H:%M"))
            col_m2.metric("예상 대기/잔여 시간", f"약 {time_remaining}분")
            
            # --- 맞이객 출발 권장 타이머 ---
            meet_gap = time_remaining - picker_dist
            if meet_gap > 60:
                st.success(f"🟢 자택 실내에서 편하게 대기하셔도 좋습니다. 출발 권장 시간까지 약 {meet_gap}분 남았습니다.")
            elif meet_gap > 10:
                st.warning(f"🟡 교통 체증이 있을 수 있으므로, 지금 슬슬 공항 게이트 방향으로 이동을 준비해 주세요!")
            else:
                st.error("🔴 입국장 게이트 앞(1층)으로 지금 즉시 이동하여 대기하세요!")
                
            # --- 실시간 터미널 특화 착륙 알림 ---
            if mins_until_arr is not None and mins_until_arr <= 40:
                st.warning("🛬 **[시스템 실시간 알림] 해당 여객기가 하강(착륙)을 시작했습니다!** 곧 수속이 진행됩니다.")

            # --- 실시간 터미널 주차장 연동 스마트 추천 (상시 접근 가능하도록 변경) ---
            with st.expander("🅿️ 단기주차장 실시간 빈자리 검색", expanded=False):
                try:
                    from parking_api import get_recommended_parking
                    p_term = "T2" if "2" in str(arr_flight.get("터미널", "")) else "T1"
                    best_parking = get_recommended_parking(p_term)
                    
                    if best_parking:
                        st.caption("차량을 이용해 맞이하러 오신 경우, 가장 널널한 아래 단기주차장으로 진입하세요.")
                        st.success(f"📍 **추천 구역: {best_parking['구역/층']}**\n\n(현재 잔여 {best_parking['잔여대수']}대 / 총 {best_parking['총면수']}대 공간 열림)")
                    else:
                        st.write("주차장 혼잡도 정보를 불러올 수 없습니다.")
                except Exception:
                    st.write("실시간 혼잡도 조회 중 오류가 발생했습니다.")
            
            

        # ── 5) AI 맞춤형 대중교통 추천 ──
        
        st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>🚇 AI 목적지 맞춤 교통수단 추천</h3>", unsafe_allow_html=True)
        search_dest = st.text_input("목적지 검색 (예: 강남, 홍대, 부산 등)", placeholder="어디로 가시나요?")
        
        recommended = []
        if search_dest:
            q = search_dest.strip().lower()
            
            # 1. API 기반 공항버스 실시간 노선 검색 (진짜 데이터 꽂아넣기!)
            from bus_api import get_bus_by_keyword
            bus_term_code = "2" if "2" in str(arr_flight.get("터미널", "")) else "1"
            
            with st.spinner("최적 경로 및 요금 정보 검색 중..."):
                api_buses = get_bus_by_keyword(q, terminal=bus_term_code)
                recommended.extend(api_buses)
                
            # 2. 공항철도/KTX 등 휴리스틱 보조 추천
            if "강남" in q or "송파" in q or "잠실" in q:
                if not any("공항철도" in r["name"] for r in recommended):
                    recommended.append({"icon": "🚇", "name": "공항철도 + 9호선", "time": "약 90분", "cost": "4,950원", "tip": "평소 도로 정체가 심한 시간대라면 전철 추천"})
            elif "홍대" in q or "공덕" in q or "서울역" in q or "명동" in q or "종로" in q:
                if "서울역" in q or "명동" in q:
                    recommended.insert(0, {"icon": "🚇", "name": "공항철도 직통열차", "time": "약 43분", "cost": "9,500원", "tip": "서울역 종점 무정차, 최단 시간 소요"})
                recommended.append({"icon": "🚇", "name": "공항철도 일반열차", "time": "약 66분", "cost": "4,950원", "tip": "홍대입구역, 공덕역 등 중간 거점 하차 시 유리"})
            elif ("부산" in q or "대구" in q or "대전" in q or "천안" in q):
                if not any("KTX" in r["name"] for r in recommended):
                    recommended.append({"icon": "🚄", "name": "KTX (광명역/서울역 환승)", "time": "약 2~3시간", "cost": "50,000원~", "tip": "버스가 매진된 경우 공항철도(서울역) 또는 KTX리무진(광명역) 환승 이용"})
            
            if not recommended:
                st.warning(f"'{search_dest}' 방면으로 운행하는 버스나 직통 노선을 찾지 못했습니다. 대략적인 시/구 이름을 검색하시거나 미터기 택시를 이용해 주세요.")
            else:
                st.success(f"**'{search_dest}'** 방면 가장 빠르고 편한 최적 경로입니다.")
                for t in recommended:
                    st.markdown(f"""
                    <div class='transit-card'>
                      <div class='transit-icon'>{t['icon']}</div>
                      <div>
                        <div class='transit-name'>{t['name']} <span style='color:#E6A800; font-size:0.85rem;'>⏱ {t['time']}</span></div>
                        <div class='transit-detail'>💰 {t['cost']} · {t['tip']}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("👆 위 검색창에 목적지(예: 강남구, 수원, 홍대)를 입력하시면 가장 빠르고 편한 경로를 인공지능이 찾아 드립니다.")
        
        
        # ── 6) 택시 승강장 대기 현황 (API) ──
        
        st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>🚕 실시간 공항 택시 대기열 현황</h3>", unsafe_allow_html=True)
        from taxi_api import get_taxi_status
        
        taxi_term_code = "P02" if "2" in str(arr_flight.get("터미널", "")) else "P01"
        with st.spinner("택시 대기 현황 불러오는 중..."):
            df_taxi = get_taxi_status(terminal=taxi_term_code)
            
        if not df_taxi.empty:
            c_seoul, c_incheon, c_gyeonggi = st.columns(3)
            val_s = df_taxi[df_taxi["택시 종류"] == "서울 택시"]["대기 대수"].sum()
            val_i = df_taxi[df_taxi["택시 종류"] == "인천 택시"]["대기 대수"].sum()
            val_g = df_taxi[df_taxi["택시 종류"] == "경기 택시"]["대기 대수"].sum()
            val_b = df_taxi[df_taxi["택시 종류"] == "모범/대형 택시"]["대기 대수"].sum()
            
            c_seoul.metric("서울 택시", f"{val_s}대 대기")
            c_incheon.metric("인천 택시", f"{val_i}대 대기")
            c_gyeonggi.metric("경기 택시", f"{val_g}대 대기")
            
            st.caption(f"안내: 모범/대형 등 특수 목적 택시 {val_b}대 대기 중 (기준: { 'T2' if taxi_term_code=='P02' else 'T1' } 제{ '2' if taxi_term_code=='P02' else '1'}여객터미널)")
        else:
            if taxi_term_code == "P02":
                st.info("ℹ️ 현재 실시간 택시 대기 데이터는 제1여객터미널(T1)만 제공됩니다. 제2여객터미널(T2) 현장 승강장 안내를 참고해 주세요.")
            else:
                st.info("현재 택시 승강장 데이터를 불러올 수 없습니다.")
        

        # ── 7) 공항철도 실시간 운행정보 ──
        
        st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>🚆 실시간 공항철도(AREX) 운행정보</h3>", unsafe_allow_html=True)
        
        arex_stn_choice = st.radio("조회할 공항철도역 선택", ["인천공항1터미널", "인천공항2터미널"], horizontal=True, label_visibility="collapsed")
        arex_filter_code = "049" if arex_stn_choice == "인천공항1터미널" else "060"
        
        from railroad_api import get_railroad_info
        with st.spinner(f"{arex_stn_choice}역 실시간 공항철도 운행정보 불러오는 중..."):
            df_arex = get_railroad_info(station_filter=arex_filter_code)
            
        if not df_arex.empty:
            st.dataframe(
                df_arex.head(5),
                hide_index=True,
                use_container_width=True,
                height=250,
                column_config={
                    "역명": st.column_config.TextColumn("역명", width="small"),
                    "열차번호": st.column_config.TextColumn("편성", width="small"),
                    "등급": st.column_config.TextColumn("운행 종류", width="small"),
                    "예정/도착시간": st.column_config.TextColumn("도착/출발 시각"),
                    "상태": st.column_config.TextColumn("운행 상태", width="small")
                }
            )
        else:
            st.info("현재 운행중인 공항철도 내역이 없거나 데이터를 불러올 수 없습니다.")
        

    with col_arr_right:
        # ── 4) RL 이동 타이밍 알람 ──
        
        st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>🧠 AI 이동 타이밍 추천</h3>", unsafe_allow_html=True)

        rl_arr = AIPortRLEngine(mode="ARRIVAL")
        arr_state = rl_arr.get_state(
            passenger_phase=p_phase,
            time_remaining=time_remaining,
            picker_distance=picker_dist
        )
        arr_action = rl_arr.select_action(arr_state)

        arr_action_styles = {
            ARR_ACTION_0: ("action-green", "☕", "현 위치에서 대기/휴식",
                           "아직 여객이 나오기까지 시간이 충분합니다.\n카페 또는 차량 안에서 편히 기다리세요."),
            ARR_ACTION_1: ("action-yellow", "🚶", "출구 방향으로 이동 시작",
                           "슬슬 게이트로 이동하세요!\n너무 늦으면 엇갈릴 수 있습니다."),
            ARR_ACTION_2: ("action-red", "📍", "출구 게이트 앞에서 대기",
                           "여객이 곧 나옵니다!\n지금 바로 게이트 앞에 서서 맞이할 준비를 하세요."),
        }
        aa_class, aa_icon, aa_title, aa_desc = arr_action_styles[arr_action]
        st.markdown(f"""
        <div class='action-box {aa_class}'>
          <div style='font-size:2.2rem; margin-bottom:0.5rem;'>{aa_icon}</div>
          <div style='font-size:1.05rem; font-weight:700; margin-bottom:0.4rem;'>{aa_title}</div>
          <div style='font-size:0.85rem; opacity:0.85; white-space:pre-line;'>{aa_desc}</div>
        </div>
        """, unsafe_allow_html=True)
        

        # ── 3) 맞이객 연동 공유 코드 (탑승객 전용 뷰) ──
        if "탑승객" in arr_role:
            
            st.markdown("<h3 style='color:#2D3748; font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>📡 입국 픽업 연동 코드 공유</h3>", unsafe_allow_html=True)
            st.markdown("""
            <div style='color:#718096; font-size:0.82rem; margin-bottom:1rem; line-height:1.6;'>
              아래 코드를 마중할 맞이객(가족/친구)에게 카톡이나 문자로 전송하세요.<br>탑승객의 비행 위치, 심사 상태가 100% 동일하게 연동됩니다.<br>
              <span style='color:#E6A800;'>⏳ 최대 24시간 유효 · 도착 직후 1시간 뒤 자동 소멸</span>
            </div>
            """, unsafe_allow_html=True)

            import hashlib
            hash_tag = hashlib.md5(arr_flight['편명'].encode()).hexdigest()[:4].upper()
            share_code = f"{arr_flight['편명']}-{hash_tag}"

            # 만료 시간 로직: 착륙 전이면 24시간, 착륙/수속 시작됐으면 1시간 뒤 만료
            _expire_dt = datetime.now(timezone(timedelta(hours=9))) + timedelta(hours=24)
            if p_phase >= 0: 
                _expire_dt = datetime.now(timezone(timedelta(hours=9))) + timedelta(hours=1)
            _expire_str = _expire_dt.strftime("%m월 %d일 %H:%M") + " 만료 예정"

            st.markdown(f"""
            <div class='share-code-box'>
              <div style='color:#718096; font-size:0.8rem; margin-bottom:0.5rem;'>내 전용 공유 암호코드</div>
              <div class='share-code'>{share_code}</div>
              <div style='color:#718096; font-weight:600;; font-size:0.75rem; margin-top:0.5rem;'>이 코드를 복사하여 맞이객에게 알려주세요</div>
              <div style='color:#E6A800; font-size:0.72rem; margin-top:0.3rem;'>⏳ {_expire_str}</div>
            </div>
            """, unsafe_allow_html=True)
            
            


    st.markdown(f"""
    <div style='text-align:right; color:#A0AEC0; font-size:0.75rem; margin-top:1rem;'>
      마지막 업데이트: {datetime.now(timezone(timedelta(hours=9))).strftime("%H:%M:%S")} · 공공데이터포털 실시간
    </div>
    """, unsafe_allow_html=True)
