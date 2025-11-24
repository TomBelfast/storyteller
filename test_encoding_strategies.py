import requests
import json
import base64
from config import settings

api_url = settings.NOCODB_API_URL
table_id = settings.NOCODB_PROJECTS_TABLE_ID
headers = {"xc-token": settings.NOCODB_API_TOKEN}

# Test different encoding strategies
test_data = [
    {"word": "Test", "start": 0.0, "end": 0.5},
    {"word": "Data", "start": 0.5, "end": 1.0}
]

strategies = [
    ("Raw JSON", json.dumps(test_data)),
    ("Base64", base64.b64encode(json.dumps(test_data).encode()).decode()),
    ("Escaped JSON", json.dumps(test_data).replace('"', '\\"')),
]

for strategy_name, encoded_data in strategies:
    print(f"\n=== Testing: {strategy_name} ===")
    payload = [{
        "Id": 5,
        "Visual Story JSON": encoded_data,
        "Description": f"Test: {strategy_name}"  # Marker to identify which strategy
    }]
    
    resp = requests.patch(
        f"{api_url}/api/v2/tables/{table_id}/records",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {resp.status_code}")
    
    # Verify
    get_resp = requests.get(f"{api_url}/api/v2/tables/{table_id}/records/5", headers=headers)
    data = get_resp.json()
    result = data.get('Visual Story JSON')
    desc = data.get('Description')
    
    print(f"Description: {desc}")
    print(f"Result: {result}")
    if result:
        print(f"✅ SUCCESS!")
        break
    else:
        print(f"❌ FAILED")
