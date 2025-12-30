import json
import os
import uuid
from datetime import datetime

PORTFOLIO_PATH = "data/portfolio.json"

class PortfolioLedger:
    def __init__(self):
        self.load()
    
    def load(self):
        if os.path.exists(PORTFOLIO_PATH):
            try:
                with open(PORTFOLIO_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.balance = data.get("balance", 100000) # Start with 100k yen
                    self.transactions = data.get("transactions", [])
                    self.history = data.get("history", []) # Daily snapshots
            except:
                self.balance = 100000
                self.transactions = []
                self.history = []
        else:
            self.balance = 100000
            self.transactions = []
            self.history = []

    def save(self):
        os.makedirs("data", exist_ok=True)
        data = {
            "balance": self.balance,
            "transactions": self.transactions,
            "history": self.history
        }
        with open(PORTFOLIO_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def record_bet(self, strategy_name, race_id, amount, bet_type, combo, odds):
        # Prevent duplicate betting for same race/strategy/combo
        for t in self.transactions:
            if t['race_id'] == race_id and t['combo'] == combo and t['strategy'] == strategy_name:
                return # Already bet

        tx = {
            "id": str(uuid.uuid4()),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategy": strategy_name,
            "race_id": race_id,
            "type": "bet",
            "bet_type": bet_type, # 'tansho', '2ren', '3ren'
            "combo": combo,
            "amount": amount,
            "odds_at_purchase": odds,
            "status": "pending", # pending, win, lose
            "return_amount": 0
        }
        
        self.balance -= amount
        self.transactions.append(tx)
        self.save()
        print(f"Recorded bet: {combo} ({amount}yen) for {strategy_name}")

    def update_results(self, race_df):
        # race_df should have 'race_no', 'jyo_cd', 'rank', 'date'
        # We need to construct race_id key from df rows? 
        # Or better, we iterate pending transactions and check if this df contains the result.
        
        pending_txs = [t for t in self.transactions if t['status'] == 'pending']
        if not pending_txs:
            return

        # Pre-process race_df to match race_id
        # Our race_id format from main_api: STRAT_{timestamp}_{jyo}_{race} ? 
        # Actually in main_api we generated `strat_race_key`, but `race_id` passed to ledger 
        # should probably be simpler: "{date}_{jyo}_{race}"
        
        # Let's assume passed race_id is "{date}_{jyo}_{race}" (e.g. 20251230_05_11)
        
        for tx in pending_txs:
            # Check if this tx's race is in the updated data
            # tx['race_id'] e.g. "20251230_05_12"
            
            # Filter df
            try:
                # Parse ID
                date_str, jyo_str, race_no_str = tx['race_id'].split('_')
                
                # Find race in df
                # ensure df types match
                matches = race_df[
                    (race_df['date'].astype(str) == date_str) &
                    (race_df['jyo_cd'].astype(str).str.zfill(2) == jyo_str) &
                    (race_df['race_no'].astype(str) == race_no_str)
                ]
                
                if matches.empty:
                    continue
                
                # Check result
                # We need the rank of boats.
                # 'combo' is like "1-2"
                
                # Parse combo
                picks = [int(p) for p in tx['combo'].split('-')]
                
                # Get actual result ranks
                # We need to find which boat came 1st, 2nd, 3rd
                
                ranks = {} # boat -> rank
                for _, row in matches.iterrows():
                    if pd.notna(row['rank']):
                         ranks[int(row['boat_no'])] = int(row['rank'])
                
                # Check if we have complete results (1,2,3)
                if 1 not in ranks.values():
                    continue # Not finished?
                
                # Judge Win
                won = False
                
                if tx['bet_type'] == 'tansho': # Win
                    if ranks.get(picks[0]) == 1: won = True
                
                elif tx['bet_type'] == 'nirentan': # Exact 1-2
                    if ranks.get(picks[0]) == 1 and ranks.get(picks[1]) == 2: won = True

                elif tx['bet_type'] == 'sanrentan': # Exact 1-2-3
                     if ranks.get(picks[0]) == 1 and ranks.get(picks[1]) == 2 and ranks.get(picks[2]) == 3: won = True
                
                if won:
                    # Return Amount = Amount * Odds
                    # Use the stored purchase odds (simplified) 
                    # OR use actual result dividend if we had it. 
                    # For simulation, Purchase Odds is fair 'Paper Trading' assumption unless odds crashed.
                    ret = int(tx['amount'] * tx['odds_at_purchase'])
                    tx['status'] = 'win'
                    tx['return_amount'] = ret
                    self.balance += ret
                    print(f"Win! {tx['combo']} +{ret}")
                else:
                    # Lose logic: Are results fully finalized? 
                    # If we have Rank 1, 2, 3, and ours isn't it, we lost.
                    # (Unless dead heat or disqualification logic, ignoring for now)
                    
                    # Ensure top 2/3 decided
                    required_ranks = 2 if 'nirentan' in tx['bet_type'] else 3
                    found_ranks = len([r for r in ranks.values() if r <= required_ranks])
                    
                    if found_ranks >= required_ranks:
                         tx['status'] = 'lose'
                         tx['return_amount'] = 0
                         print(f"Lose: {tx['combo']}")

            except Exception as e:
                print(f"Error checking tx {tx['id']}: {e}")
        
        self.save()

    def get_summary(self):
        # Calc Stats
        total_bets = len(self.transactions)
        wins = len([t for t in self.transactions if t['status'] == 'win'])
        invested = sum([t['amount'] for t in self.transactions])
        returned = sum([t.get('return_amount', 0) for t in self.transactions])
        
        roi = (returned / invested * 100) if invested > 0 else 0
        
        return {
            "balance": self.balance,
            "total_bets": total_bets,
            "wins": wins,
            "win_rate": (wins/total_bets*100) if total_bets > 0 else 0,
            "invested": invested,
            "returned": returned,
            "roi": roi,
            "transactions": self.transactions[-50:] # Last 50 for UI
        }
