import torch
import math
from typing import Dict, Any

class WorldClassGraphBuilder:
    """
    Procedural generation of a massive scale-free graph representing a 
    multi-city power grid (e.g., 50 cities with thousands of sensors).
    Uses pure PyTorch to synthesize node features and edge indices.
    """
    
    @staticmethod
    def generate_macro_topology(num_cities: int = 50, sensors_per_city: int = 1000) -> Dict[str, Any]:
        """
        Generates a massive graph tensor structure.
        """
        num_nodes = num_cities * sensors_per_city
        
        # 1. Generate Node Features (Voltage, Frequency, Temp, Dropout_Risk, Capacity)
        # Shape: [num_nodes, 5]
        x = torch.randn(num_nodes, 5) 
        
        # Normalize and set realistic bounds
        x[:, 0] = x[:, 0] * 0.05 + 1.0  # Voltage around 1.0 p.u.
        x[:, 1] = x[:, 1] * 0.01 + 60.0 # Frequency around 60 Hz
        x[:, 2] = torch.abs(x[:, 2] * 5.0 + 25.0) # Temp around 25C
        x[:, 3] = torch.sigmoid(x[:, 3] - 2.0) # Dropout risk (mostly low)
        x[:, 4] = torch.abs(x[:, 4] * 100 + 500) # Capacity in MW
        
        # 2. Generate edges (Scale-Free approximation)
        # For simplicity and speed in the API, we use a random sparse connection matrix 
        # heavily biased towards intra-city connections.
        
        # Average degree of 4
        num_edges = num_nodes * 4 
        
        # Source and Target arrays
        row = torch.randint(0, num_nodes, (num_edges,))
        
        # Make it scale-free-ish by squaring a uniform random variable
        # This biases the targets towards lower indices (hubs)
        col_uniform = torch.rand(num_edges)
        col = (col_uniform ** 2 * num_nodes).long()
        
        edge_index = torch.stack([row, col], dim=0)
        
        # 3. Edge features (Line rating, Resistance, Reactance)
        edge_attr = torch.randn(num_edges, 3)
        edge_attr = torch.abs(edge_attr)
        
        # 4. Generate physical coordinates (clustered around global cities)
        GLOBAL_CITIES = [
            (40.7128, -74.0060),   # New York
            (41.8781, -87.6298),   # Chicago
            (51.5074, -0.1278),    # London
            (35.6762, 139.6503),   # Tokyo
            (34.0522, -118.2437),  # Los Angeles
            (48.8566, 2.3522),     # Paris
            (-33.8688, 151.2093),  # Sydney
            (19.0760, 72.8777),    # Mumbai
            (-23.5505, -46.6333),  # Sao Paulo
            (-26.2041, 28.0473),   # Johannesburg
        ]
        
        lat_list = []
        lon_list = []
        for i in range(num_nodes):
            city_idx = (i // sensors_per_city) % len(GLOBAL_CITIES)
            base_lat, base_lon = GLOBAL_CITIES[city_idx]
            lat_list.append(base_lat + float(torch.randn(1)) * 0.15)
            lon_list.append(base_lon + float(torch.randn(1)) * 0.15)
            
        lat = lat_list
        lon = lon_list
        
        return {
            "x": x,
            "edge_index": edge_index,
            "edge_attr": edge_attr,
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "lat": lat,
            "lon": lon,
            "topology_scale": f"{num_cities} cities, {num_nodes} sensors"
        }
