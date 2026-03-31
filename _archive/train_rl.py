"""
AI-PORT RL 사전학습 스크립트 v3
────────────────────────────────
변경사항:
- gamma 0.98 -> 0.85 (음수 보상 누적 폭발 방지)
- 보상 크기 축소 및 정규화 (최대 ±10)
- 에피소드를 상태 스냅샷 단위로 단순화 (시간 흐름 대신 상태 직접 샘플링)
- alpha 0.2 (빠른 수렴)
- 에피소드 수 증가: 출국 30,000 / 입국 10,000
"""

import random
import pickle
import numpy as np
from rl_engine import (
    AIPortRLEngine,
    DEP_ACTION_0, DEP_ACTION_1, DEP_ACTION_2, DEP_ACTION_3,
    ARR_ACTION_0, ARR_ACTION_1, ARR_ACTION_2,
    ACTION_NAMES,
)

SAVE_PATH = "q_table.pkl"

# ─────────────────────────────────────────────────────────────────────────────
# 보상 함수: 시간 구간별 "정답 행동"을 명확히 정의 (±1~±10 범위)
# ─────────────────────────────────────────────────────────────────────────────
def dep_reward(action, time_left, density, margin):
    """
    실제 국제선 기준:
      60분~   : 체크인 마감 전 → 쇼핑/라운지 가능 (DEP_ACTION_0)
      30~60분 : 게이트 마감 30분전 → 이동 준비 (DEP_ACTION_1 or _2)
      15~30분 : 게이트 마감 15분전 → 즉시 이동 (DEP_ACTION_2)
      ~15분   : 긴급 탑승 불가 위험 → 우회하며 달려가기 (DEP_ACTION_3)
    """
    if time_left >= 60:
        # 여유: 쇼핑·라운지 최선, 혼잡하면 대기도 OK
        if density > 0.7:
            scores = {
                DEP_ACTION_0: +6,   # 혼잡해도 아직 시간 여유
                DEP_ACTION_1: +8,   # 혼잡 피해 대기 — 최선
                DEP_ACTION_2: +2,
                DEP_ACTION_3: +4,
            }
        else:
            scores = {
                DEP_ACTION_0: +10,  # 면세점/라운지 — 최선
                DEP_ACTION_1: +3,
                DEP_ACTION_2: +1,
                DEP_ACTION_3: -2,
            }

    elif 30 <= time_left < 60:
        # 이동 준비 구간: 대기하거나 이동 시작
        if density > 0.6:
            scores = {
                DEP_ACTION_0: -7,   # 면세점 — 이미 위험
                DEP_ACTION_1: +7,   # 혼잡 대기 후 진입 — 좋음
                DEP_ACTION_2: +5,
                DEP_ACTION_3: +8,   # 혼잡 우회 — 최선
            }
        else:
            scores = {
                DEP_ACTION_0: -6,
                DEP_ACTION_1: +6,
                DEP_ACTION_2: +9,   # 즉시 이동 — 최선
                DEP_ACTION_3: +3,
            }

    elif 15 <= time_left < 30:
        # 국제선 게이트 마감 15~30분 전: 즉시 이동 필수
        scores = {
            DEP_ACTION_0: -10,
            DEP_ACTION_1: -6,
            DEP_ACTION_2: +8,
            DEP_ACTION_3: +7 if density > 0.5 else +4,
        }

    else:
        # ~15분: 긴급 탑승 불가 위험
        scores = {
            DEP_ACTION_0: -10,
            DEP_ACTION_1: -9,
            DEP_ACTION_2: +6,
            DEP_ACTION_3: +10,  # 우회가 최선
        }

    base = scores[action]
    return base



def arr_reward(action, phase, t_rem, dist):
    """
    phase 0(착륙), 1(심사), 2(수하물), 3(출구)
    """
    if phase <= 1:  # 아직 한참 기다려야 함
        gap = t_rem - dist
        if gap > 20:
            scores = {ARR_ACTION_0: +8, ARR_ACTION_1: +2, ARR_ACTION_2: -8}
        else:
            scores = {ARR_ACTION_0: -4, ARR_ACTION_1: +8, ARR_ACTION_2: -4}
    elif phase == 2:  # 수하물 수취 중
        if t_rem > dist + 5:
            scores = {ARR_ACTION_0: +2, ARR_ACTION_1: +8, ARR_ACTION_2: +4}
        else:
            scores = {ARR_ACTION_0: -6, ARR_ACTION_1: +6, ARR_ACTION_2: +8}
    else:  # phase 3: 출구 도착 임박
        scores = {ARR_ACTION_0: -8, ARR_ACTION_1: +4, ARR_ACTION_2: +10}

    return scores[action]


