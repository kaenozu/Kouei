"""ONNX Runtime Predictor for Fast Inference"""
import numpy as np
import pandas as pd
import os
from typing import Optional, List, Union
import warnings

from src.config.settings import settings
from src.utils.logger import get_logger, log_execution_time

logger = get_logger()

# Try to import onnxruntime
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX Runtime not available, falling back to LightGBM")


class ONNXPredictor:
    """High-performance predictor using ONNX Runtime"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.onnx_model_path
        self.session: Optional[ort.InferenceSession] = None
        self.input_name: Optional[str] = None
        self.output_name: Optional[str] = None
        self._loaded = False
    
    def load(self) -> bool:
        """Load ONNX model"""
        if not ONNX_AVAILABLE:
            logger.error("ONNX Runtime not installed")
            return False
        
        if not os.path.exists(self.model_path):
            logger.warning(f"ONNX model not found: {self.model_path}")
            return False
        
        try:
            # Configure session options for performance
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 4
            sess_options.inter_op_num_threads = 4
            
            # Try GPU first, fall back to CPU
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            
            self.session = ort.InferenceSession(
                self.model_path,
                sess_options,
                providers=providers
            )
            
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self._loaded = True
            
            active_provider = self.session.get_providers()[0]
            logger.info(
                f"ONNX model loaded",
                path=self.model_path,
                provider=active_provider
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            return False
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    @log_execution_time()
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Run inference"""
        if not self._loaded:
            if not self.load():
                raise RuntimeError("Model not loaded")
        
        # Convert to numpy if DataFrame
        if isinstance(X, pd.DataFrame):
            X = X.values.astype(np.float32)
        elif isinstance(X, np.ndarray):
            X = X.astype(np.float32)
        
        # Run inference
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: X}
        )
        
        return outputs[0].flatten()
    
    def predict_batch(self, batches: List[Union[pd.DataFrame, np.ndarray]]) -> List[np.ndarray]:
        """Predict multiple batches efficiently"""
        return [self.predict(batch) for batch in batches]


class HybridPredictor:
    """Hybrid predictor that uses ONNX when available, falls back to LightGBM"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        self.onnx_predictor: Optional[ONNXPredictor] = None
        self.lgbm_model = None
        self._use_onnx = False
        self._loaded = False
    
    def load(self) -> bool:
        """Load best available model"""
        # Try ONNX first if enabled
        if settings.use_onnx and ONNX_AVAILABLE:
            onnx_path = os.path.join(self.model_dir, "model.onnx")
            if os.path.exists(onnx_path):
                self.onnx_predictor = ONNXPredictor(onnx_path)
                if self.onnx_predictor.load():
                    self._use_onnx = True
                    self._loaded = True
                    logger.info("Using ONNX predictor")
                    return True
        
        # Fall back to LightGBM
        lgbm_path = os.path.join(self.model_dir, "lgbm_model.txt")
        if os.path.exists(lgbm_path):
            try:
                import lightgbm as lgb
                self.lgbm_model = lgb.Booster(model_file=lgbm_path)
                self._loaded = True
                logger.info("Using LightGBM predictor")
                return True
            except Exception as e:
                logger.error(f"Failed to load LightGBM: {e}")
        
        logger.error("No model available")
        return False
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    def predict(self, X: Union[pd.DataFrame, np.ndarray], pred_contrib: bool = False) -> np.ndarray:
        """Run prediction"""
        if not self._loaded:
            if not self.load():
                raise RuntimeError("No model loaded")
        
        if self._use_onnx and not pred_contrib:
            return self.onnx_predictor.predict(X)
        elif self.lgbm_model is not None:
            if isinstance(X, pd.DataFrame):
                X_np = X.values
            else:
                X_np = X
            return self.lgbm_model.predict(X_np, pred_contrib=pred_contrib)
        else:
            raise RuntimeError("No model available")


def convert_lgbm_to_onnx(lgbm_model_path: str, output_path: str, n_features: int = 16):
    """Convert LightGBM model to ONNX format"""
    try:
        import lightgbm as lgb
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        import onnxmltools
        from onnxmltools.convert import convert_lightgbm
        
        # Load LightGBM model
        lgbm_model = lgb.Booster(model_file=lgbm_model_path)
        
        # Define input type
        initial_type = [('float_input', FloatTensorType([None, n_features]))]
        
        # Convert to ONNX
        onnx_model = convert_lightgbm(
            lgbm_model,
            initial_types=initial_type,
            target_opset=12
        )
        
        # Save
        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        
        logger.info(f"Converted to ONNX: {output_path}")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependencies for ONNX conversion: {e}")
        logger.info("Install with: pip install onnxmltools skl2onnx")
        return False
    except Exception as e:
        logger.error(f"ONNX conversion failed: {e}")
        return False


if __name__ == "__main__":
    # Test prediction speed
    import time
    
    predictor = HybridPredictor()
    predictor.load()
    
    # Generate test data
    test_data = np.random.randn(1000, 16).astype(np.float32)
    
    # Warmup
    _ = predictor.predict(test_data[:10])
    
    # Benchmark
    start = time.time()
    for _ in range(100):
        predictor.predict(test_data)
    elapsed = time.time() - start
    
    print(f"100 predictions (1000 samples each): {elapsed:.3f}s")
    print(f"Average per prediction: {elapsed/100*1000:.2f}ms")
