"""PyTorch Deep Tabular Network optimized for NVIDIA GeForce RTX 4060."""
import time
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from src.features.builder import prepare_feature_dataframe, TabularPreprocessor

class TabularResBlock(nn.Module):
    """Residual MLP block with LayerNorm and SiLU activation."""
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )
        self.act = nn.SiLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(x + self.block(x))

class ThroughputResNet(nn.Module):
    """Deep Tabular Network for cellular throughput regression."""
    def __init__(self, in_features: int = 15, hidden_dim: int = 256, num_blocks: int = 3, dropout: float = 0.1):
        super().__init__()
        self.in_proj = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            nn.Dropout(dropout)
        )
        self.blocks = nn.ModuleList([
            TabularResBlock(hidden_dim, dropout=dropout) for _ in range(num_blocks)
        ])
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.SiLU(),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.in_proj(x)
        for b in self.blocks:
            h = b(h)
        out = self.head(h)
        return torch.relu(out)  # Throughput is strictly non-negative

class GPUThroughputNeuralPredictor:
    """Trainer and inference engine utilizing NVIDIA RTX 4060 with mixed precision."""
    def __init__(self, hidden_dim: int = 256, num_blocks: int = 3, lr: float = 1e-3,
                 batch_size: int = 64, epochs: int = 100, patience: int = 15, random_seed: int = 42):
        self.hidden_dim = hidden_dim
        self.num_blocks = num_blocks
        self.lr = lr
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience
        self.random_seed = random_seed
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.preprocessor = TabularPreprocessor()
        self.model: Optional[ThroughputResNet] = None
        self.profiling_info: Dict[str, float] = {}

    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray,
            X_val: Optional[pd.DataFrame] = None, y_val: Optional[np.ndarray] = None):
        torch.manual_seed(self.random_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.random_seed)
            torch.cuda.reset_peak_memory_stats(self.device)

        # Leak-free feature preprocessing
        X_train_f = prepare_feature_dataframe(X_train)
        X_scaled_tr = self.preprocessor.fit_transform(X_train_f)
        
        train_ds = TensorDataset(
            torch.tensor(X_scaled_tr, dtype=torch.float32),
            torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
        )
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)

        val_loader = None
        if X_val is not None and y_val is not None and len(X_val) > 0:
            X_val_f = prepare_feature_dataframe(X_val)
            X_scaled_val = self.preprocessor.transform(X_val_f)
            val_ds = TensorDataset(
                torch.tensor(X_scaled_val, dtype=torch.float32),
                torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
            )
            val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        in_dim = X_scaled_tr.shape[1]
        self.model = ThroughputResNet(in_features=in_dim, hidden_dim=self.hidden_dim, num_blocks=self.num_blocks).to(self.device)
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.epochs, eta_min=1e-5)
        criterion = nn.HuberLoss(delta=1.0)
        scaler = torch.amp.GradScaler('cuda', enabled=(self.device.type == 'cuda'))

        best_loss = float('inf')
        patience_counter = 0
        best_weights = None
        
        start_time = time.time()
        self.model.train()

        for epoch in range(self.epochs):
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device, non_blocking=True)
                batch_y = batch_y.to(self.device, non_blocking=True)
                
                optimizer.zero_grad(set_to_none=True)
                with torch.amp.autocast(device_type=self.device.type, enabled=(self.device.type == 'cuda')):
                    pred = self.model(batch_x)
                    loss = criterion(pred, batch_y)
                    
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()

            scheduler.step()

            # Validation evaluation
            if val_loader is not None:
                self.model.eval()
                val_loss = 0.0
                val_count = 0
                with torch.no_grad():
                    for vx, vy in val_loader:
                        vx, vy = vx.to(self.device), vy.to(self.device)
                        with torch.amp.autocast(device_type=self.device.type, enabled=(self.device.type == 'cuda')):
                            vpred = self.model(vx)
                            val_loss += criterion(vpred, vy).item() * len(vx)
                        val_count += len(vx)
                val_loss /= max(1, val_count)
                self.model.train()
                
                if val_loss < best_loss:
                    best_loss = val_loss
                    best_weights = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self.patience:
                        break

        total_train_time = time.time() - start_time
        if best_weights is not None:
            self.model.load_state_dict(best_weights)
        self.model.eval()

        peak_vram_mb = torch.cuda.max_memory_allocated(self.device) / (1024 * 1024) if self.device.type == 'cuda' else 0.0
        param_count = sum(p.numel() for p in self.model.parameters())

        self.profiling_info = {
            'device': str(self.device),
            'gpu_name': torch.cuda.get_device_name(0) if self.device.type == 'cuda' else 'CPU',
            'train_time_seconds': total_train_time,
            'peak_vram_mb': peak_vram_mb,
            'parameter_count': param_count,
            'best_val_loss': best_loss
        }
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise RuntimeError('Model not fitted.')
        self.model.eval()
        X_feats = prepare_feature_dataframe(X)
        X_scaled = self.preprocessor.transform(X_feats)
        x_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(self.device)
        
        with torch.no_grad():
            with torch.amp.autocast(device_type=self.device.type, enabled=(self.device.type == 'cuda')):
                preds = self.model(x_tensor).cpu().numpy().flatten()
        return np.maximum(0.0, preds)

