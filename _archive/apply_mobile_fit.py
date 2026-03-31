import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. PC Container (stVerticalBlockBorderWrapper) Transparentization
    # We turn off the giant white background so widgets float on the sky blue.
    # From: background-color: #FFFFFF !important; ... box-shadow: 0 10px 40px ...
    # To: background-color: transparent !important; ... box-shadow: none !important;
    content = re.sub(
        r'div\[data-testid="stVerticalBlock"\] > div > div\[data-testid="stVerticalBlockBorderWrapper"\]\s*{[^}]*}',
        r'''/* 스트림릿 기본 회색 카드 테두리 잔재들 전부 날리기 (PC 모바일 핏 동기화를 위해 투명화) */
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}''',
        content
    )

    # 2. Add individual shadows to floating elements to replace the global shadow
    # and restrict phase-items width
    css_enhancement = """
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
"""

    # Replace the existing Phase Items Styling Enhancement section
    content = re.sub(
        r'/\* Phase Items Styling Enhancement \*/\s*\.phase-item\s*{[^}]*}',
        css_enhancement.strip(),
        content
    )

    # Prevent duplicates if it didn't exist or re-inject at the end of style
    if "/* Phase Items Styling Enhancement (모바일 핏 강제 적용" not in content:
        content = content.replace("</style>", css_enhancement + "\n</style>")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully applied mobile-app styling to PC elements.")
    
except Exception as e:
    print(f"Error: {e}")
