import re
import sys

file_path = "app.py"
try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Borderless & Deep Shadow
    # Change [data-testid="stVerticalBlockBorderWrapper"]
    old_border = "border: 1px solid rgba(0, 0, 0, 0.08) !important;"
    new_border = "border: none !important;"
    old_shadow = "box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;"
    new_shadow = "box-shadow: 0 10px 40px rgba(0, 0, 0, 0.06) !important;"
    
    content = content.replace(old_border, new_border)
    content = content.replace(old_shadow, new_shadow)
    
    # Also if the old blue ones are still there:
    content = content.replace("border: 1px solid rgba(0, 132, 255, 0.15) !important;", new_border)
    content = content.replace("box-shadow: 0 4px 20px rgba(0, 132, 255, 0.08) !important;", new_shadow)


    # 2. Typography: Change h3's --color-primary to a muted sophisticated dark gray (#2D3748)
    content = content.replace("color:var(--color-primary);", "color:#2D3748;")


    # 3. Mute intense warning colors
    # Replace #f87171 (bright red) with #D9534F (muted terracotta)
    content = content.replace("#f87171", "#D9534F")
    # Replace #34d399 (bright green) with #2A9D8F (deep teal)
    content = content.replace("#34d399", "#2A9D8F")
    # Replace #fbbf24 (bright yellow) with #E6A800 (dark amber)
    content = content.replace("#fbbf24", "#E6A800")
    
    
    # 4. Action Box borders (AI Recommendations)
    # The action-red box is currently using #f87171. We need to mute its background.
    # It probably doesn't have inline css but uses classes. 
    # Let's add the map filter and override action box colors in the inject CSS block.
    
    css_map_filter = """
/* 지도 눈부심 방지 e-ink 필터 */
[data-testid="stDeckGlJsonChart"] {
    filter: sepia(0.05) contrast(0.95) brightness(0.85);
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
}

/* AI Action Box / Muted Palette Overrides */
.action-box.action-red {
    background: rgba(217, 83, 79, 0.08) !important;
    border: 1px solid rgba(217, 83, 79, 0.2) !important;
    color: #D9534F !important;
}
.action-box.action-yellow {
    background: rgba(230, 168, 0, 0.08) !important;
    border: 1px solid rgba(230, 168, 0, 0.2) !important;
    color: #D09300 !important;
}
.action-box.action-green {
    background: rgba(42, 157, 143, 0.08) !important;
    border: 1px solid rgba(42, 157, 143, 0.2) !important;
    color: #2A9D8F !important;
}

/* Mute the huge red text of countdown */
.countdown-huge {
    color: #D9534F !important;
    font-weight: 800;
}
"""

    if "/* 지도 눈부심 방지 e-ink 필터" not in content:
        content = content.replace("</style>", css_map_filter + "\n</style>")

    # The countdown huge text says <h2 style='...color:#f87171;'>, which got replaced to #D9534F anyway.
    
    # Optional: reduce size of map markers from 255 to something slightly less huge if needed, 
    # but the user said they couldn't see it, so 100% opacity is good.

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("UI Muting and Borderless design applied successfully.")

except Exception as e:
    print(f"Error applying design: {e}")
