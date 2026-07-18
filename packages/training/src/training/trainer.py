import torch
import logging
import os
import random
import numpy as np
from typing import Dict, Any, Optional
from torch.cuda.amp import autocast, GradScaler
from aethergrid_core.data.event_dataset import EventDatasetIndex # or similar custom dataset

logger = logging.getLogger(__name__)

def seed_everything(seed: int = 42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

class AetherTrainer:
    def __init__(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        device: torch.device,
        grad_accum_steps: int = 1,
        use_amp: bool = False,
        patience: int = 5,
        checkpoint_dir: str = "runs/checkpoints",
        primary_metric: str = "val_loss",
        minimize_metric: bool = True
    ):
        self.model = model.to(device)
        self.optimizer = optimizer
        self.device = device
        self.grad_accum_steps = grad_accum_steps
        self.use_amp = use_amp and device.type == 'cuda'
        self.scaler = GradScaler() if self.use_amp else None
        
        self.patience = patience
        self.checkpoint_dir = checkpoint_dir
        self.primary_metric = primary_metric
        self.minimize_metric = minimize_metric
        
        self.best_metric = float('inf') if minimize_metric else float('-inf')
        self.patience_counter = 0
        self.epoch = 0
        
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _compute_loss(self, preds: Dict[str, Any], batch: Any) -> torch.Tensor:
        """
        Computes masked multi-task losses.
        (Placeholder logic depending on batch format)
        """
        # Assume batch has 'occurrence_label', 'cascade_size', 'graph_radius', 'horizon_label'
        # with masks for valid entries.
        loss = torch.tensor(0.0, device=self.device, requires_grad=True)
        return loss

    def train_epoch(self, dataloader) -> Dict[str, float]:
        self.model.train()
        total_loss = 0.0
        
        for batch_idx, batch in enumerate(dataloader):
            # Move to device (placeholder)
            
            with autocast(enabled=self.use_amp):
                # Dummy forward, actual inputs depend on PyG structure
                # preds, _ = self.model(batch)
                # loss = self._compute_loss(preds, batch)
                loss = torch.tensor(0.1, device=self.device, requires_grad=True) # dummy
                
            loss = loss / self.grad_accum_steps
            
            if self.use_amp:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
                
            if (batch_idx + 1) % self.grad_accum_steps == 0:
                if self.use_amp:
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    self.optimizer.step()
                self.optimizer.zero_grad()
                
            total_loss += loss.item() * self.grad_accum_steps
            
        return {"train_loss": total_loss / max(1, len(dataloader))}

    def validate(self, dataloader) -> Dict[str, float]:
        self.model.eval()
        total_loss = 0.0
        with torch.no_grad():
            for batch in dataloader:
                loss = torch.tensor(0.1, device=self.device) # dummy
                total_loss += loss.item()
                
        # Simulate computing metrics
        val_loss = total_loss / max(1, len(dataloader))
        return {"val_loss": val_loss, "val_auroc": 0.85}

    def save_checkpoint(self, path: str):
        torch.save({
            'epoch': self.epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_metric': self.best_metric
        }, path)

    def load_checkpoint(self, path: str):
        if os.path.exists(path):
            checkpoint = torch.load(path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.epoch = checkpoint['epoch']
            self.best_metric = checkpoint['best_metric']
            logger.info(f"Resumed from {path} at epoch {self.epoch}")
        else:
            logger.warning(f"Checkpoint {path} not found.")

    def fit(self, train_loader, val_loader, max_epochs: int = 100):
        for epoch in range(self.epoch, max_epochs):
            self.epoch = epoch
            train_metrics = self.train_epoch(train_loader)
            val_metrics = self.validate(val_loader)
            
            metric_val = val_metrics.get(self.primary_metric, 0.0)
            
            improved = (metric_val < self.best_metric) if self.minimize_metric else (metric_val > self.best_metric)
            
            if improved:
                self.best_metric = metric_val
                self.patience_counter = 0
                self.save_checkpoint(os.path.join(self.checkpoint_dir, "best_model.pt"))
                logger.info(f"Epoch {epoch}: {self.primary_metric} improved to {metric_val:.4f}")
            else:
                self.patience_counter += 1
                
            if self.patience_counter >= self.patience:
                logger.info(f"Early stopping triggered at epoch {epoch}")
                break
                
        # Save partial/final run status
        self.save_checkpoint(os.path.join(self.checkpoint_dir, "last_model.pt"))
