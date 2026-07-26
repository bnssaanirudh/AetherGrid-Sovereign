import asyncio
import time
import random
from typing import List

async def simulate_api_traffic(rps: int, duration: int):
    """Simulate API metadata traffic (e.g. fetching scenarios)."""
    print(f"Simulating API metadata traffic at {rps} RPS for {duration}s...")
    await asyncio.sleep(duration * 0.1)  # scale down for fast simulation
    return {"latency_p50": 12, "latency_p95": 24, "latency_p99": 45, "error_rate": 0.0}

async def simulate_inference(ego_size: str, requests: int):
    """Simulate synchronous/asynchronous inference workloads."""
    print(f"Simulating {requests} {ego_size}-ego inference requests...")
    # Mock compute delay based on ego size
    base_delay = 0.05 if ego_size == "small" else 0.25
    await asyncio.sleep(base_delay * requests * 0.1)
    
    return {
        "latency_p50": int(base_delay * 1000), 
        "latency_p95": int(base_delay * 1200), 
        "latency_p99": int(base_delay * 1500), 
        "error_rate": 0.0,
        "vqc_overhead_ms": 15 if ego_size == "small" else 42
    }

async def simulate_ingestion_burst(events: int):
    """Simulate an event ingestion burst."""
    print(f"Simulating ingestion of {events} events...")
    await asyncio.sleep(1)
    return {"throughput_eps": events / 1.0, "queue_delay_ms": 5}

async def run_load_profiles():
    print("--- Starting Load Profiling ---")
    
    api_res = await simulate_api_traffic(rps=500, duration=30)
    print("API Metadata:", api_res)
    
    sync_small = await simulate_inference("small", 100)
    print("Sync Small Ego Inference:", sync_small)
    
    async_medium = await simulate_inference("medium", 50)
    print("Async Medium Ego Inference:", async_medium)
    
    ingest = await simulate_ingestion_burst(5000)
    print("Ingestion Burst:", ingest)
    
    print("--- Load Profiling Complete ---")

if __name__ == "__main__":
    asyncio.run(run_load_profiles())
