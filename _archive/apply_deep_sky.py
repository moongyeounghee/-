import re

file_path = "app.py"
try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Deepen the Sky Blue Background
    content = content.replace("--color-bg-light: #F0F9FF;", "--color-bg-light: #E0F2FE;")
    content = content.replace("--color-secondary-bg: #E0F2FE;", "--color-secondary-bg: #BAE6FD;")

    # 2. Add Shadow to Hero header and remove borders from internal metric boxes
    css_deep_sky = """
/* 3. 내부 메트릭(Metric) 및 데이터 상자 테두리 완전 삭제 (카드 안의 카드 현상 제거) */
[data-testid="stMetric"] {
    background: #F8FAFC !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px !important;
}
/* 4. 헤더 배너 '공중 부양' 효과 (Background-color 강제 적용 및 Shadow) */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}
/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 */
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important; /* 하늘색 계열 그림자로 변경 */
    border-radius: 16px !important;
}
"""

    if "/* 3. 내부 메트릭(Metric)" not in content:
        content = content.replace("</style>", css_deep_sky + "\n</style>")

    # Add a shadow to the manual HTML hero block if it exists
    # The user might have: "<div style='background-color: white; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05);'>"
    # We can regex replace the exact hardcoded HTML style that lacks a shadow.
    content = re.sub(
        r"(<div style='background-color: white; padding: 20px; border-radius: 15px; text-align: center;).*?(')",
        r"\1 border: none; box-shadow: 0 15px 50px rgba(14, 165, 233, 0.12);\2",
        content,
        flags=re.DOTALL
    )
    # Another variation in case it's using double quotes
    content = re.sub(
        r'(<div style="background-color: white; padding: 20px; border-radius: 15px; text-align: center;).*?(")',
        r'\1 border: none; box-shadow: 0 15px 50px rgba(14, 165, 233, 0.12);\2',
        content,
        flags=re.DOTALL
    )

    # 3. Fix config.toml
    config_path = ".streamlit/config.toml"
    with open(config_path, "r", encoding="utf-8") as f_c:
        config = f_c.read()
    
    config = config.replace('backgroundColor="#F0F9FF"', 'backgroundColor="#E0F2FE"')
    # If the user's config actually had something else, let's just use regex
    config = re.sub(r'backgroundColor=".*?"', 'backgroundColor="#E0F2FE"', config)
    
    with open(config_path, "w", encoding="utf-8") as f_c:
        f_c.write(config)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully deepened background sky tint and removed metric box residue.")

except Exception as e:
    print(f"Error applying design: {e}")
