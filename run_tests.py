import os
import sys
import pytest

root_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.join(root_dir, "packages")
python_paths = [os.path.join(root_dir, "backend")]
if os.path.exists(packages_dir):
    for pkg in os.listdir(packages_dir):
        pkg_root = os.path.join(packages_dir, pkg)
        python_paths.append(pkg_root)

for p in python_paths:
    if p not in sys.path:
        sys.path.insert(0, p)

env = os.environ.copy()
os.environ["PYTHONPATH"] = os.pathsep.join(python_paths) + (os.pathsep + os.environ.get("PYTHONPATH", "") if os.environ.get("PYTHONPATH") else "")

# also test the weather api adapter
try:
    sys.path.append(root_dir)
    from packages.aethergrid_core.src.aethergrid_core.adapters.weather_api import LiveWeatherAdapter
    adapter = LiveWeatherAdapter(api_key=os.environ.get("OPENWEATHER_API_KEY", "dummy_key"))
    # try to fetch something
    import asyncio
    async def fetch_w():
        return await adapter.fetch_hazard_for_location(lat=25.0, lon=-80.0, node_id="test_01")
    res = asyncio.run(fetch_w())
    print("Weather API Test Result:", res)
except Exception as e:
    print("Weather API Test Failed:", e)

sys.exit(pytest.main(["tests", "experiments"]))
