import re

file_path = "app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update CSS: Add Container styles and Button Gradients
css_addition = """
/* Streamlit Native Container Styling (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid rgba(0, 132, 255, 0.15) !important;
    background: var(--color-card-white) !important;
    border-radius: 16px !important;
    padding: 0.8rem 1rem !important;
    box-shadow: 0 4px 20px rgba(0, 132, 255, 0.08) !important;
    transition: box-shadow 0.3s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 6px 24px rgba(0, 132, 255, 0.12) !important;
}

/* Phase Items Styling Enhancement */
.phase-item {
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
}

/* Button Gradients & Hover Lift */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0084FF 0%, #0056D2 100%) !important;
    color: var(--color-card-white) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0, 132, 255, 0.25) !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, #0076E5 0%, #004CB8 100%) !important;
    box-shadow: 0 8px 20px rgba(0, 132, 255, 0.35) !important;
}
"""

if "stVerticalBlockBorderWrapper" not in content:
    content = content.replace("</style>", css_addition + "\n</style>")


# 2. Fix the Map Style to Light Mode!
old_map = "st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))"
new_map = "st.pydeck_chart(pdk.Deck(map_style='light', layers=[layer], initial_view_state=view_state))"
content = content.replace(old_map, new_map)


# 3. Add st.container(border=True) wrappers logically where headers are.
# Wait, this is difficult via simple string replacement without messing up python indentation.
# Let's use string replacement to add st.markdown("---") or similar dividers, or just use HTML containers carefully.
# Wait, I CAN inject st.container via `with ...:` if I use ast or just don't inject `with`, but instead do:
# c1 = st.container(border=True)
# c1.markdown(...)
# That is also complex.

# Wait, if I use:
# st.markdown("<div data-testid='stVerticalBlockBorderWrapper'>", unsafe_allow_html=True)
# It's an HTML div simulating a Streamlit container.
# BUT we saw earlier that Streamlit closes unclosed divs instantly and creates "ghost cards".
# So using standard HTML wraps for Streamlit components DOES NOT WORK.

# What if I find the layout blocks and just manually add `with st.container(border=True):` indenting the lines 4 spaces?
# Let's simply write an intelligent python rewriter for `app.py`.
lines = content.split('\n')
new_lines = []
in_main_block = False

# Actually, doing indentation programmatically might break syntax if not extremely careful.
# Instead of `with st.container`, we can use `st.markdown('<hr class="section-divider">', unsafe_allow_html=True)` 
# to artificially group things without needing nested scopes.
# BUT wait, the instruction is to use `st.container` for a PREMIUM look (cards).
# Let's do a trick: we don't need `st.container` if we style the existing Streamlit columns!
# `col_main, col_side = st.columns([1.6, 1])`
# `with col_main:`
# Streamlit components are grouped inside `col_main`. 
# BUT `col_main` spans the whole height.

# Let's just fix the map style and CSS first.
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("CSS enhanced and Map Style fixed.")
