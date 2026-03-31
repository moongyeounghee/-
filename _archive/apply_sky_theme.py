import re

file_path = "app.py"
try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    css_sky_enhancements = """
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

/* 2. 입국(Arrival) 버튼 (투명화 해결): 차분한 밤하늘색 (Night Sky Navy Gradient) */
div.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #1E3A8A 0%, #312E81 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(30, 58, 138, 0.25) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="secondary"]:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #1D4ED8 0%, #3730A3 100%) !important;
    color: white !important;
    box-shadow: 0 8px 25px rgba(30, 58, 138, 0.35) !important;
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
"""

    if "/* '인하늘' 조이름 모티브" not in content:
        content = content.replace("</style>", css_sky_enhancements + "\n</style>")

    # 4. Change default primary blue to match the Sky Blue motif (for spinners, headers)
    # Old streamilt primary was #0084FF. Let's make it #0EA5E9 (Sky 500)
    config_path = ".streamlit/config.toml"
    with open(config_path, "r", encoding="utf-8") as f_c:
        config = f_c.read()
    config = config.replace('primaryColor="#0084FF"', 'primaryColor="#0EA5E9"')
    with open(config_path, "w", encoding="utf-8") as f_c:
        f_c.write(config)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Sky blue motif and secondary button styling applied.")

except Exception as e:
    print(f"Error applying design: {e}")
