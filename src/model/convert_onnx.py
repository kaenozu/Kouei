import lightgbm as lgb
import onnxmltools
from onnxmltools.convert.common.data_types import FloatTensorType
import os
import sys

def convert():
    model_path = "models/lgbm_model.txt"
    onnx_path = "models/model.onnx"
    
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        return

    print("Loading LightGBM model...")
    bst = lgb.Booster(model_file=model_path)
    
    # Needs simple dummy input signature
    # 31 features? We need to know exact number.
    # LightGBM model saves feature names.
    n_features = bst.num_feature()
    print(f"Detected {n_features} features.")
    
    initial_types = [('input', FloatTensorType([None, n_features]))]
    
    print("Converting to ONNX...")
    onnx_model = onnxmltools.convert_lightgbm(bst, initial_types=initial_types)
    
    print(f"Saving to {onnx_path}...")
    onnxmltools.utils.save_model(onnx_model, onnx_path)
    print("Conversion Complete.")

if __name__ == "__main__":
    convert()
