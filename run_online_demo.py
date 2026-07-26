import asyncio
import json
from packages.aethergrid_core.src.aethergrid_core.adapters.weather_api import LiveWeatherAdapter

async def main():
    print("==================================================")
    print("AetherGrid Sovereign - Live Weather Adapter Demo")
    print("==================================================")
    print("\nInitializing LiveWeatherAdapter...")
    
    # Use the real API key provided by the user
    adapter = LiveWeatherAdapter(api_key=os.environ.get("OPENWEATHER_API_KEY", "dummy_key"))
    
    print("Executing REAL HTTP fetch to OpenWeatherMap for Chicago (Lat: 41.8781, Lon: -87.6298)...")
    
    try:
        # Fetch hazard for location
        hazard_node = await adapter.fetch_hazard_for_location(lat=41.8781, lon=-87.6298, node_id="chicago_downtown")
        
        print("\n[SUCCESS] Received and parsed Live Weather Telemetry:")
        print(json.dumps(hazard_node, indent=4))
        
        print("\nNote: The severity score is dynamically calculated based on the wind_speed and thresholds.")
        print("This node is now ready to be injected into the AetherGrid topology via the Sovereign Watchdog.")
    except Exception as e:
        print(f"\n[FAILED] Live Weather API call failed: {e}")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
