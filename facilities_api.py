"""
인천국제공항공사 여객터미널 시설정보 현황 API 연동 모듈
공공데이터포털: B551177/FacilitiesInformation/getFacilitesInfo
"""
import requests
import json
import os
from datetime import datetime, timedelta

SERVICE_KEY = "f057b51365f28ead992af0e533cd91df9f3a469051f42f2c1ae684426c843f39"
BASE_URL = "http://apis.data.go.kr/B551177/FacilitiesInformation/getFacilitesInfo"
CACHE_FILE = "facilities_cache.json"
CACHE_TTL_HOURS = 24

# terminalid → 내부 터미널 코드
TERMINAL_MAP = {
    "P01": "T1",   # 제1여객터미널
    "P02": "T1",   # 제1터미널 교통센터
    "P03": "T2",   # 제2여객터미널
    "P04": "T2",   # 제2터미널 교통센터
    "P05": "T1",   # 탑승동(Concourse) → T1 귀속
}

# 대분류/중분류 → 내부 카테고리 매핑
def _map_category(item: dict) -> str | None:
    lcat = (item.get("lcategorynm") or "").strip()
    mcat = (item.get("mcategorynm") or "").strip()
    duty = item.get("lcduty", "N") == "Y"

    # 라운지 (우선 체크)
    if "라운지" in mcat or "라운지" in lcat:
        return "LOUNGE"

    # 편의점 / 편의시설
    convenience_kw = ["편의점", "편의시설", "약국", "의료", "서점", "문구"]
    if any(k in mcat for k in convenience_kw):
        return "CONVENIENCE"

    # 면세 쇼핑
    shopping_kw = ["면세", "쇼핑", "패션", "잡화", "화장품", "향수", "주류", "담배", "전자", "명품", "가방", "시계", "보석"]
    if duty and (any(k in lcat for k in ["쇼핑"]) or any(k in mcat for k in shopping_kw)):
        return "SHOPPING"
    if any(k in mcat for k in shopping_kw) or (duty and "쇼핑" in lcat):
        return "SHOPPING"

    # 식음료 분기
    food_lcat = "식" in lcat or "음료" in lcat or "푸드" in lcat
    if food_lcat:
        cafe_kw = ["카페", "커피", "스낵", "디저트", "베이커리", "도넛", "아이스크림", "음료", "주스", "버블티"]
        if any(k in mcat for k in cafe_kw):
            return "CAFE"
        return "FOOD"

    return None


def _fetch_all_raw() -> list:
    """API에서 모든 시설 데이터를 페이지 단위로 전부 가져옴."""
    all_items = []
    page = 1
    num_rows = 500
    try:
        while True:
            params = {
                "serviceKey": SERVICE_KEY,
                "type": "json",
                "numOfRows": num_rows,
                "pageNo": page,
            }
            res = requests.get(BASE_URL, params=params, timeout=15)
            if res.status_code != 200:
                break
            data = res.json()
            body = data.get("response", {}).get("body", {})
            items = body.get("items") or []
            if not items:
                break
            all_items.extend(items)
            total = int(body.get("totalCount", 0))
            if len(all_items) >= total:
                break
            page += 1
    except Exception as e:
        print(f"[facilities_api] fetch error: {e}")
    return all_items


def _load_cache() -> list | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        cached_at = datetime.fromisoformat(cache.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return cache.get("items", [])
    except Exception:
        pass
    return None


def _save_cache(items: list):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"cached_at": datetime.now().isoformat(), "items": items}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_all_facilities() -> list:
    """캐시에서 로드하거나 API에서 전체 시설 데이터를 가져옴."""
    cached = _load_cache()
    if cached is not None:
        return cached
    raw = _fetch_all_raw()
    if raw:
        _save_cache(raw)
    return raw


def get_facilities_by_category(
    category: str,
    terminal_key: str | None = None,
    dep_only: bool = True
) -> list[dict]:
    """
    category: SHOPPING / FOOD / CAFE / LOUNGE / CONVENIENCE
    terminal_key: 'T1' | 'T2' | None (전체)
    dep_only: 출국 구역만 (True 권장)
    반환: [{"id", "name", "category", "description", "location", "hours", "tel", "duty_free", "terminal_id", "floor"}, ...]
    """
    raw = load_all_facilities()
    result = []
    seen = set()

    for item in raw:
        # 중복 제거 (sn 기준)
        sn = item.get("sn", "")
        if sn in seen:
            continue

        # 출국 구역 필터
        if dep_only and item.get("arrordep") != "D":
            continue

        # 카테고리 매핑
        cat = _map_category(item)
        if cat != category:
            continue

        # 터미널 필터
        term_raw = item.get("terminalid", "")
        mapped_term = TERMINAL_MAP.get(term_raw, "T1")
        if terminal_key == "T1" and mapped_term != "T1":
            continue
        if terminal_key == "T2" and mapped_term != "T2":
            continue

        name = (item.get("facilitynm") or "").strip()
        if not name or name.startswith("1층") or name.startswith("2층"):  # 층/입구 항목 제외
            continue

        description = (item.get("goods") or item.get("facilityitem") or "").strip()
        if description == "-":
            description = ""

        result.append({
            "id": sn,
            "name": name,
            "category": cat,
            "description": description,
            "location": (item.get("lcnm") or "").strip(),
            "hours": (item.get("servicetime") or "").strip(),
            "tel": (item.get("tel") or "").strip().strip("-"),
            "duty_free": item.get("lcduty") == "Y",
            "terminal_id": mapped_term,
            "floor": (item.get("floorinfo") or "").strip(),
        })
        seen.add(sn)

    return result


def is_open_now(hours_str: str) -> bool | None:
    """영업시간 문자열('HH:MM ~ HH:MM')을 파싱해 현재 영업 중인지 반환. 알 수 없으면 None."""
    if not hours_str or "~" not in hours_str:
        return None
    try:
        parts = hours_str.replace(" ", "").split("~")
        open_h, open_m = map(int, parts[0].split(":"))
        close_h, close_m = map(int, parts[1].split(":"))
        now = datetime.now()
        now_mins = now.hour * 60 + now.minute
        open_mins = open_h * 60 + open_m
        close_mins = close_h * 60 + close_m
        if close_mins == 0:  # 00:00 = 자정 마감
            close_mins = 24 * 60
        return open_mins <= now_mins <= close_mins
    except Exception:
        return None
