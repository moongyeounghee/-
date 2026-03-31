import re

file_path = "app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Background Color Fix (Cool Gray instead of glaring bright blue)
content = content.replace("--color-bg-light: #F0F7FF;", "--color-bg-light: #EDF2F7;")
content = content.replace("--color-secondary-bg: #DBEDFF;", "--color-secondary-bg: #E2E8F0;")

# 2. Border contrast enhancement (Remove overwhelming blue borders)
content = content.replace("border: 1px solid rgba(0, 132, 255, 0.15) !important;", "border: 1px solid rgba(0, 0, 0, 0.08) !important;")
content = content.replace("box-shadow: 0 4px 20px rgba(0, 132, 255, 0.08) !important;", "box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;")

# 3. Map Marker and Style Visibility Enhancement
# Change yellow/red pale markers to deep blue / crimson red # [255, 75, 75, 230] to [220, 20, 60, 255]
content = content.replace("[255, 75, 75, 230]", "[220, 20, 60, 255]") 
content = content.replace("[251, 191, 36, 200]", "[0, 85, 255, 255]")

# Change map style from light to road (darker land/water contrast)
content = content.replace("map_style='light'", "map_style='road'")

# 4. Streamlit config.toml background update
config_path = ".streamlit/config.toml"
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = f.read()
    config = config.replace('backgroundColor="#F0F7FF"', 'backgroundColor="#EDF2F7"')
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config)
except Exception as e:
    print(f"Skipping config modification: {e}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Glare and radar visibility resolved!")
