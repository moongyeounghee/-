import pickle
import random
import numpy as np
from dynamic_poi_env import DynamicAIPortEnv, generate_mock_pois

def train_q_learning(episodes=1000000):
    # 1. 환경 초기화
    pois, gates = generate_mock_pois(50, 20)
    env = DynamicAIPortEnv(pois, gates)
    
    q_table = {}
    alpha = 0.1
    gamma = 0.95
    
    print(f"Starting Q-Learning with {episodes} episodes...")
    print(f"- Total POIs: {len(pois)}, Gates: {len(gates)}")
    
    for ep in range(episodes):
        state = env.reset()
        epsilon = max(0.01, 1.0 - ep / (episodes * 0.8)) # 선형 감소 탐색률
        
        while True:
            # 상태 이산화 값이 Q-Table에 없으면 초기화
            if state not in q_table:
                # 모든 노드(POI + Gates)에 대한 Q값 리스트
                q_table[state] = {n["id"]: 0.0 for n in env.all_nodes}
                
            # 에이전트는 가지치기(Pruning)가 완료된 후보군 내에서만 액션을 선택합니다.
            # valid_actions = Time Margin이 음수가 되지 않는(지각하지 않는) 안전한 시설 리스트 + 타겟 게이트
            valid_actions = env.get_valid_actions()
            
            # e-greedy
            if random.random() < epsilon:
                action_id = random.choice(valid_actions)
            else:
                # valid_actions 중에서 가장 Q값이 높은 액션 선택
                best_action = None
                best_q = -float('inf')
                for a_id in valid_actions:
                    val = q_table[state][a_id]
                    if val > best_q:
                        best_q = val
                        best_action = a_id
                action_id = best_action
                
            next_state, reward, done = env.step(action_id)
            
            # 다음 상태 공간 초기화
            if next_state not in q_table:
                q_table[next_state] = {n["id"]: 0.0 for n in env.all_nodes}
                
            # Bellman 업데이트
            best_next_q = max([q_table[next_state][a] for a in env.get_valid_actions()]) if not done else 0.0
            
            # TD Error
            td_target = reward + gamma * best_next_q
            td_error = td_target - q_table[state][action_id]
            q_table[state][action_id] += alpha * td_error
            
            state = next_state
            
            if done:
                break
                
        if (ep + 1) % 10000 == 0:
            print(f"Episode {ep+1}/{episodes} | Epsilon: {epsilon:.2f} | Unique States in Q-Table: {len(q_table)}")
            
    # 학습된 Q-Table 및 환경 맵 데이터 로컬 저장
    with open("dynamic_q_table.pkl", "wb") as f:
        pickle.dump(q_table, f)
    with open("dynamic_env_data.pkl", "wb") as f:
        pickle.dump({"pois": pois, "gates": gates}, f)
        
    print(f"Training Complete! Total States learned: {len(q_table)}")
    return q_table, env

def evaluate_model(q_table, env):
    print("\n--- Model Evaluation (Greedy Run) ---")
    state = env.reset()
    print(f"Start Scenario:")
    print(f"  Target Gate: {env.target_gate['id']}")
    print(f"  Time Margin: {env.time_margin:.1f} minutes")
    
    total_reward = 0
    steps = 0
    
    while True:
        valid_actions = env.get_valid_actions()
        best_action = None
        best_q = -float('inf')
        
        # OOV 엣지 케이스 대처
        if state not in q_table:
            best_action = random.choice(valid_actions)
        else:
            for a_id in valid_actions:
                val = q_table[state][a_id]
                if val > best_q:
                    best_q = val
                    best_action = a_id
                    
        next_state, reward, done = env.step(best_action)
        total_reward += reward
        steps += 1
        
        if env.node_dict[best_action]["type"] == "GATE":
            print(f"Step {steps}: Arrived at GATE {best_action}")
            print(f"  -> Margin remaining: {env.time_margin:.1f} mins (Target JIT: 30 mins) | Reward: {reward:.1f}")
            break
        else:
            poi_info = env.node_dict[best_action]
            print(f"Step {steps}: Visited POI {best_action} (Category: {poi_info['category']})")
            print(f"  -> Margin remaining: {env.time_margin:.1f} mins | Reward: {reward:.1f}")
            
        state = next_state
        
    print(f"Total Episodic Reward: {total_reward:.1f}")

if __name__ == "__main__":
    trained_q, sample_env = train_q_learning(episodes=10000000)
    evaluate_model(trained_q, sample_env)
