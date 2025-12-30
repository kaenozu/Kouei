import numpy as np
import pandas as pd
import random
import os
import json

# Actions: 0=Skip, 1=Bet Boat1, 2=Bet Boat2 ... 6=Bet Boat6
ACTIONS = [0, 1, 2, 3, 4, 5, 6]

class SimpleRLAgent:
    def __init__(self, learning_rate=0.1, discount_factor=0.95, exploration_rate=1.0, exploration_decay=0.995):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.epsilon_decay = exploration_decay
        self.q_table = {} # State (Hash) -> Q-Values [q0, q1...q6]
        self.model_path = "models/rl_qtable.json"
        
        self.load()

    def get_state_key(self, row):
        # Discretize state to reduce space
        # Factors: Jyo, Boat1 Rank (A/B), Wind (Low/High)
        jyo = row['jyo_cd']
        # Simplified: Is Boat 1 A1?
        b1_rank = 1 if row.get('racer_rank', 'B1') == 'A1' else 0
        wind = 1 if row.get('wind_speed', 0) >= 5 else 0
        
        return f"{jyo}_{b1_rank}_{wind}"

    def choose_action(self, state_key):
        if random.random() < self.epsilon:
            return random.choice(ACTIONS)
        
        if state_key not in self.q_table:
            return 0 # Default Skip
        
        return np.argmax(self.q_table[state_key])

    def learn(self, state, action, reward, next_state):
        if state not in self.q_table:
            self.q_table[state] = np.zeros(len(ACTIONS))
        
        if next_state not in self.q_table:
            self.q_table[next_state] = np.zeros(len(ACTIONS))
            
        predict = self.q_table[state][action]
        target = reward + self.gamma * np.max(self.q_table[next_state])
        self.q_table[state][action] += self.lr * (target - predict)

    def save(self):
        # Convert numpy to list
        save_data = {k: v.tolist() for k, v in self.q_table.items()}
        with open(self.model_path, 'w') as f:
            json.dump(save_data, f)

    def load(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'r') as f:
                    data = json.load(f)
                    self.q_table = {k: np.array(v) for k, v in data.items()}
            except:
                pass

def train_rl_agent(df):
    agent = SimpleRLAgent()
    print("Training RL Agent...")
    
    # Sort by date
    df = df.sort_values('date')
    
    # Iterate races
    # Need to group by race_id to get full picture?
    # RL usually needs sequential interaction. 
    # Simplified: Iterate row by row (Boat 1 view)
    
    current_balance = 0
    
    # Group by race for context
    # Assuming df has 'race_id'
    if 'race_id' not in df.columns:
        df['race_id'] = df['date'].astype(str) + '_' + df['race_no'].astype(str) # simplified

    for race_id, group in df.groupby('race_id'):
        # Just use Boat 1's row as "Race State" representative
        row = group.iloc[0]
        state = agent.get_state_key(row)
        
        # Decide
        action = agent.choose_action(state)
        
        # Act & Observe Reward
        reward = 0
        if action == 0:
            reward = 0 # No bet
        else:
            # Bet on Boat X (Action 1-6)
            bet_boat = action
            # Did it win?
            winner = group[group['rank'] == 1]
            if not winner.empty and winner.iloc[0]['boat_no'] == bet_boat:
                # Won!
                # Reward = Payout - 100
                # Use 'tansho' column if available, else approx 150*odds
                payout = winner.iloc[0].get('tansho', 150) # default assumption
                reward = payout - 100
            else:
                # Lost
                reward = -100
        
        # Update
        # Next state is effectively independent in independent races, 
        # but for Q-learning we treat the sequence of races as the episode or reliable stream.
        # We can just update Q(s,a) towards Reward (gamma=0 for independent)
        agent.learn(state, action, reward, state) # Next state matterless if gamma=0
        
        agent.epsilon *= agent.epsilon_decay
        
    agent.save()
    print("RL Training Complete.")
    return agent
