import math
import random
import pickle
import numpy as np
import time

# ==========================================
# 1. Physics Engine Constants (물리 엔진)
# ==========================================
V_USER = 1.34  # m/s (182cm/78kg 남성 보행 속도 기준)
DISTANCE_MULTIPLIER = 20.0  # 단위 거리(1)당 실제 20m
MAX_TIME_BUDGET = 780  # 에피소드 최대 마진 시간 (13시간 * 60분)

def calc_travel_time(x1, y1, x2, y2, t1="T1", t2="T1"):
    """
    Antigravity 물리 엔진 (직선 거리 단순화 + 셔틀 트레인 패널티)
    """
    euclidean_dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    time_min = (euclidean_dist * DISTANCE_MULTIPLIER) / (V_USER * 60)
    
    # 셔틀 트레인 (T1 <-> CONCOURSE 구간 이동 시 +15분 고정 패널티)
    if t1 != t2 and ("CONCOURSE" in [t1, t2]):
        time_min += 10.0
        
    return round(time_min, 1)

# ==========================================
# 2. Dynamic Data Layer (모의 API 데이터셋)
# ==========================================
CATEGORIES = {
    "SHOPPING": {"base_reward": 100, "min_stay": 20},
    "FOOD":     {"base_reward": 150, "min_stay": 40},
    "CAFE":     {"base_reward": 80,  "min_stay": 15},
    "LOUNGE":   {"base_reward": 200, "min_stay": 60},
}

def generate_mock_pois(num_pois=50, num_gates=20):
    pois = []
    for i in range(num_pois):
        cat = random.choice(list(CATEGORIES.keys()))
        term = random.choice(["T1", "T2", "CONCOURSE"])
        pois.append({
            "id": f"POI_{i}",
            "type": "FACILITY",
            "category": cat,
            "terminal_id": term,
            "x": random.randint(0, 50),
            "y": random.randint(0, 30),
            "base_reward": CATEGORIES[cat]["base_reward"],
            "min_stay": CATEGORIES[cat]["min_stay"]
        })
    gates = []
    for i in range(num_gates):
        term = random.choice(["T1", "T2", "CONCOURSE"])
        gates.append({
            "id": f"GATE_{100+i}",
            "type": "GATE",
            "category": "GATE",
            "terminal_id": term,
            "x": random.randint(10, 50),
            "y": random.randint(10, 30),
            "base_reward": 0,
            "min_stay": 0
        })
    return pois, gates

