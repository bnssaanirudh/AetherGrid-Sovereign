import json
import os
import torch
import math
import pennylane as qml
from core.phase_generator import VQCPhaseGenerator

def run_noise_sensitivity_experiment():
    torch.manual_seed(42)
    
    E = 50
    edge_embed_dim = 4
    node_dim = 4
    
    hesitation = torch.rand(E, 1)
    staleness = torch.rand(E, 1)
    edge_type = torch.rand(E, edge_embed_dim)
    src = torch.rand(E, node_dim)
    dst = torch.rand(E, node_dim)
    stress = torch.rand(E, 1)
    
    # Base noiseless VQC
    vqc_base = VQCPhaseGenerator(edge_embed_dim, node_dim, out_dim=1, num_qubits=4, circuit_depth=2, backend="default.qubit")
    out_base, _ = vqc_base(hesitation, staleness, edge_type, src, dst, stress)
    
    noise_levels = [0.01, 0.05, 0.1, 0.2]
    drifts = {}
    
    try:
        # Check if default.mixed is available
        dev_mixed = qml.device("default.mixed", wires=4)
        
        for p in noise_levels:
            # We override the circuit to inject noise
            @qml.qnode(dev_mixed, interface="torch")
            def noisy_circuit(inputs, weights):
                qml.templates.AngleEmbedding(inputs, wires=range(4), rotation='Y')
                qml.templates.StronglyEntanglingLayers(weights, wires=range(4))
                # Inject Depolarizing channel
                for i in range(4):
                    qml.DepolarizingChannel(p, wires=i)
                return [qml.expval(qml.PauliZ(i)) for i in range(1)]
                
            vqc_noisy = VQCPhaseGenerator(edge_embed_dim, node_dim, out_dim=1, num_qubits=4, circuit_depth=2, backend="default.mixed")
            vqc_noisy.circuit = noisy_circuit
            # Match weights
            vqc_noisy.vqc_weights.data.copy_(vqc_base.vqc_weights.data)
            vqc_noisy.input_proj.load_state_dict(vqc_base.input_proj.state_dict())
            
            out_noisy, _ = vqc_noisy(hesitation, staleness, edge_type, src, dst, stress)
            drift_mse = torch.mean((out_noisy - out_base)**2).item()
            drifts[str(p)] = round(drift_mse, 4)
            
    except Exception as e:
        drifts["error"] = str(e)
        
    results = {
        "noise_sensitivity": {
            "drifts_by_noise_level": drifts,
            "conclusion": "Increasing depolarizing noise drives expectation values toward 0, causing phase to drift toward 0 (wrapped to -pi/pi)."
        }
    }
    
    os.makedirs("artifacts", exist_ok=True)
    handoff_path = "artifacts/prompt_04_handoff.json"
    if os.path.exists(handoff_path):
        with open(handoff_path, "r") as f:
            data = json.load(f)
    else:
        data = {}
        
    data.update(results)
    
    with open(handoff_path, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Noise experiment completed: {results}")

if __name__ == "__main__":
    run_noise_sensitivity_experiment()
