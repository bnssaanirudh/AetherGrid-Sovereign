import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from packages.aethergrid_core.src.aethergrid_core.adapters.weather_api import LiveWeatherAdapter

@pytest.mark.asyncio
async def test_weather_adapter_no_key():
    adapter = LiveWeatherAdapter(api_key=None)
    with pytest.raises(ValueError, match="OPENWEATHER_API_KEY is missing"):
        await adapter.fetch_hazard_for_location(41.8, -87.6, "node_1")

@pytest.mark.asyncio
async def test_weather_adapter_success():
    adapter = LiveWeatherAdapter(api_key="mocked_key")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 25.0},
        "wind": {"speed": 10.0}
    }
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        node = await adapter.fetch_hazard_for_location(41.8, -87.6, "node_1")
        
    assert node["id"] == "hazard_node_1"
    assert node["type"] == "atmospheric"
    assert node["severity"] == 10.0 / 40.0
    assert node["parameters"]["temperature"] == 25.0

@pytest.mark.asyncio
async def test_weather_adapter_grid():
    adapter = LiveWeatherAdapter(api_key="mocked_key")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 22.0},
        "wind": {"speed": 15.0}
    }
    
    locations = [{"lat": 41.8, "lon": -87.6}, {"lat": 41.9, "lon": -87.5}]
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        nodes = await adapter.fetch_hazards_for_grid(locations)
        
    assert len(nodes) == 2
    assert nodes[0]["id"] == "hazard_loc_0"
    assert nodes[1]["id"] == "hazard_loc_1"