# ==========================================
# 3. Environment (강화학습 환경)
# ==========================================
class DynamicAIPortEnv:
    def __init__(self, pois, gates):
        self.pois = pois
        self.gates = gates
        self.all_nodes = pois + gates
        self.node_dict = {n["id"]: n for n in self.all_nodes}
        self.reset()
        
    def reset(self):
        self.target_gate = random.choice(self.gates)
        
        t_gate = self.target_gate.get("terminal_id", "T1")
        # 탑승동(CONCOURSE) 승객은 물리적으로 T1에서 체크인 후 여정을 시작함
        start_term = "T1" if t_gate == "CONCOURSE" else t_gate
        valid_starts = [p for p in self.pois if p.get("terminal_id") == start_term]
        
        start_node = random.choice(valid_starts) if valid_starts else random.choice(self.pois)
        self.current_node_id = start_node["id"]
        
        self.time_margin = random.uniform(60, MAX_TIME_BUDGET)
        
        self.dynamic_state = {}
        for n in self.pois:
            self.dynamic_state[n["id"]] = {
                "congestion": round(random.uniform(0.0, 0.9), 2),
                "is_open": random.random() > 0.1
            }
            
        self.meta = {"SHOPPING": 0, "FOOD": 0, "CAFE": 0, "LOUNGE": 0}
        self.visited = set([self.current_node_id])
        return self._get_state()
        
    def _get_state(self):
        curr = self.node_dict[self.current_node_id]
        x_d = int(curr["x"])
        y_d = int(curr["y"])
        
        travel_to_gate = calc_travel_time(
            curr["x"], curr["y"], self.target_gate["x"], self.target_gate["y"], 
            curr.get("terminal_id"), self.target_gate.get("terminal_id")
        )
        net_margin = self.time_margin - travel_to_gate
        
        margin_d = round(net_margin * 2) / 2.0
        margin_d = max(-20.0, min(720.0, margin_d)) 
        
        meta_s = self.meta["SHOPPING"] > 0
        meta_f = self.meta["FOOD"] > 0
        meta_c = self.meta["CAFE"] > 0
        meta_l = self.meta["LOUNGE"] > 0
        
        return (x_d, y_d, margin_d, meta_s, meta_f, meta_c, meta_l)
        
    def get_valid_actions(self):
        # 라운지 블랙홀: 이미 라운지에 들어갔다면 다른 시설 방문 불가, 게이트 직행만 허용
        if self.meta["LOUNGE"] > 0:
            return [self.target_gate["id"]]
            
        curr = self.node_dict[self.current_node_id]
        valid_actions = []
        
        for poi in self.pois:
            if poi["id"] in self.visited:
                continue
            if not self.dynamic_state[poi["id"]]["is_open"]:
                continue
                
            t_poi = poi.get("terminal_id", "T1")
            t_gate = self.target_gate.get("terminal_id", "T1")
            t_curr = curr.get("terminal_id", "T1")
            
            # 터미널 분리 및 탑승동 일방통행 제약
            if t_gate == "T2" and t_poi != "T2":
                continue
            if t_gate == "T1" and t_poi != "T1":
                continue
            if t_gate == "CONCOURSE":
                if t_poi not in ["T1", "CONCOURSE"]:
                    continue
                # 한번 T1에서 CONCOURSE로 넘어갔다면 다시 T1 시설 방문 불가
                if t_curr == "CONCOURSE" and t_poi == "T1":
                    continue
                
            t_move = calc_travel_time(curr["x"], curr["y"], poi["x"], poi["y"], t_curr, t_poi)
            t_stay = poi["min_stay"]
            t_to_gate = calc_travel_time(poi["x"], poi["y"], self.target_gate["x"], self.target_gate["y"], t_poi, t_gate)
            
            expected_margin = self.time_margin - (t_move + t_stay + t_to_gate)
            if expected_margin >= 0:
                valid_actions.append(poi["id"])
                
        valid_actions.append(self.target_gate["id"])
        return valid_actions

    def step(self, action_id):
        curr = self.node_dict[self.current_node_id]
        target = self.node_dict[action_id]
        
        t_move = calc_travel_time(
            curr["x"], curr["y"], target["x"], target["y"], 
            curr.get("terminal_id"), target.get("terminal_id")
        )
        
        reward = 0
        done = False
        
        if target["type"] == "GATE":
            self.time_margin -= t_move
            offset = max(0.0, abs(self.time_margin - 30.0) - 5.0) 
            
            if self.time_margin < -5:
                reward = -50000
            else:
                reward = 10000 - (offset * 500)
            
            self.current_node_id = target["id"]
            done = True
            
        else:
            if target["category"] == "LOUNGE":
                # 라운지 블랙홀 시간 흡수 로직
                t_to_gate = calc_travel_time(
                    target["x"], target["y"], self.target_gate["x"], self.target_gate["y"], 
                    target.get("terminal_id"), self.target_gate.get("terminal_id")
                )
                max_stay = self.time_margin - t_move - t_to_gate - 30.0
                t_stay = min(180.0, max(target["min_stay"], max_stay))
            else:
                t_stay = target["min_stay"]
                
            self.time_margin -= (t_move + t_stay)
            
            congestion = self.dynamic_state[target["id"]]["congestion"]
            poi_val = target["base_reward"]
            cat = target["category"]
            
            reward_stay = (poi_val * (1 - congestion)) / (t_stay ** 0.5) * 10
            
            if self.meta[cat] > 0:
                if cat in ["FOOD", "LOUNGE"]:
                    reward_stay *= 0.1
                else:
                    reward_stay *= (0.5 ** self.meta[cat])
                    
            if self.time_margin < 40:
                reward_stay *= 0.1
                
            self.meta[cat] += 1
            reward += reward_stay
            self.current_node_id = target["id"]
            self.visited.add(target["id"])
            
        next_state = self._get_state()
        return next_state, reward, done
