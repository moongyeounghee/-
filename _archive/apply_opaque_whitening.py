import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 칙칙한 메트릭(Metric) 박스를 순도 100% 흰색(#FFFFFF)으로 변경
    content = content.replace("background: #F8FAFC !important;", "background: #FFFFFF !important;")
    content = content.replace("/* 3. 내부 메트릭(Metric) 및 데이터 상자 테두리 완전 삭제 (카드 안의 카드 현상 제거) */", "/* 3. 내부 메트릭(Metric) 상자 순백색(White) 통일 (때 낀 느낌 제거) */")

    # 2. 반투명(rgba) 액션 박스를 오파크(불투명 파스텔) 컬러로 통일 (탁색 섞임 방지)
    action_css_old = """/* AI Action Box / Muted Palette Overrides */
.action-box.action-red {
    background: rgba(217, 83, 79, 0.08) !important;
    border: 1px solid rgba(217, 83, 79, 0.2) !important;
    color: #D9534F !important;
}
.action-box.action-yellow {
    background: rgba(230, 168, 0, 0.08) !important;
    border: 1px solid rgba(230, 168, 0, 0.2) !important;
    color: #D09300 !important;
}
.action-box.action-green {
    background: rgba(42, 157, 143, 0.08) !important;
    border: 1px solid rgba(42, 157, 143, 0.2) !important;
    color: #2A9D8F !important;
}"""

    action_css_new = """/* AI Action Box / Opaque Pastel Overrides (파란색 배경과 섞여 탁해지는 현상 방지용 순정 솔리드 컬러) */
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
}"""

    if action_css_old in content:
        content = content.replace(action_css_old, action_css_new)
    else:
        # Fallback regex replace if slightly mutated
        content = re.sub(
            r'/\* AI Action Box / Muted Palette Overrides \*/.*?\.action-box\.action-green\s*{[^}]*}',
            action_css_new,
            content,
            flags=re.DOTALL
        )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully corrected muddy transparent colors to opaque pastel & pure white.")
    
except Exception as e:
    print(f"Error correcting muddy colors: {e}")
