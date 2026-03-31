import re

file_path = "app.py"
try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Revert Secondary Button Global Disaster
    old_secondary_css = """/* 2. 입국(Arrival) 버튼 (투명화 해결): 차분한 밤하늘색 (Night Sky Navy Gradient) */
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
}"""

    new_secondary_css = """/* 2. 모든 보조 버튼 원상 복구 및 투명화 방지: 하늘색 외곽선(Outline) 버튼 테마 */
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
}"""

    if old_secondary_css in content:
        content = content.replace(old_secondary_css, new_secondary_css)
    else:
        print("Could not find the exact old secondary button CSS. Will attempt regex.")
        # Fallback regex if spacing is weird
        content = re.sub(r'/\* 2\. 입국\(Arrival\) 버튼.*?\}\n\}', new_secondary_css, content, flags=re.DOTALL)


    # 2. Add Sky Tint to Global Background (Cool Gray to Sky Lightest)
    content = content.replace("--color-bg-light: #EDF2F7;", "--color-bg-light: #F0F9FF;")
    content = content.replace("--color-secondary-bg: #E2E8F0;", "--color-secondary-bg: #E0F2FE;")

    # Also fix config.toml
    config_path = ".streamlit/config.toml"
    with open(config_path, "r", encoding="utf-8") as f_c:
        config = f_c.read()
    
    config = config.replace('backgroundColor="#EDF2F7"', 'backgroundColor="#F0F9FF"')
    
    with open(config_path, "w", encoding="utf-8") as f_c:
        f_c.write(config)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully reverted secondary buttons and tinted global background to sky blue.")

except Exception as e:
    print(f"Error applying design: {e}")
