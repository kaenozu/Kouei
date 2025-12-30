import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_PATH = "data/race_data.db"

class DatabaseData:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = None
        self.init_db()

    def get_conn(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def init_db(self):
        conn = self.get_conn()
        cur = conn.cursor()
        
        # Races Table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS races (
                race_id TEXT PRIMARY KEY,
                date TEXT,
                jyo_cd TEXT,
                race_no INTEGER,
                race_name TEXT,
                start_time TEXT,
                weather TEXT,
                wind_direction TEXT,
                wind_speed REAL,
                temperature REAL,
                water_temperature REAL,
                wave_height REAL
            )
        ''')
        
        # Boats Table (Racers info per race)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS race_entries (
                entry_id TEXT PRIMARY KEY, -- race_id + boat_no
                race_id TEXT,
                boat_no INTEGER,
                racer_id TEXT,
                racer_name TEXT,
                racer_rank TEXT,
                motor_no TEXT,
                motor_2ren REAL,
                boat_no_machine TEXT, 
                boat_2ren REAL,
                result_rank INTEGER,
                exhibition_time REAL,
                start_time_result REAL,
                FOREIGN KEY(race_id) REFERENCES races(race_id)
            )
        ''')
        
        # Odds Table (Simplified: just storing JSON blobs or key summaries if complex)
        # For querying speed, we might want separated tables, but for now JSON is flexible
        cur.execute('''
            CREATE TABLE IF NOT EXISTS race_odds (
                race_id TEXT PRIMARY KEY,
                odds_json TEXT,
                updated_at TEXT
            )
        ''')

        # Create Indexes for Performance
        cur.execute('CREATE INDEX IF NOT EXISTS idx_races_date ON races(date)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_races_jyo_race ON races(jyo_cd, race_no)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_entries_racer ON race_entries(racer_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_entries_race ON race_entries(race_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_entries_motor ON race_entries(motor_no)')

        conn.commit()
        print("✅ Database indexes created")

    def save_races_df(self, df):
        """Save standard race dataframe to DB"""
        conn = self.get_conn()
        # df usually acts as a flat table. We need to split into races and entries.
        
        # Iterate or bulk insert? efficiency matters.
        # Let's use pandas to_sql if processed df matches schema.
        # But our df is denormalized.
        
        # 1. Races (Unique)
        if 'race_id' not in df.columns:
            # Construct race_id: YYYYMMDD_JJ_RR
            df['race_id'] = df['date'].astype(str) + '_' + df['jyo_cd'].astype(str).str.zfill(2) + '_' + df['race_no'].astype(str)
            
        races_cols = ['race_id', 'date', 'jyo_cd', 'race_no', 'race_name', 'start_time', 'weather', 'wind_direction', 'wind_speed', 'temperature', 'water_temperature', 'wave_height']
        existing_cols = [c for c in races_cols if c in df.columns]
        
        races_df = df[existing_cols].drop_duplicates(subset=['race_id'])
        # Upsert logic is hard in pure pandas.
        # We'll stick to 'append' and ignore errors or doing manual loop for safety.
        # For speed: using pure SQL REPLACE INTO
        
        data_tuples = []
        for _, row in races_df.iterrows():
            data_tuples.append(tuple(row.get(c, None) for c in races_cols))
            
        columns_str = ', '.join(races_cols)
        placeholders = ', '.join(['?'] * len(races_cols))
        
        cur = conn.cursor()
        cur.executemany(f"REPLACE INTO races ({columns_str}) VALUES ({placeholders})", data_tuples)
        
        # 2. Entries
        # entry_id = race_id + '_' + boat_no
        df['entry_id'] = df['race_id'] + '_' + df['boat_no'].astype(str)
        
        entries_cols = ['entry_id', 'race_id', 'boat_no', 'racer_id', 'racer_name', 'racer_rank', 'motor_no', 'motor_2ren', 'boat_no_machine', 'boat_2ren', 'result_rank', 'exhibition_time', 'start_time_result']
        # Map some columns from df if names differ
        # df usually has 'rank' for result_rank
        df['result_rank'] = df['rank'] if 'rank' in df.columns else None
        
        entries_exist = [c for c in entries_cols if c in df.columns]
        entries_df = df[entries_exist].drop_duplicates(subset=['entry_id'])
        
        et_data = []
        for _, row in entries_df.iterrows():
            et_data.append(tuple(row.get(c, None) for c in entries_cols))
            
        e_cols_str = ', '.join(entries_cols)
        e_ph = ', '.join(['?'] * len(entries_cols))
        
        cur.executemany(f"REPLACE INTO race_entries ({e_cols_str}) VALUES ({e_ph})", et_data)
        
        conn.commit()
        print(f"Saved {len(races_df)} races and {len(entries_df)} entries to DB.")

    def load_df(self):
        """Load flattened DF for ML"""
        query = '''
            SELECT r.*, e.* 
            FROM race_entries e
            JOIN races r ON e.race_id = r.race_id
        '''
        return pd.read_sql(query, self.get_conn())

if __name__ == "__main__":
    db = DatabaseData()
    print("Database Initialized")
