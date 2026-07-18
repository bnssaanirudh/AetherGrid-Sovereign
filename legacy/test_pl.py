import pennylane as qml
import torch
from torch import nn

print(f"PennyLane version: {qml.__version__}")

dev = qml.device('default.qubit', wires=2)

@qml.qnode(dev, interface='torch')
def circuit(inputs, weights):
    qml.templates.AngleEmbedding(inputs, wires=range(2))
    qml.templates.StronglyEntanglingLayers(weights, wires=range(2))
    return [qml.expval(qml.PauliZ(i)) for i in range(2)]

inputs = torch.tensor([[0.1, 0.2], [0.3, 0.4]], requires_grad=True)
weights = torch.randn(1, 2, 3, requires_grad=True)

out = circuit(inputs[0], weights)
print(f"Output type: {type(out)}, val: {out}")
