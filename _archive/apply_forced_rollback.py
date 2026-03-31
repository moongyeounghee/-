import re

file_path = "app.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The previous script accidentally deleted the container wrapper CSS or failed to find it.
    # We will inject the Glassmorphism/Rollback container block safely at the end of the <style> block.
    
    # Check if the block exists
    if 'div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"]' in content:
        # It exists, we should replace it
        content = re.sub(
            r'div\[data-testid="stVerticalBlock"\] > div > div\[data-testid="stVerticalBlockBorderWrapper"\]\s*{[^}]*}',
            r'''div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important;
    padding: 1.5rem !important;
    border-radius: 20px !important;
}''', content)
    else:
        # It does not exist, inject before </style>
        css_inject = '''
/* ------------------------------------------------------------- */
/* PC 대시보드 구조 복원 (거대 컨테이너 바탕 롤백) */
/* ------------------------------------------------------------- */
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 10px 40px rgba(14, 165, 233, 0.12) !important;
    padding: 1.5rem !important;
    border-radius: 20px !important;
}
'''
        content = content.replace("</style>", css_inject + "\n</style>")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Restored the missing container CSS successfully.")

except Exception as e:
    print(f"Error: {e}")
