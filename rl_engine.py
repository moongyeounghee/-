import math
import random
import pickle
import os
import numpy as np

# --- 통합 행동 공간 (Action Space) 정의 ---
# [출국 행동 (DEPARTURE)] 
DEP_ACTION_0 = 0  # [초록] 잉여 시간 활용 권장 (면세점/라운지 10~20분 체류)
DEP_ACTION_1 = 1  # [노랑] 전략적 대기 (혼잡 구간 진입 전 5분간 인근에서 대기)
DEP_ACTION_2 = 2  # [빨강] 표준 속도 이동 (현재 경로를 따라 탑승구로 즉시 직행)
DEP_ACTION_3 = 3  # [빨강] 우회 이동 (돌발 혼잡도를 피해 다른 검색대나 우회로 이용)

ACTION_NAMES = {
    DEP_ACTION_0: "[초록] 잉여 시간 활용 권장 (면세점/라운지 10~20분)",
    DEP_ACTION_1: "[노랑] 전략적 대기 (인근 5분 휴식)",
    DEP_ACTION_2: "[빨강] 표준 속도 이동 (즉각 탑승구로 직행)",
    DEP_ACTION_3: "[빨강] 돌발 혼잡 회피! 우회 이동"
}

# [입국 맞이 행동 (ARRIVAL)]
ARR_ACTION_0 = 0 # [초록] 현 위치 대기 (카페, 주차장 등에서 휴식 - 피로도 최소화)
ARR_ACTION_1 = 1 # [노랑] 게이트 근처로 서서히 이동 시작
ARR_ACTION_2 = 2 # [빨강] 출구(게이트) 앞 도착 및 대기 (승객 맞이 준비)


