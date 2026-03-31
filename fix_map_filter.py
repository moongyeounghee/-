import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The previous filter broke the map. Let's use a much simpler cleaner filter.
    # Carto Positron's default water is already light blue. We just boost its saturation 
    # and maybe hue-rotate slightly towards cyan to match #BFDFFF.
    # Also, we return brightness to normal.
    
    pattern = r'/\* 지도 청보리\(Mint\).*?\}\s*\[data-testid="stDeckGlJsonChart"\]:hover\s*{[^}]+}'
    
    clean_map_css = '''/* 지도 청보리 & 스카이블루: 기본 맵(Carto Positron)의 원래 예쁜 물색을 되살리고 채도만 증폭 (하얗게 날아가는 버그 수정) */
[data-testid="stDeckGlJsonChart"] {
    filter: saturate(2.5) hue-rotate(-10deg) brightness(1.0) contrast(1.0) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(14, 165, 233, 0.15) !important;
    transition: filter 0.5s ease;
}'''

    # If the previous pattern is not found, it means the regex didn't match. 
    # Let's just use string replace for safety.
    
    # Try a broader regex to replace the map filter block completely
    broad_pattern = r'\[data-testid="stDeckGlJsonChart"\]\s*{[^}]+}(?:\s*\[data-testid="stDeckGlJsonChart"\]:hover\s*{[^}]+})?'
    
    content = re.sub(broad_pattern, clean_map_css, content, count=1)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Successfully replaced with clean saturation filter.")

except Exception as e:
    print(f"Error customizing map styles: {e}")
