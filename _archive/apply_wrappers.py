import sys

file_path = "app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

blocks_to_wrap = [
    (
        "# ── 1) 탑승수속 남은 시간 게이지 ──\n        \n        st.markdown(f\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>탑승 시간 현황</h3>\", unsafe_allow_html=True)",
        "st.error(\"🔴 긴급 — 즉시 게이트로 이동하세요!\")",
        "        # ── 1) 탑승수속 남은 시간 게이지 ──\n        with st.container(border=True):\n            st.markdown(f\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>탑승 시간 현황</h3>\", unsafe_allow_html=True)"
    ),
    (
        "# ── 2) 현재 위치 기준 남은 시간 + 단계 ──\n        \n        st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>📍 현재 위치 기반 단계 가이드</h3>\", unsafe_allow_html=True)",
        "st.warning(f\"🚶 게이트까지 약 {loc_walk_time}분 소요. 곧 출발하세요.\")",
        "        # ── 2) 현재 위치 기준 남은 시간 + 단계 ──\n        with st.container(border=True):\n            st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>📍 현재 위치 기반 단계 가이드</h3>\", unsafe_allow_html=True)"
    ),
    (
        "# ── 3 & 4) RL 행동 추천 ──\n        \n        st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>🧠 AI 행동 추천</h3>\", unsafe_allow_html=True)",
        "            </div>\n            \"\"\", unsafe_allow_html=True)",
        "        # ── 3 & 4) RL 행동 추천 ──\n        with st.container(border=True):\n            st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>🧠 AI 행동 추천</h3>\", unsafe_allow_html=True)"
    ),
    (
        "# ── 6) 이동 타이밍 카운트다운 ──\n        \n        st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>⏱️ 이동 타이밍 카운트다운</h3>\", unsafe_allow_html=True)",
        "        </div>\n        \"\"\", unsafe_allow_html=True)",
        "        # ── 6) 이동 타이밍 카운트다운 ──\n        with st.container(border=True):\n            st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>⏱️ 이동 타이밍 카운트다운</h3>\", unsafe_allow_html=True)"
    ),
    (
        "# ── 1) 현재 단계 상태 ──\n        \n        st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:1.5rem; margin-bottom:0.5rem;'>✈️ 입국 여객 현재 상태</h3>\", unsafe_allow_html=True)",
        "                      <span style='color:#718096; font-weight:600;;'>{phase_name}</span>\n                    </div>\"\"\", unsafe_allow_html=True)",
        "        # ── 1) 현재 단계 상태 ──\n        with st.container(border=True):\n            st.markdown(\"<h3 style='color:var(--color-primary); font-weight:800; margin-top:0.2rem; margin-bottom:1rem;'>✈️ 입국 여객 현재 상태</h3>\", unsafe_allow_html=True)"
    )
]

for start_str, end_str, replace_start_str in blocks_to_wrap:
    try:
        start_idx = content.index(start_str)
        end_idx = content.index(end_str, start_idx) + len(end_str)
        
        block = content[start_idx:end_idx]
        inner_block = block[len(start_str):]
        
        indented_inner = "\n".join(["    " + line if line else "" for line in inner_block.split("\n")])
        
        new_block = replace_start_str + indented_inner
        
        content = content[:start_idx] + new_block + content[end_idx:]
        print(f"Wrapped block successfully.")
    except ValueError as e:
        print(f"Skipping a block, not found: {start_str[:30]}...")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Wrappers applied.")
