import shap
import lightgbm as lgb
import pandas as pd
import numpy as np
import os

class SHAPExplainer:
    def __init__(self, model_path="models/lgbm_model.txt"):
        self.model = None
        if os.path.exists(model_path):
            self.model = lgb.Booster(model_file=model_path)
            # TreeExplainer is best for trees
            self.explainer = shap.TreeExplainer(self.model)
        else:
            print("Model not found for SHAP.")

    def explain_local(self, X_row):
        """
        Explain a single prediction.
        X_row: DataFrame (single row) or numpy array (1, n_features)
        Returns: list of (feature_name, shap_value) sorted by absolute impact
        """
        if not self.model: return []
        
        # Calculate SHAP
        shap_values = self.explainer.shap_values(X_row)
        
        # shap_values shape for binary: list of arrays [class0, class1] or just array?
        # LightGBM binary: usually array (N, Features) corresponding to log-odds of class 1?
        # Or list of length 2?
        # TreeExplainer for LightGBM usually returns raw values change in margin.
        
        vals = shap_values
        if isinstance(vals, list):
            # Binary classification often returns [val_class0, val_class1]
            # We care about Class 1 (Win)
            vals = vals[1]
            
        # Extract single row
        if len(vals.shape) > 1:
            vals = vals[0]
            
        # Map to feature names
        feature_names = self.model.feature_name()
        
        explanation = []
        for name, val in zip(feature_names, vals):
            explanation.append((name, float(val)))
            
        # Sort by magnitude
        explanation.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return explanation

if __name__ == "__main__":
    # Test
    se = SHAPExplainer()
    print("Explainer Ready")
