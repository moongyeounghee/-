import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    map_css = '''
/* ------------------------------------------------------------- */
/* 지도 미세조정 (육지 초록빛 + 바다 푸른빛 강화) */
/* ------------------------------------------------------------- */
[data-testid="stDeckGlJsonChart"] {
    /* 원래의 창백한 Carto 맵 색상을 육지는 싱그럽게, 바다는 짙고 푸르게 펌핑! */
    filter: hue-rotate(-15deg) saturate(4.0) brightness(0.95) contrast(1.05) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(14, 165, 233, 0.15) !important;
    transition: filter 0.5s ease;
}
'''

    # Clean existing map CSS blocks
    content = re.sub(r'/\* 지도 .*?\}\s*', '', content, flags=re.DOTALL)
    content = re.sub(r'/\* ------------------------------------------------------------- \*/\s*/\* 지도 미세조정.*?\n\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\[data-testid="stDeckGlJsonChart"\].*?\}', '', content, flags=re.DOTALL)

    # Inject
    content = content.replace("</style>", map_css + "\n</style>")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Success: Fine-tuned chart colors.")

except Exception as e:
    print(f"Error: {e}")
