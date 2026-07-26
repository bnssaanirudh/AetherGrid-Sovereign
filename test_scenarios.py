import urllib.request
import json

def test_scenario(hazard_type, intensity):
    url = "http://localhost:8080/api/v1/scenarios/sync"
    data = json.dumps({
        "trigger_nodes": ["substation_a"],
        "hazard_type": hazard_type,
        "hazard_intensity": intensity
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dev-token-administrator'
    })
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        print(f"[{hazard_type.upper()}] Success!")
        print(f"   Signature: {result.get('cryptographic_signature', 'MISSING')[:20]}...")
        if result.get('prediction'):
            print(f"   Predicted Radius: {result.get('prediction', {}).get('predicted_radius_graph', 'N/A')}")
        else:
            print(f"   Abstained: {result.get('abstention', {}).get('reason_code')}")
        print(f"   Interventions: {len(result.get('interventions', []))} proposed")
        
    except urllib.error.HTTPError as e:
        print(f"[{hazard_type.upper()}] Failed with {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"[{hazard_type.upper()}] Error: {str(e)}")

print("Testing core project scenarios (AetherGrid Sovereign)")
print("=====================================================")

def setup_model():
    print("Registering and approving model...")
    reg_req = urllib.request.Request("http://localhost:8080/api/v1/models/register", data=json.dumps({
        "model_id": "aether-v1",
        "version": "1.0.0",
        "checksum": "dummy-hash-1234",
        "config": {"layers": 3, "fuzzy_enabled": True}
    }).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer dev-token-administrator'})
    try: urllib.request.urlopen(reg_req)
    except: pass
    
    app_req = urllib.request.Request("http://localhost:8080/api/v1/models/approve/aether-v1", data=b'', headers={'Authorization': 'Bearer dev-token-administrator'})
    try: urllib.request.urlopen(app_req)
    except: pass
    
    print("Ingesting sensor data...")
    ingest_req = urllib.request.Request("http://localhost:8080/api/v1/events/ingest", data=json.dumps({
        "event_id": "evt_test_123",
        "event_type": "sensor_reading",
        "data": {"sensor_id": "substation_a", "voltage": 120.5}
    }).encode(), headers={'Content-Type': 'application/json', 'X-API-Key': '59b192eca07275bb01c546ee33eca182'})
    try: urllib.request.urlopen(ingest_req)
    except Exception as e: print("Ingest err:", e)
    
    print("Materializing snapshot...")
    mat_req = urllib.request.Request("http://localhost:8080/api/v1/snapshots/materialize", data=b'', headers={'Authorization': 'Bearer dev-token-administrator'})
    try: urllib.request.urlopen(mat_req)
    except Exception as e: print("Mat err:", e)
    
    print("Model ready!")

setup_model()

test_scenario("hurricane", 0.9)
test_scenario("cyber", 0.7)
test_scenario("emp", 1.0)
test_scenario("heatwave", 0.8)
