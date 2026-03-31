import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Apply Glassmorphism to the PC wrapper
    wrapper_regex = r'div\[data-testid="stVerticalBlock"\] > div > div\[data-testid="stVerticalBlockBorderWrapper"\]\s*{[^}]*}'
    glassmorphism_css = '''div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.45) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.7) !important;
    box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important;
    padding: 1.5rem !important;
    border-radius: 20px !important;
}'''
    content = re.sub(wrapper_regex, glassmorphism_css, content)

    # 2. Fix the Mode-Card (출국/입국 선택 상자) Mobile proportions on Desktop
    mode_card_old_regex = r'\.mode-card\s*\{[^}]*\}'
    mode_card_new_css = '''.mode-card {
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
}'''

    content = re.sub(mode_card_old_regex, mode_card_new_css, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully applied Glassmorphism and fixed Mode Card Mobile Proportions.")
    
except Exception as e:
    print(f"Error customizing styles: {e}")
