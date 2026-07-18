import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple, Any

class CascadeOccurrenceHead(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, graph_embedding: torch.Tensor) -> torch.Tensor:
        """Returns logit or prob depending on loss used. Using sigmoid for prob output."""
        return torch.sigmoid(self.net(graph_embedding)).squeeze(-1)


class CascadeSizeHead(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, graph_embedding: torch.Tensor) -> torch.Tensor:
        """Nonnegative regression for size (count-aware). Using Softplus to ensure > 0."""
        return F.softplus(self.net(graph_embedding)).squeeze(-1)


class CascadeRadiusHead(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        # Outputs two values: graph_radius (hops) and physical_radius
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 2)
        )

    def forward(self, graph_embedding: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        out = F.softplus(self.net(graph_embedding))
        return out[:, 0], out[:, 1]


class HorizonHead(nn.Module):
    def __init__(self, hidden_dim: int, num_classes: int = 3, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )

    def forward(self, graph_embedding: torch.Tensor) -> torch.Tensor:
        """Multiclass logits for short/medium/long risk."""
        return self.net(graph_embedding)


class NodeAffectedHead(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, node_embeddings: torch.Tensor) -> torch.Tensor:
        """Node-level precision/recall for affected maps."""
        return torch.sigmoid(self.net(node_embeddings)).squeeze(-1)


class InterventionScoreHead(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, graph_embedding: torch.Tensor, candidate_node_embedding: torch.Tensor) -> torch.Tensor:
        """Scores a candidate protection node by predicted reduction in cascade severity."""
        if graph_embedding.dim() == 1:
            graph_embedding = graph_embedding.unsqueeze(0)
        
        # Expand graph embedding to match candidate nodes if evaluating multiple
        if candidate_node_embedding.dim() == 2 and graph_embedding.size(0) == 1:
            graph_embedding = graph_embedding.expand(candidate_node_embedding.size(0), -1)
            
        combined = torch.cat([graph_embedding, candidate_node_embedding], dim=-1)
        return self.net(combined).squeeze(-1)


class MultiTaskHead(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.occurrence = CascadeOccurrenceHead(hidden_dim, dropout)
        self.size = CascadeSizeHead(hidden_dim, dropout)
        self.radius = CascadeRadiusHead(hidden_dim, dropout)
        self.horizon = HorizonHead(hidden_dim, 3, dropout) # 0: short, 1: medium, 2: long
        self.node_affected = NodeAffectedHead(hidden_dim, dropout)
        self.intervention = InterventionScoreHead(hidden_dim, dropout)

    def forward(self, graph_emb: torch.Tensor, node_embs: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        graph_radius, physical_radius = self.radius(graph_emb)
        
        affected_probs = {}
        for ntype, embs in node_embs.items():
            affected_probs[ntype] = self.node_affected(embs)
            
        return {
            "occurrence_prob": self.occurrence(graph_emb),
            "predicted_size": self.size(graph_emb),
            "graph_radius": graph_radius,
            "physical_radius": physical_radius,
            "horizon_logits": self.horizon(graph_emb),
            "affected_probs": affected_probs
        }
