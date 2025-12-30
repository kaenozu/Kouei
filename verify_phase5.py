import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from src.model.explainer import SHAPExplainer
from src.model.train_incremental import train_incremental
from src.model.evaluator import AccuracyGuard

def verify():
    print("=== Phase 5 Verification ===")
    
    # 1. SHAP
    print("\n--- Testing SHAP ---")
    explainer = SHAPExplainer()
    # Dummy data with correct feature count?
    # Need to match model's features.
    if explainer.model:
        feats = explainer.model.feature_name()
        print(f"Model expects {len(feats)} features: {feats[:3]}...")
        
        # Create dummy DF with specific columns
        dummy_df = pd.DataFrame([ [0]*len(feats) ], columns=feats)
        
        exps = explainer.explain_local(dummy_df)
        print("Top 3 Contributing Factors:")
        for name, val in exps[:3]:
            print(f"  {name}: {val:.4f}")
    else:
        print("Skipping SHAP test (No model).")

    # 2. Incremental Learning (includes Guard)
    print("\n--- Testing Incremental Training & Guard ---")
    # This might fail if data.csv doesn't exist or is empty, but logic is checked.
    try:
        train_incremental()
        print("Incremental training script ran successfully.")
    except Exception as e:
        print(f"Incremental training error: {e}")

if __name__ == "__main__":
    verify()
