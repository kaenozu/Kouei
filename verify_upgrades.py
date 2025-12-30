import sys
import os
import pandas as pd
import random
sys.path.append(os.getcwd())

from src.inference.commentary import CommentaryGenerator
from src.model.rl_agent import SimpleRLAgent, train_rl_agent
from src.db.database import DatabaseData

def verify_all():
    print("--- Verifying Updates ---")
    
    # 1. DB
    print("[1/3] Checking Database...")
    db = DatabaseData()
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM races")
    count = cur.fetchone()[0]
    print(f"DB Race Count: {count}")
    
    # 2. GenAI
    print("[2/3] Checking Commentary...")
    gen = CommentaryGenerator()
    # Mock data
    row = {
        'boat_no': 1, 'racer_name': 'Test Racer', 'motor_no': '10', 
        'motor_2ren': 45.5, 'exhibition_time': 6.75, 'racer_win_rate': 7.0,
        'wind_speed': 5
    }
    comment = gen.generate(row, 1)
    print(f"Generated Comment: {comment}")
    
    # 3. RL
    print("[3/3] Checking RL Agent...")
    # Create tiny dummy DF
    data = []
    for i in range(10):
        data.append({
            'date': '20250101', 'jyo_cd': '01', 'race_no': i+1,
            'boat_no': 1, 'racer_rank': 'A1', 'wind_speed': 3 if i%2==0 else 6,
            'rank': 1 if i%3==0 else 4, 'tansho': 150
        })
    df = pd.DataFrame(data)
    agent = train_rl_agent(df)
    print(f"Agent trained. Q-Table Size: {len(agent.q_table)}")

if __name__ == "__main__":
    verify_all()
