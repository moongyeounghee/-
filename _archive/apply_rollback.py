import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Rollback transparent container to solid white container
    # From:
    # background-color: transparent !important;
    # border: none !important;
    # box-shadow: none !important;
    # padding: 0 !important;
    # To:
    # background-color: #FFFFFF !important;
    # border: none !important;
    # box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important;
    # padding: 1.5rem !important;

    target_css_regex = r'div\[data-testid="stVerticalBlock"\] > div > div\[data-testid="stVerticalBlockBorderWrapper"\]\s*{[^}]*}'
    
    new_css = '''/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 (PC 롤백: 거대 하얀 박스 + 그림자 부활) */
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important;
    padding: 1.5rem !important;
    border-radius: 20px !important;
}'''

    content = re.sub(target_css_regex, new_css, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully rolled back transparent wrapper to solid white box.")
    
except Exception as e:
    print(f"Error rolling back layout: {e}")
