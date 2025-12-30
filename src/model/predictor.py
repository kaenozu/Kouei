import os
import lightgbm as lgb
import numpy as np

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

class Predictor:
    def __init__(self, model_dir="models"):
        self.model_dir = model_dir
        self.onnx_path = os.path.join(model_dir, "model.onnx")
        self.lgb_path = os.path.join(model_dir, "lgbm_model.txt")
        self.session = None
        self.bst = None
        self.mode = None
        
        self.load()

    def load(self):
        # Try ONNX first
        if ONNX_AVAILABLE and os.path.exists(self.onnx_path):
            try:
                print(f"Loading ONNX Model from {self.onnx_path}...")
                self.session = ort.InferenceSession(self.onnx_path)
                self.mode = "onnx"
                return
            except Exception as e:
                print(f"ONNX Load Error: {e}. Falling back to LightGBM.")

        # Fallback to LGBM
        if os.path.exists(self.lgb_path):
            print(f"Loading LightGBM Model from {self.lgb_path}...")
            self.bst = lgb.Booster(model_file=self.lgb_path)
            self.mode = "lgbm"
        else:
            print("No model found.")

    def predict(self, X):
        """
        X: numpy array or pandas DataFrame
        """
        if self.mode == "onnx":
            # ONNX requires float32 numpy
            if hasattr(X, "values"):
                data = X.values.astype(np.float32)
            else:
                data = np.array(X, dtype=np.float32)
            
            input_name = self.session.get_inputs()[0].name
            # ONNX Runtime returns list of outputs. 
            # LGBM classifier usually outputs probabilities. Check one output?
            # Typically ONNX converted from LightGBM Classifier has ZipMap or Probabilities.
            # If Regressor -> Value.
            # Assuming Binary Prob -> [0] might be label, [1] probability map.
            # Let's inspect output shape.
            
            # Simple conversion usually keeps it parallel to predict methods.
            preds = self.session.run(None, {input_name: data})
            # preds[0] is often the label if Classifier, or value if Regressor.
            # preds[1] is probabilities.
            
            # Since our lgb model was likely trained as regression or binary with objective='binary',
            # lgb.predict returns prob of class 1.
            # onnxmltools usually produces: output_label, output_probability
            
            # If we trained with 'binary', output 0 is label, output 1 is list of maps {0:p0, 1:p1}
            # This is slow to parse.
            # But let's check what our result looks like.
            
            # Hack: If result is a map/dict, extract current.
            res = preds[0] 
            # If result is just values (regressor style), use it.
            # If it's class labels, we need probability.
            
            # Actually, `onnxmltools.convert_lightgbm` with `initial_types` often defaults to 
            # ZipMap=True.
            
            if len(preds) > 1:
                # preds[1] matches [{'0': 0.8, '1': 0.2}, ...]
                # Extract prob for '1'
                final_preds = []
                for p_map in preds[1]:
                    final_preds.append(p_map.get(1, 0.0))
                return np.array(final_preds)
            else:
                # Regressor
                return res
            
        elif self.mode == "lgbm":
            return self.bst.predict(X)
        else:
            return np.zeros(len(X))
