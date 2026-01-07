"""Neural Network model for ensemble prediction"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, Tuple

class BoatRaceNet(nn.Module):
    """Neural Network for boat race prediction"""
    def __init__(self, input_dim: int, hidden_dims: List[int] = [256, 128, 64], dropout: float = 0.3):
        super(BoatRaceNet, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())
        
        self.layers = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.layers(x.squeeze())

class NeuralNetworkPredictor:
    """Neural Network model for integration in ensemble"""
    def __init__(self, device: str = 'cpu'):
        self.device = torch.device(device)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'target') -> Tuple[torch.Tensor, torch.Tensor]:
        """Prepare data for neural network"""
        # 特徴量とターゲットを分離
        feature_cols = [col for col in df.columns if col != target_col]
        self.feature_names = feature_cols
        
        X = df[feature_cols].fillna(0)
        y = df[target_col]
        
        # スケーリング
        X_scaled = self.scaler.fit_transform(X)
        
        # テンソルに変換
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        y_tensor = torch.FloatTensor(y.values).to(self.device)
        
        return X_tensor, y_tensor.unsqueeze(1)
    
    def train(self, df: pd.DataFrame, epochs: int = 100, batch_size: int = 1024) -> Dict[str, float]:
        """Train neural network model"""
        # データ準備
        X, y = self.prepare_data(df)
        input_dim = X.shape[1]
        
        # モデル初期化
        self.model = BoatRaceNet(input_dim).to(self.device)
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=5)
        
        # データ分割
        X_train, X_val, y_train, y_val = train_test_split(X.cpu().numpy(), y.cpu().numpy(), test_size=0.2, random_state=42)
        X_train = torch.FloatTensor(X_train).to(self.device)
        y_train = torch.FloatTensor(y_train).to(self.device)
        X_val = torch.FloatTensor(X_val).to(self.device)
        y_val = torch.FloatTensor(y_val).to(self.device)
        
        # 学習ループ
        train_dataset = torch.utils.data.TensorDataset(X_train, y_train)
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        best_val_auc = 0
        training_history = {'loss': [], 'val_auc': []}
        
        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                epoch_loss += loss.item()
            
            # 検証
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val)
                val_pred = val_outputs.cpu().numpy()
                val_true = y_val.cpu().numpy()
                val_auc = self._calculate_auc(val_true, val_pred)
                
            if val_auc > best_val_auc:
                best_val_auc = val_auc
                # Save best model if needed
            
            scheduler.step(val_auc)
            training_history['loss'].append(epoch_loss / len(train_loader))
            training_history['val_auc'].append(val_auc)
            
            if epoch % 20 == 0:
                print(f'Epoch {epoch}/{epochs}, Loss: {epoch_loss}, Val AUC: {val_auc:.4f}')
        
        return {'best_val_auc': best_val_auc, 'final_val_auc': val_auc}
    
    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Predict probability"""
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        X = df[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            predictions = self.model(X_tensor)
            return predictions.cpu().numpy().squeeze()
    
    def _calculate_auc(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate AUC score"""
        try:
            from sklearn.metrics import roc_auc_score
            return roc_auc_score(y_true, y_pred)
        except:
            return 0.0
    
    def save_model(self, path: str):
        """Save model state"""
        torch.save({
            'model_state': self.model.state_dict(),
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }, path)
    
    def load_model(self, path: str):
        """Load model state"""
        checkpoint = torch.load(path, map_location=self.device)
        input_dim = len(checkpoint['feature_names'])
        self.model = BoatRaceNet(input_dim).to(self.device)
        self.model.load_state_dict(checkpoint['model_state'])
        self.scaler = checkpoint['scaler']
        self.feature_names = checkpoint['feature_names']
