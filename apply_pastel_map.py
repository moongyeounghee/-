import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the map filter block and replace it
    pattern = r'/\* 지도 눈부심 방지 e-ink 필터 \*/\s*\[data-testid="stDeckGlJsonChart"\]\s*{[^}]+}'
    
    pastel_map_css = '''/* 지도 청보리(Mint) & 스카이블루(Sky Blue) 파스텔 필터 (Plan A 기반) */
[data-testid="stDeckGlJsonChart"] {
    /* 기존 칙칙한 회색 지도를 Sepia(노란빛)로 강제 통일 후, hue-rotate로 청량한 바다/민트빛으로 180도 반전시킵니다. */
    filter: sepia(0.6) hue-rotate(175deg) saturate(1.8) brightness(1.1) contrast(0.9);
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
    transition: filter 0.5s ease;
}
[data-testid="stDeckGlJsonChart"]:hover {
    filter: sepia(0.4) hue-rotate(175deg) saturate(2.0) brightness(1.1) contrast(1.0);
}'''

    if re.search(pattern, content):
        content = re.sub(pattern, pastel_map_css, content)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully applied pastel map CSS filter.")
    else:
        print("Could not find the map filter block in app.py!")

except Exception as e:
    print(f"Error customizing map styles: {e}")
