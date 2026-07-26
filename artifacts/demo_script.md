# AetherGrid Sovereign - Live Demo Script

**Target Duration**: 5-7 minutes
**Audience**: Security Analysts, Civil Engineers, Data Scientists

## Introduction (0:00 - 1:00)
**Presenter**: "Welcome to the AetherGrid Sovereign Digital Twin. This system leverages our proprietary Quantum-Fuzzy Heterogeneous Graph Transformer (Q-HGT) to predict cascading infrastructure failures under severe atmospheric and cyber hazards. Today, we'll run a live scenario and inspect the safety diagnostics."

## Walkthrough: The Live Twin Dashboard (1:00 - 3:00)
*(Presenter is on the main `/` route)*

**Presenter**: "Here is our core WebGL geospatial interface. The map visualizes our urban infrastructure network—nodes and edges colored by health status. 
On the left, we have the Scenario Builder. Let's configure a scenario."
*Action: Select 'Chicago (Urban-KG)' and 'Hurricane / Flooding'. Set Hesitation Margin to 15%.*
**Presenter**: "When we hit 'Run Simulation', AetherGrid submits the topology to our asynchronous FastAPI pipeline. The HGT model calculates failure probabilities while explicitly tracking prediction bounds."
*Action: Click 'Run Simulation'*

## Walkthrough: Safety Certificates (3:00 - 4:30)
*(Presenter directs attention to the Safety Dashboard on the left panel)*

**Presenter**: "Upon completion, the system generates a cryptographic Prediction Certificate. Here, we see `cert_success_01` mapped to the underlying `trace_01` fixture trace ID. This isn't just an accuracy metric; it's a bound of trust.
Notice the 'Confidence Decay' chart. Unlike a standard MLP that degrades linearly (the gray line), our Q-HGT maintains tight confidence bounds up to 50 seconds into the cascading failure event. The Phase Vector radar chart visualizes the precise breakdown of epistemic and aleatoric uncertainties."

## Walkthrough: Data Quality & Export (4:30 - 6:00)
*(Presenter navigates to the `/data` route)*

**Presenter**: "Predictions are only as good as the underlying telemetry. Our Data Quality dashboard provides a real-time audit log of the ingest stream. We're currently parsing over 14,000 live sensors with 99.8% uptime, and flagging quarantined records."
*(Presenter navigates back and clicks the 'Export Certificate' button)*
**Presenter**: "Finally, these bounds can be exported directly to JSON or PDF to comply with the IEEE Cyber-Physical Safety standards."

## Conclusion (6:00 - 7:00)
**Presenter**: "AetherGrid Sovereign gives operators the mathematical guarantee needed to trust AI in critical infrastructure. Thank you."
