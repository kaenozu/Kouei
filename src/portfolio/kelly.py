"""
Kelly Criterion - Optimal Bet Sizing Logic
Calculates the fraction of bankroll to wager to maximize long-term growth.
Formula: f* = (bp - q) / b = (p(b+1) - 1) / b
where:
f* is the fraction of the bankroll to wager
b is the decimal odds - 1 (net odds)
p is the probability of winning
q is the probability of losing (1-p)
"""

def calculate_kelly_fraction(probability, odds, fractional_kelly=0.5):
    """
    Calculate the Kelly fraction.
    
    Args:
        probability (float): Win probability (0.0 to 1.0)
        odds (float): Decimal odds (e.g., 2.5)
        fractional_kelly (float): Risk management multiplier (default 0.5 for Half-Kelly)
        
    Returns:
        float: Fraction of bankroll to wager (0.0 to 1.0)
    """
    if odds <= 1.0 or probability <= 0:
        return 0.0
    
    # b is net odds
    b = odds - 1.0
    p = probability
    q = 1.0 - p
    
    # Kelly Formula
    f_star = (b * p - q) / b
    
    # Negative Kelly means no bet
    if f_star <= 0:
        return 0.0
    
    # Apply fractional Kelly for safety
    return f_star * fractional_kelly

def get_recommended_bet(bankroll, probability, odds, min_bet=100, max_bet_pct=0.1):
    """
    Get recommended bet amount in Yen.
    
    Args:
        bankroll (int): Current bankroll
        probability (float): Win probability
        odds (float): Decimal odds
        min_bet (int): Minimum bet unit (default 100)
        max_bet_pct (float): Maximum allowed % of bankroll for a single bet
        
    Returns:
        int: Recommended bet amount (rounded to 100s)
    """
    f = calculate_kelly_fraction(probability, odds)
    
    # Cap the bet percentage
    f = min(f, max_bet_pct)
    
    bet_amount = bankroll * f
    
    # Round to nearest 100
    bet_amount = int(round(bet_amount / 100.0) * 100)
    
    # Must meet minimum bet
    if bet_amount < min_bet:
        return 0
        
    return bet_amount

if __name__ == "__main__":
    # Example
    bankroll = 100000
    prob = 0.6
    odds = 2.0
    
    suggested = get_recommended_bet(bankroll, prob, odds)
    print(f"Bankroll: ¥{bankroll}")
    print(f"Prob: {prob*100}%, Odds: {odds}")
    print(f"Suggested Bet: ¥{suggested} (Kelly fraction applied)")