# ─────────────────────────────────────────────────────────────────────────────
# 학습 (상태 스냅샷 직접 샘플링 방식)
# ─────────────────────────────────────────────────────────────────────────────
def train_departure(agent, num_episodes):
    """
    매 에피소드마다:
    1. 랜덤 상황(time_left, density, margin)을 샘플링
    2. 행동 선택 (epsilon-greedy)
    3. 보상 계산 후 Q 업데이트
    4. time_left를 조금 줄여서 다음 상태로 이동
    """
    MAX_T = 180
    alpha, gamma = agent.alpha, agent.gamma

    for ep in range(num_episodes):
        # epsilon: 처음엔 50% 탐색, 후반엔 5%
        agent.epsilon = max(0.05, 0.5 - (ep / num_episodes) * 0.45)

        # 랜덤 상황 생성
        time_left   = random.randint(5, MAX_T)
        density     = round(random.uniform(0.0, 1.0), 1)
        loc_walk    = random.choice([2, 5, 10, 15, 30])
        flight_stat = random.choices(
            ["NORMAL", "DELAYED"], weights=[0.75, 0.25]
        )[0]
        margin = max(0, time_left - loc_walk)

        state = agent.get_state(
            flight_status=flight_stat,
            time_left=time_left,
            max_time_left=MAX_T,
            current_density=density,
            margin=margin,
        )

        # 행동 선택
        action = agent.select_action(state, time_left=time_left)

        # 다음 상태 (5분 경과 시뮬레이션)
        next_time    = max(0, time_left - 5)
        next_density = round(min(1.0, max(0.0, density + random.uniform(-0.1, 0.1))), 1)
        next_margin  = max(0, next_time - loc_walk)
        next_state   = agent.get_state(
            flight_status=flight_stat,
            time_left=next_time,
            max_time_left=MAX_T,
            current_density=next_density,
            margin=next_margin,
        )

        # 보상 계산
        reward = dep_reward(action, time_left, density, margin)

        # Q-테이블 초기화
        if state not in agent.q_table:
            agent.q_table[state] = [0.0] * 4
        if next_state not in agent.q_table:
            agent.q_table[next_state] = [0.0] * 4

        # Q-Learning 업데이트
        best_next = max(agent.q_table[next_state])
        td_target = reward + gamma * best_next
        td_error  = td_target - agent.q_table[state][action]
        agent.q_table[state][action] += alpha * td_error

    print(f"  [OK] 출국 학습 완료 - 상태 수: {len(agent.q_table):,}")


def train_arrival(agent, num_episodes):
    PHASE_MINS = [5, 25, 15, 5]
    alpha, gamma = agent.alpha, agent.gamma

    for ep in range(num_episodes):
        agent.epsilon = max(0.05, 0.5 - (ep / num_episodes) * 0.45)

        phase   = random.randint(0, 3)
        t_rem   = random.randint(0, sum(PHASE_MINS))
        dist    = random.choice([0, 5, 10, 20])

        state   = agent.get_state(
            passenger_phase=phase,
            time_remaining=t_rem,
            picker_distance=dist,
        )
        action  = agent.select_action(state)

        # 다음 상태 (단계 진행)
        next_phase = min(3, phase + 1)
        next_t_rem = max(0, t_rem - random.randint(5, 20))
        next_state = (
            int(next_phase),
            int(next_t_rem // 5) * 5,
            int(dist // 5) * 5,
        )

        reward = arr_reward(action, phase, t_rem, dist)

        n = 3
        if state not in agent.q_table:
            agent.q_table[state] = [0.0] * n
        if next_state not in agent.q_table:
            agent.q_table[next_state] = [0.0] * n

        best_next = max(agent.q_table[next_state])
        td_error  = (reward + gamma * best_next) - agent.q_table[state][action]
        agent.q_table[state][action] += alpha * td_error

    print(f"  [OK] 입국 학습 완료 - 상태 수: {len(agent.q_table):,}")


# ─────────────────────────────────────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("AI-PORT RL v3 학습 시작\n")

    # ── 출국 ──
    DEP_EP = 30_000
    print(f"[1/2] 출국 에이전트 ({DEP_EP:,} 에피소드)")
    dep = AIPortRLEngine(mode="DEPARTURE")
    dep.q_table = {}     # ★ 기존 q_table.pkl 오염값 무시, 처음부터 학습
    dep.alpha   = 0.20
    dep.gamma   = 0.85
    dep.epsilon = 0.50
    train_departure(dep, DEP_EP)

    # ── 입국 ──
    ARR_EP = 10_000
    print(f"\n[2/2] 입국 에이전트 ({ARR_EP:,} 에피소드)")
    arr = AIPortRLEngine(mode="ARRIVAL")
    arr.q_table = {}     # ★ 이전 오염값 무시
    arr.alpha   = 0.20
    arr.gamma   = 0.85
    arr.epsilon = 0.50
    train_arrival(arr, ARR_EP)

    # ── 저장 ──
    with open(SAVE_PATH, "wb") as f:
        pickle.dump({"departure": dep.q_table, "arrival": arr.q_table}, f)
    print(f"\n[SAVED] {SAVE_PATH}")

    # ── 검증 ──
    dep.epsilon = 0.0
    print("\n[VERIFY] 상황별 추천 행동:")
    tests = [
        {"flight_status":"NORMAL",  "time_left":120,"max_time_left":180,"current_density":0.2,"margin":100, "lbl":"120분, 한산 "},
        {"flight_status":"NORMAL",  "time_left": 60,"max_time_left":180,"current_density":0.6,"margin": 45, "lbl":"60분,  혼잡  "},
        {"flight_status":"NORMAL",  "time_left": 40,"max_time_left":180,"current_density":0.5,"margin": 25, "lbl":"40분,  보통  "},
        {"flight_status":"NORMAL",  "time_left": 15,"max_time_left":180,"current_density":0.9,"margin":  5, "lbl":"15분,  긴급  "},
        {"flight_status":"DELAYED", "time_left": 60,"max_time_left":180,"current_density":0.7,"margin": 40, "lbl":"지연편, 60분 "},
    ]
    print(f"  {'상황':<20} {'추천 행동':<40} {'Q값 [A0 A1 A2 A3]'}")
    print(f"  {'-'*20} {'-'*40} {'-'*30}")
    for t in tests:
        lbl = t.pop("lbl")
        tl  = t.get("time_left", 60)
        s   = dep.get_state(**t)
        a   = dep.select_action(s, time_left=tl)
        q   = dep.q_table.get(s, [0,0,0,0])
        action_short = ACTION_NAMES[a].split("]")[1].strip()[:35]
        print(f"  {lbl:<20} {action_short:<40} {[round(v,1) for v in q]}")

    print("\n[DONE] 앱 재시작 시 자동 적용됩니다.")
