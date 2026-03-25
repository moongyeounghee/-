import streamlit as st
import pandas as pd
import time
import random
import string
from datetime import datetime, timedelta

from departure_congestion_api import get_departure_congestion
from departure_flight_api import get_departure_flights
from arrival_flight_api import get_arrival_flights
from rl_engine import (
    AIPortRLEngine,
    DEP_ACTION_0, DEP_ACTION_1, DEP_ACTION_2, DEP_ACTION_3,
    ARR_ACTION_0, ARR_ACTION_1, ARR_ACTION_2,
    ACTION_NAMES
)

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
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Inter:wght@300;400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Inter', sans-serif;
}

/* 배경 */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 50%, #0a1628 100%);
    min-height: 100vh;
}

/* 히어로 헤더 */
.hero-header {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    background: linear-gradient(180deg, rgba(0,150,255,0.08) 0%, transparent 100%);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2rem;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(135deg, #60b8ff, #c084fc, #67e8f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.4rem;
    letter-spacing: -1px;
}
.hero-sub {
    color: rgba(255,255,255,0.5);
    font-size: 1rem;
    font-weight: 300;
}

/* 모드 선택 카드 */
.mode-card {
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    margin: 0.5rem;
}
.mode-dep {
    background: linear-gradient(135deg, rgba(96,184,255,0.12), rgba(100,110,255,0.12));
    border-color: rgba(96,184,255,0.3);
}
.mode-dep:hover { border-color: #60b8ff; box-shadow: 0 8px 40px rgba(96,184,255,0.2); }
.mode-arr {
    background: linear-gradient(135deg, rgba(103,232,249,0.12), rgba(192,132,252,0.12));
    border-color: rgba(103,232,249,0.3);
}
.mode-arr:hover { border-color: #67e8f9; box-shadow: 0 8px 40px rgba(103,232,249,0.2); }
.mode-emoji { font-size: 4rem; margin-bottom: 1rem; }
.mode-title { font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
.mode-desc { font-size: 0.9rem; color: rgba(255,255,255,0.6); line-height: 1.6; }

/* 정보 카드 */
.info-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.info-card h4 { color: #60b8ff; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem; }

/* 상태 배지 */
.badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 0.2rem;
}
.badge-green { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.badge-yellow { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-red { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }
.badge-blue { background: rgba(96,184,255,0.15); color: #60b8ff; border: 1px solid rgba(96,184,255,0.3); }

/* 게이지 바 */
.gauge-wrap { background: rgba(255,255,255,0.08); border-radius: 8px; height: 12px; overflow: hidden; margin: 0.5rem 0; }
.gauge-bar { height: 100%; border-radius: 8px; transition: width 0.5s ease; }
.gauge-green { background: linear-gradient(90deg, #34d399, #059669); }
.gauge-yellow { background: linear-gradient(90deg, #fbbf24, #d97706); }
.gauge-red { background: linear-gradient(90deg, #f87171, #dc2626); animation: pulse-red 1s ease-in-out infinite; }
@keyframes pulse-red { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }

/* 단계 진행 바 */
.phase-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    margin-bottom: 0.5rem;
    border: 1px solid rgba(255,255,255,0.06);
}
.phase-active { background: rgba(96,184,255,0.12); border-color: rgba(96,184,255,0.4); }
.phase-done { background: rgba(52,211,153,0.08); border-color: rgba(52,211,153,0.2); }
.phase-pending { background: rgba(255,255,255,0.02); }

/* 액션 박스 */
.action-box {
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 1px solid;
}
.action-green { background: rgba(52,211,153,0.08); border-color: rgba(52,211,153,0.3); color: #34d399; }
.action-yellow { background: rgba(251,191,36,0.08); border-color: rgba(251,191,36,0.3); color: #fbbf24; }
.action-red { background: rgba(248,113,113,0.08); border-color: rgba(248,113,113,0.3); color: #f87171; }

/* 공유코드 박스 */
.share-code-box {
    background: linear-gradient(135deg, rgba(192,132,252,0.12), rgba(96,184,255,0.12));
    border: 2px dashed rgba(192,132,252,0.5);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin: 1rem 0;
}
.share-code {
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: 0.5rem;
    background: linear-gradient(135deg, #c084fc, #60b8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* 대중교통 카드 */
.transit-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.transit-icon { font-size: 2rem; }
.transit-name { font-weight: 700; color: #fff; font-size: 0.95rem; }
.transit-detail { color: rgba(255,255,255,0.55); font-size: 0.85rem; }

/* 사이드바 */
.css-1d391kg, [data-testid="stSidebar"] {
    background: rgba(10,14,26,0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* 공통 메트릭 */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1rem 1.2rem;
}

/* 버튼 */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
}

/* 섹션 구분선 */
.section-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 1.5rem 0;
}

/* 입력 필드 */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.92) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 10px !important;
    color: #111 !important;
}
.stTextInput > div > div > input::placeholder {
    color: #888 !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #fff !important;
}

div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


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

# ─────────────────────────────────────────────
# 접속 코드 게이트 (비공개 접근 제어)
# ─────────────────────────────────────────────
ACCESS_CODE = "AIPORT2026"  # ← 접속 코드 (변경 가능)

if not st.session_state.access_granted:
    st.markdown("""
    <div style='max-width:420px; margin:8vh auto; padding:3rem 2.5rem;
      background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);
      border-radius:24px; text-align:center;'>
      <div style='font-size:3rem; margin-bottom:1rem;'>🔐</div>
      <div style='font-size:1.4rem; font-weight:800; color:#fff; margin-bottom:0.4rem;'>AI-PORT 접속 코드</div>
      <div style='color:rgba(255,255,255,0.45); font-size:0.9rem; margin-bottom:2rem;'>
        초대받은 사용자만 이용할 수 있습니다.<br>접속 코드를 입력해주세요.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2, col_g3 = st.columns([1, 1.5, 1])
    with col_g2:
        pw_input = st.text_input("접속 코드", type="password", placeholder="접속 코드 입력",
                                 label_visibility="collapsed")
        if st.button("입장하기 →", use_container_width=True, type="primary"):
            if pw_input.strip().upper() == ACCESS_CODE:
                st.session_state.access_granted = True
                st.rerun()
            else:
                st.error("❌ 접속 코드가 올바르지 않습니다.")
    st.stop()


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
    """target HH:MM 까지 남은 분수 (현재시간 기준)"""
    now = datetime.now()
    now_mins = now.hour * 60 + now.minute
    target_mins = time_to_minutes(target_str)
    if target_mins is None:
        return None
    return target_mins - now_mins

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

def generate_share_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

DEP_FACILITY_RULES = [
    {"name": "🛍️ 면세점", "icon": "🛍️", "min_mins": 60, "desc": "출발 60분 이상 여유 시 이용 권장"},
    {"name": "🍽️ 레스토랑", "icon": "🍽️", "min_mins": 75, "desc": "출발 75분 이상 여유 시 이용 권장"},
    {"name": "☕ 카페", "icon": "☕", "min_mins": 30, "desc": "출발 30분 이상 여유 시 이용 가능"},
    {"name": "🛋️ 라운지", "icon": "🛋️", "min_mins": 90, "desc": "출발 90분 이상 여유 시 이용 권장"},
    {"name": "🏪 편의점", "icon": "🏪", "min_mins": 20, "desc": "출발 20분 이상 여유 시 이용 가능"},
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


# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
  <div class="hero-title">🛫 AI-PORT</div>
  <div class="hero-sub">실시간 공항 스마트 네비게이션 · Powered by AI &amp; 공공 데이터</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 모드 선택 화면
# ─────────────────────────────────────────────
if st.session_state.mode is None:
    st.markdown("<h2 style='text-align:center; color:rgba(255,255,255,0.9); margin-bottom:0.3rem;'>서비스를 선택하세요</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.4); margin-bottom:2rem;'>출발하시나요? 아니면 입국하는 분을 마중 가시나요?</p>", unsafe_allow_html=True)

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
    <div style='text-align:center; color:rgba(255,255,255,0.25); font-size:0.8rem; padding:1rem;'>
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
            st.rerun()
        st.markdown("---")

        search_flight = st.text_input("✈️ 편명 검색 (예: KE123, OZ311)", placeholder="편명을 입력하세요")
        st.markdown("---")

        st.subheader("📍 현재 위치")
        current_loc = st.selectbox("현재 어디 계세요?", [
            "장기 주차장 (도보 30분)",
            "단기 주차장 (도보 15분)",
            "터미널 입구 (도보 10분)",
            "체크인 카운터 앞 (도보 5분)",
            "출국장 내부 (도보 2분)",
        ])
        loc_walk_time = {
            "장기 주차장 (도보 30분)": 30,
            "단기 주차장 (도보 15분)": 15,
            "터미널 입구 (도보 10분)": 10,
            "체크인 카운터 앞 (도보 5분)": 5,
            "출국장 내부 (도보 2분)": 2,
        }[current_loc]

        st.subheader("⚙️ 상황 설정")
        checkin_done = st.toggle("✅ 체크인 완료", value=False)
        security_done = st.toggle("✅ 보안검색 통과", value=False)
        immig_done = st.toggle("✅ 출국심사 완료", value=False)

    # ── 데이터 로드 ──
    with st.spinner("🔄 실시간 항공편 데이터 불러오는 중..."):
        df_flights = get_departure_flights()
        df_congestion = get_departure_congestion()

    if df_flights is None or df_flights.empty:
        st.error("⚠️ 출국 항공편 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
        st.stop()

    # ── 편명 검색 ──
    if search_flight:
        flight_match = df_flights[df_flights["편명"].str.upper() == search_flight.upper().strip()]
    else:
        now_hm = datetime.now().strftime("%H:%M")
        df_valid = df_flights[df_flights["예정시간"] != "N/A"]
        df_upcoming = df_valid[df_valid["예정시간"] >= now_hm]
        flight_match = df_upcoming.head(1) if not df_upcoming.empty else df_flights.head(1)

    if flight_match.empty:
        st.warning(f"'{search_flight}' 항공편을 찾을 수 없습니다.")
        st.stop()

    flight = flight_match.iloc[0]
    dep_time_str = flight["예정시간"]
    est_time_str = flight["변경/출발시간"]
    mins_left = minutes_diff(dep_time_str)
    if mins_left is None:
        mins_left = 90  # fallback

    urgency = get_urgency(mins_left)
    urg_emoji = urgency_emoji(mins_left)

    col_main, col_side = st.columns([1.6, 1])

    with col_main:
        # ── 1) 탑승수속 남은 시간 게이지 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>탑승 시간 현황</h4>", unsafe_allow_html=True)

        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("✈️ 편명", flight['편명'])
        col_f2.metric("🌏 목적지", flight['목적지'])
        col_f3.metric("🚪 탑승구", flight.get('탑승구(Gate)', '미정'))

        gauge_pct = max(0, min(100, int(mins_left / 180 * 100))) if mins_left >= 0 else 0
        gauge_class = f"gauge-{urgency}"

        st.markdown(f"""
        <div style='margin: 1rem 0;'>
          <div style='display:flex; justify-content:space-between; margin-bottom:0.4rem;'>
            <span style='color:rgba(255,255,255,0.7); font-size:0.9rem;'>{urg_emoji} 출발까지 남은 시간</span>
            <span style='font-size:1.5rem; font-weight:800;
              color:{"#34d399" if urgency=="green" else "#fbbf24" if urgency=="yellow" else "#f87171"};'>
              {max(0, mins_left)}분
            </span>
          </div>
          <div class='gauge-wrap'>
            <div class='gauge-bar {gauge_class}' style='width:{gauge_pct}%;'></div>
          </div>
          <div style='display:flex; justify-content:space-between; color:rgba(255,255,255,0.35); font-size:0.75rem; margin-top:0.3rem;'>
            <span>예정 출발: {dep_time_str}</span>
            <span>{"변경: " + est_time_str if est_time_str != dep_time_str else "정시 출발 예정"}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if urgency == "green":
            st.success("🟢 여유 — 시간이 충분합니다. 편의시설을 이용하실 수 있습니다.")
        elif urgency == "yellow":
            st.warning("🟡 주의 — 슬슬 게이트 방향으로 이동을 준비하세요.")
        else:
            st.error("🔴 긴급 — 즉시 게이트로 이동하세요!")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── 2) 현재 위치 기준 남은 시간 + 단계 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📍 현재 위치 기반 단계 가이드</h4>", unsafe_allow_html=True)

        steps = [
            ("🎫 체크인", checkin_done),
            ("🔍 보안검색", security_done),
            ("🛂 출국심사", immig_done),
            (f"🚶 게이트 이동 ({loc_walk_time}분)", False),
        ]
        for step_name, done in steps:
            if done:
                st.markdown(f"""
                <div class='phase-item phase-done'>
                  <span style='font-size:1.1rem; margin-right:0.8rem;'>✅</span>
                  <span style='color:rgba(255,255,255,0.5); text-decoration:line-through;'>{step_name}</span>
                </div>""", unsafe_allow_html=True)
            elif not all([s[1] for s in steps[:steps.index((step_name, done))]]):
                st.markdown(f"""
                <div class='phase-item phase-active'>
                  <span style='font-size:1.1rem; margin-right:0.8rem; animation: pulse-red 1s infinite;'>▶️</span>
                  <span style='color:#60b8ff; font-weight:600;'>{step_name} ← 지금 여기!</span>
                </div>""", unsafe_allow_html=True)
                break
            else:
                st.markdown(f"""
                <div class='phase-item phase-pending'>
                  <span style='font-size:1.1rem; margin-right:0.8rem;'>⏳</span>
                  <span style='color:rgba(255,255,255,0.5);'>{step_name}</span>
                </div>""", unsafe_allow_html=True)

        # 도보 시간 경고
        if mins_left <= loc_walk_time + 10:
            st.error(f"⚠️ 현재 위치에서 게이트까지 {loc_walk_time}분 소요! 즉시 이동하세요.")
        elif mins_left <= loc_walk_time + 20:
            st.warning(f"🚶 게이트까지 약 {loc_walk_time}분 소요. 곧 출발하세요.")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── 5) 시설 이용 가능 여부 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>🏪 시설 이용 가능 여부</h4>", unsafe_allow_html=True)
        fac_cols = st.columns(len(DEP_FACILITY_RULES))
        for i, fac in enumerate(DEP_FACILITY_RULES):
            available = mins_left >= fac["min_mins"]
            with fac_cols[i]:
                st.markdown(f"""
                <div style='text-align:center; padding:0.8rem 0.3rem;
                  background:{"rgba(52,211,153,0.08)" if available else "rgba(248,113,113,0.06)"};
                  border-radius:12px; border:1px solid {"rgba(52,211,153,0.2)" if available else "rgba(248,113,113,0.15)"};'>
                  <div style='font-size:1.5rem;'>{fac["icon"]}</div>
                  <div style='font-size:0.7rem; color:rgba(255,255,255,0.7); margin:0.3rem 0;'>{fac["name"].split(" ")[1]}</div>
                  <div style='font-size:0.8rem; font-weight:700; color:{"#34d399" if available else "#f87171"};'>
                    {"✅ 가능" if available else "❌ 촉박"}
                  </div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        # ── 3 & 4) RL 행동 추천 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>🧠 AI 행동 추천</h4>", unsafe_allow_html=True)

        avg_density = 0.0
        if df_congestion is not None and not df_congestion.empty:
            avg_density_raw = df_congestion["대기 시간(분)"].mean()
            avg_density = min(1.0, avg_density_raw / 30.0)

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
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 6) 이동 타이밍 카운트다운 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>⏱️ 이동 타이밍 카운트다운</h4>", unsafe_allow_html=True)

        move_in_mins = max(0, mins_left - loc_walk_time - 15)  # 15분 여유
        now_dt = datetime.now()
        move_time_dt = now_dt + timedelta(minutes=move_in_mins)

        st.metric("지금 이동 출발 권장 시각", move_time_dt.strftime("%H:%M"))
        st.metric("게이트 도착 여유 시간", f"{max(0, mins_left - loc_walk_time)}분 전 도착 예상")

        cd_h = move_in_mins // 60
        cd_m = move_in_mins % 60
        st.markdown(f"""
        <div style='text-align:center; margin:1rem 0; padding:1rem;
          background:rgba(255,255,255,0.04); border-radius:14px;'>
          <div style='color:rgba(255,255,255,0.5); font-size:0.8rem; margin-bottom:0.4rem;'>이동 출발까지</div>
          <div style='font-size:2.5rem; font-weight:900;
            color:{"#34d399" if move_in_mins > 30 else "#fbbf24" if move_in_mins > 10 else "#f87171"};'>
            {"즉시 출발!" if move_in_mins <= 0 else f"{cd_h}시간 {cd_m}분" if cd_h > 0 else f"{cd_m}분 후"}
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 출국장 혼잡도 현황 ──
        if df_congestion is not None and not df_congestion.empty:
            st.markdown("<div class='info-card'>", unsafe_allow_html=True)
            st.markdown("<h4>🚦 출국장 혼잡도 현황</h4>", unsafe_allow_html=True)
            df_cong_sorted = df_congestion.sort_values("대기 시간(분)", ascending=True)
            best = df_cong_sorted.iloc[0]
            worst = df_cong_sorted.iloc[-1]
            st.markdown(f"""
            <div style='margin-bottom:0.5rem;'>
              <span class='badge badge-green'>🟢 추천: {best['게이트(Gate)']} ({best['대기 인원(명)']}명 / {best['대기 시간(분)']}분)</span><br>
              <span class='badge badge-red'>🔴 혼잡: {worst['게이트(Gate)']} ({worst['대기 인원(명)']}명 / {worst['대기 시간(분)']}분)</span>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("전체 게이트 현황 보기"):
                st.dataframe(df_congestion.sort_values("대기 시간(분)"), hide_index=True, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='text-align:right; color:rgba(255,255,255,0.25); font-size:0.75rem; margin-top:1rem;'>
      마지막 업데이트: {datetime.now().strftime("%H:%M:%S")} · 공공데이터포털 실시간
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

        search_arr_flight = st.text_input("✈️ 입국 편명 검색 (예: OZ123)", placeholder="마중할 편명 입력")
        st.markdown("---")

        st.subheader("📍 현재 마중객 위치")
        picker_loc = st.selectbox("현재 어디 계세요?", [
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
    if search_arr_flight:
        arr_match = df_arr[df_arr["편명"].str.upper() == search_arr_flight.upper().strip()]
    else:
        now_hm = datetime.now().strftime("%H:%M")
        df_valid_arr = df_arr[df_arr["예정시간"] != "N/A"]
        df_upcoming_arr = df_valid_arr[df_valid_arr["예정시간"] >= now_hm]
        arr_match = df_upcoming_arr.head(1) if not df_upcoming_arr.empty else df_arr.head(1)

    if arr_match.empty:
        st.warning(f"'{search_arr_flight}' 항공편을 찾을 수 없습니다.")
        st.stop()

    arr_flight = arr_match.iloc[0]
    arr_status = arr_flight.get("상태", "") or ""

    # 현재 단계 매핑
    status_to_phase = {
        "착륙": 0, "공역": 0, "접근": 0,
        "심사": 1, "입국": 1,
        "수하물": 2, "수취": 2,
        "출구": 3, "도착": 3,
    }
    p_phase = 0
    for keyword, phase in status_to_phase.items():
        if keyword in arr_status:
            p_phase = phase
            break
    if arr_status in ["도착", "착륙"]:
        p_phase = 0
    elif "수하물" in arr_status:
        p_phase = 2

    # 예상 남은 시간
    time_remaining = sum(ARRIVAL_PHASE_MINS[p_phase:])

    col_arr_main, col_arr_right = st.columns([1.6, 1])

    with col_arr_main:
        # ── 1) 현재 단계 상태 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>✈️ 입국 여객 현재 상태</h4>", unsafe_allow_html=True)

        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("편명", arr_flight["편명"])
        col_a2.metric("출발지", arr_flight["출발지"])
        col_a3.metric("현재 상태", arr_status if arr_status else "정보 없음")

        st.markdown("<br>", unsafe_allow_html=True)
        for i, phase_name in enumerate(ARRIVAL_PHASES):
            mins_for_phase = ARRIVAL_PHASE_MINS[i]
            if i < p_phase:
                st.markdown(f"""
                <div class='phase-item phase-done'>
                  <span style='margin-right:0.8rem; font-size:1.1rem;'>✅</span>
                  <span style='color:rgba(255,255,255,0.45); text-decoration:line-through;'>{phase_name} (완료)</span>
                </div>""", unsafe_allow_html=True)
            elif i == p_phase:
                st.markdown(f"""
                <div class='phase-item phase-active'>
                  <span style='margin-right:0.8rem; font-size:1.1rem;'>▶️</span>
                  <span style='color:#60b8ff; font-weight:700;'>{phase_name} 진행 중 (약 {mins_for_phase}분 소요)</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='phase-item phase-pending'>
                  <span style='margin-right:0.8rem; font-size:1.1rem;'>⏳</span>
                  <span style='color:rgba(255,255,255,0.4);'>{phase_name} (약 {mins_for_phase}분 예정)</span>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 2) 예상 만남 시간 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>🤝 예상 만남 시간</h4>", unsafe_allow_html=True)
        meet_time_dt = datetime.now() + timedelta(minutes=time_remaining)
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("여객 출구 도착 예상", meet_time_dt.strftime("%H:%M"))
        col_m2.metric("예상 남은 시간", f"약 {time_remaining}분")

        meet_gap = time_remaining - picker_dist
        if meet_gap > 10:
            st.success(f"🟢 아직 {meet_gap}분 여유 있습니다. 서두르지 않으셔도 됩니다.")
        elif meet_gap > 0:
            st.warning(f"🟡 약 {meet_gap}분 후 이동 시작하면 딱 맞습니다.")
        else:
            st.error("🔴 즉시 게이트 앞으로 이동하세요!")
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 5) 대중교통 안내 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>🚇 공항 밖 대중교통 안내</h4>", unsafe_allow_html=True)
        dest_region = st.selectbox("목적지 방면을 선택하세요", list(TRANSIT_INFO.keys()))
        transits = TRANSIT_INFO[dest_region]
        for t in transits:
            st.markdown(f"""
            <div class='transit-card'>
              <div class='transit-icon'>{t['icon']}</div>
              <div>
                <div class='transit-name'>{t['name']} <span style='color:#fbbf24; font-size:0.85rem;'>⏱ {t['time']}</span></div>
                <div class='transit-detail'>💰 {t['cost']} · {t['tip']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_arr_right:
        # ── 4) RL 이동 타이밍 알람 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>🧠 AI 이동 타이밍 추천</h4>", unsafe_allow_html=True)

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
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 3) 픽업자 공유 코드 ──
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📡 픽업 연동 코드 공유</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div style='color:rgba(255,255,255,0.55); font-size:0.82rem; margin-bottom:1rem; line-height:1.6;'>
          아래 코드를 마중할 여객과 공유하면<br>서로의 위치/상태를 연동하여 확인할 수 있습니다.
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.my_share_code is None:
            if st.button("🔑 내 공유 코드 생성", use_container_width=True, type="primary"):
                code = generate_share_code()
                st.session_state.my_share_code = code
                st.session_state.share_codes[code] = {
                    "passenger_phase": p_phase,
                    "time_remaining": time_remaining,
                    "flight": arr_flight["편명"],
                    "picker_loc": picker_loc,
                }
                st.rerun()
        else:
            # 내 코드 업데이트
            st.session_state.share_codes[st.session_state.my_share_code] = {
                "passenger_phase": p_phase,
                "time_remaining": time_remaining,
                "flight": arr_flight["편명"],
                "picker_loc": picker_loc,
            }
            st.markdown(f"""
            <div class='share-code-box'>
              <div style='color:rgba(255,255,255,0.5); font-size:0.8rem; margin-bottom:0.5rem;'>내 공유 코드</div>
              <div class='share-code'>{st.session_state.my_share_code}</div>
              <div style='color:rgba(255,255,255,0.4); font-size:0.75rem; margin-top:0.5rem;'>이 코드를 상대방에게 알려주세요</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 코드 재발급", use_container_width=True):
                st.session_state.my_share_code = None
                st.rerun()

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        st.markdown("<div style='color:rgba(255,255,255,0.6); font-size:0.82rem; margin-bottom:0.5rem;'>상대방 코드 조회</div>", unsafe_allow_html=True)
        partner_code = st.text_input("상대방 코드 입력", placeholder="예: A3K9Z", key="partner_input")
        if partner_code:
            partner_code = partner_code.upper().strip()
            if partner_code in st.session_state.share_codes:
                p_data = st.session_state.share_codes[partner_code]
                st.success("✅ 연동 성공!")
                p_phase_name = ARRIVAL_PHASES[p_data['passenger_phase']] if p_data['passenger_phase'] < len(ARRIVAL_PHASES) else "알 수 없음"
                st.markdown(f"""
                <div style='background:rgba(52,211,153,0.08); border:1px solid rgba(52,211,153,0.2); border-radius:12px; padding:1rem; font-size:0.85rem;'>
                  ✈️ <b>항공편:</b> {p_data['flight']}<br>
                  📍 <b>현재 단계:</b> {p_phase_name}<br>
                  ⏱️ <b>남은 시간:</b> 약 {p_data['time_remaining']}분<br>
                  🚗 <b>마중객 위치:</b> {p_data['picker_loc']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("코드를 찾을 수 없습니다. 다시 확인해주세요.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='text-align:right; color:rgba(255,255,255,0.25); font-size:0.75rem; margin-top:1rem;'>
      마지막 업데이트: {datetime.now().strftime("%H:%M:%S")} · 공공데이터포털 실시간
    </div>
    """, unsafe_allow_html=True)