class AIPortRLEngine:
    """
    Antigravity RL Configuration 기반 여객 스마트 가이드 SARSA/Q-Learning 통합 엔진
     mode="DEPARTURE": 출국자 탑승 최적화 가이드 엔진
     mode="ARRIVAL": 입국자 지인(맞이객) 마중 최적화 가이드 엔진
    """
    def __init__(self, mode="DEPARTURE", gender="M"):
        self.mode = mode.upper()
        
        # RL 공통 하이퍼파라미터
        self.gamma = 0.98 if self.mode == "DEPARTURE" else 0.95
        self.alpha = 0.05 if self.mode == "DEPARTURE" else 0.1
        self.epsilon = 0.0  # 추론 시에는 탐색 끄기

        # 사전학습된 Q-테이블 로드
        self.q_table = self._load_q_table()
        
        # 출국 모드(DEPARTURE) 전용 초기화
        if self.mode == "DEPARTURE":
            self.gender = gender.upper()
            if self.gender == "M":
                self.m_index_std = 1.34  # 남성 평균 m/s
            else:
                self.m_index_std = 1.27  # 여성 평균 m/s

    # ----------------------------------------------------
    # 0. Q-테이블 로드/저장
    # ----------------------------------------------------
    def _load_q_table(self, path="q_table.pkl"):
        """사전학습된 Q-테이블을 로드. 없으면 빈 테이블 반환."""
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                key = "departure" if self.mode == "DEPARTURE" else "arrival"
                table = data.get(key, {})
                return table
            except Exception:
                pass
        return {}

    def save_q_table(self, path="q_table.pkl"):
        """현재 Q-테이블을 저장."""
        existing = {}
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    existing = pickle.load(f)
            except Exception:
                pass
        key = "departure" if self.mode == "DEPARTURE" else "arrival"
        existing[key] = self.q_table
        with open(path, "wb") as f:
            pickle.dump(existing, f)

    # ----------------------------------------------------
    # 1. State (상태 변환기)
    # ----------------------------------------------------
    def get_state(self, **kwargs):
        if self.mode == "DEPARTURE":
            return self._get_departure_state(**kwargs)
        else:
            return self._get_arrival_state(**kwargs)
            
    def _get_departure_state(self, flight_status, time_left, max_time_left, current_density, margin):
        if flight_status == "NORMAL": f_status_idx = 1.0
        elif flight_status == "DELAYED": f_status_idx = 0.5
        elif flight_status == "CANCELLED": f_status_idx = 0.0
        else: f_status_idx = 1.0
            
        t_ratio = time_left / max_time_left if max_time_left > 0 else 0.0
        safety_margin = margin - 15  
        
        return (
            round(f_status_idx, 1), 
            round(t_ratio, 1), 
            round(current_density, 1), 
            round(safety_margin, 0)
        )
        
    def _get_arrival_state(self, passenger_phase, time_remaining, picker_distance):
        p_phase = int(passenger_phase) 
        t_rem = int(max(0, time_remaining) // 5) * 5
        dist = int(max(0, picker_distance) // 5) * 5
        return (p_phase, t_rem, dist)

    # ----------------------------------------------------
    # 2. Reward (보상 함수)
    # ----------------------------------------------------
    def calculate_reward(self, action, next_state):
        if self.mode == "DEPARTURE":
            return self._calc_departure_reward(action, next_state)
        else:
            return self._calc_arrival_reward(action, next_state)

    def _calc_departure_reward(self, action, next_state_dict):
        reward = 0
        margin = next_state_dict.get('margin', 0)
        is_congested = next_state_dict.get('is_congested', False)
        at_gate = next_state_dict.get('at_gate', False)
        
        if margin < 15:
            reward -= math.exp(15 - margin) * 10 
        if at_gate:
            reward += 100 
            
        if action == DEP_ACTION_0 and margin > 20:
            reward += 15  
        elif action == DEP_ACTION_1 and is_congested:
            reward += 10  
        if action == DEP_ACTION_1 and not is_congested:
            reward -= 5   
            
        return reward
        
    def _calc_arrival_reward(self, action, next_state_tuple):
        p_phase, t_rem, dist = next_state_tuple
        reward = 0
        
        if p_phase == 3 and dist <= 5 and action == ARR_ACTION_2:
            reward += 100
        if p_phase <= 1 and action == ARR_ACTION_2:
            reward -= 20
        if p_phase >= 2 and t_rem < dist:
            reward -= 50
        if p_phase >= 1 and t_rem <= dist + 10 and action == ARR_ACTION_1:
            reward += 15 
            
        return reward

    # ----------------------------------------------------
    # 3. Action (행동 선택)
    # ----------------------------------------------------
    def select_action(self, state, **kwargs):
        if self.mode == "DEPARTURE":
            return self._select_departure_action(state, kwargs.get('time_left', 0))
        else:
            return self._select_arrival_action(state)

    def _select_departure_action(self, state, time_left):
        current_epsilon = 0.0 if time_left <= 30 else self.epsilon
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]

        q_vals = self.q_table[state]

        # ★ 미학습 상태(Q값 전부 0)이면 실제 항공 기준 기반 fallback
        # | 국제선 기준
        # | 60분~  : 체크인 마감 전  → 쇼핑 가능, 게이트 기준으로 이동 준비
        # | 30~60분 : 게이트 마감 30분전 → 슬슬 이동 시작
        # | 15~30분 : 게이트 마감 15분전 → 즉시 이동
        # |   ~15분 : 긴급 (탑승 불가 위험)  → 우회 구간 피해 즉시 달려가세요
        if max(q_vals) == 0.0 and min(q_vals) == 0.0:
            if time_left >= 60:
                return DEP_ACTION_0   # 면세점/라운지 권장 (취타 큰다 여유)
            elif time_left >= 30:
                return DEP_ACTION_1   # 전략적 대기 후 이동 (게이트 마감 30분전)
            elif time_left >= 15:
                return DEP_ACTION_2   # 즉시 이동 (게이트 마감 15분전)
            else:
                return DEP_ACTION_3   # 긴급: 혼잡 우회하며 바로 달려가세요!


        if random.uniform(0, 1) < current_epsilon:
            return random.choice([DEP_ACTION_0, DEP_ACTION_1, DEP_ACTION_2, DEP_ACTION_3])
        else:
            return int(np.argmax(q_vals))

    def _select_arrival_action(self, state):
        p_phase, t_rem, dist = state
        if p_phase == 0 or p_phase == 1:
            if t_rem > dist + 10:
                return ARR_ACTION_0 
            else:
                return ARR_ACTION_1  
        elif p_phase == 2:
            if t_rem <= dist + 5:
                return ARR_ACTION_1 if dist > 0 else ARR_ACTION_2
            elif dist <= 5:
                return ARR_ACTION_2
            else:
                return ARR_ACTION_1
        elif p_phase == 3:
            return ARR_ACTION_2  
            
        return ARR_ACTION_0


# =========================================================
# 간단한 통합 테스트 로직
# =========================================================
if __name__ == "__main__":
    print("🚀 [Antigravity 통합 RL Engine] 초기화 중...")
    
    # 1. 출국자 모드 테스트
    dep_agent = AIPortRLEngine(mode="DEPARTURE", gender="M")
    dep_state = dep_agent.get_state(flight_status="NORMAL", time_left=50, max_time_left=120, current_density=0.8, margin=35)
    dep_action = dep_agent.select_action(dep_state, time_left=50)
    print(f"[출국장] 추천 행동 (마진 넉넉): {ACTION_NAMES[dep_action]}")
    
    # 2. 입국 맞이객 모드 테스트
    arr_agent = AIPortRLEngine(mode="ARRIVAL")
    arr_state = arr_agent.get_state(passenger_phase=1, time_remaining=35, picker_distance=10)
    arr_action = arr_agent.select_action(arr_state)
    print(f"[입국장] 심사 중(35분 남음), 주차장(10분 거리) 시 추천 행동 ID: {arr_action} (0=휴식, 1=이동, 2=게이트도착)")
