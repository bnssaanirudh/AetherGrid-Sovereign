"""Streamlit UI for AetherGrid-Sovereign."""

from __future__ import annotations

from typing import Dict

import streamlit as st
import torch
import numpy as np

from core.hgt_model import AetherHGT
from core.schema import NODE_TYPES
from data.toy_dataset import load_toy_graph


st.set_page_config(page_title="AetherGrid-Sovereign", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=DM+Serif+Display&display=swap');
    html, body, [class*="css"]  { font-family: 'Space Grotesk', sans-serif; }
    .hero {
        background: linear-gradient(120deg, #f6f5ef 0%, #e3f1f5 45%, #fef6ec 100%);
        padding: 28px 32px;
        border-radius: 18px;
        border: 1px solid #d7e1e8;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
    }
    .hero h1 { font-family: 'DM Serif Display', serif; color: #1a2d3b; margin-bottom: 8px; }
    .hero p { color: #33505f; margin: 0; }
    .chip { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #1a2d3b; color: #fef6ec; font-size: 12px; margin-right: 6px; }
    .panel { border-radius: 16px; border: 1px solid #d7e1e8; padding: 16px; background: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _infer(model: AetherHGT, data) -> Dict[str, np.ndarray]:
    model.eval()
    with torch.no_grad():
        preds, _ = model(data, return_attention=False)
    return {nt: preds[nt].cpu().numpy().squeeze(-1) for nt in NODE_TYPES}


def main() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="chip">Quantum-Fuzzy</div>
            <div class="chip">Urban Digital Twin</div>
            <h1>AetherGrid-Sovereign</h1>
            <p>Explore cascading failure risk with a Quantum-Fuzzy HGT model on a fixed toy graph.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Model Controls")
        hidden_dim = st.select_slider("Hidden dim", options=[16, 32, 64, 128], value=32)
        num_layers = st.select_slider("Layers", options=[1, 2, 3], value=1)
        num_heads = st.select_slider("Heads", options=[2, 4, 8], value=2)
        dropout = st.slider("Dropout", 0.0, 0.5, 0.1, 0.05)
        run_btn = st.button("Run inference", use_container_width=True)

    data = load_toy_graph()
    st.subheader("Toy Graph Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Power nodes", data["power"].num_nodes)
    col2.metric("Hospital nodes", data["hospital"].num_nodes)
    col3.metric("Road nodes", data["road"].num_nodes)
    col4.metric("Citizen nodes", data["citizen"].num_nodes)

    if run_btn:
        model = AetherHGT(
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            dropout=dropout,
        )
        preds = _infer(model, data)

        st.subheader("Predicted Failure Risk")
        risk_cols = st.columns(2)
        for idx, nt in enumerate(NODE_TYPES):
            with risk_cols[idx % 2]:
                st.markdown(f"**{nt} node risks**")
                st.bar_chart(preds[nt])

        st.subheader("Risk Summary")
        summary_cols = st.columns(4)
        for idx, nt in enumerate(NODE_TYPES):
            summary_cols[idx].metric(f"{nt} mean risk", f"{preds[nt].mean():.3f}")

    st.subheader("Node Feature Preview")
    preview = {nt: data[nt].x[:3].tolist() for nt in NODE_TYPES}
    st.json(preview)


if __name__ == "__main__":
    main()
