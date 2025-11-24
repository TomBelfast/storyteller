import requests
from config import settings

# Test correct PATCH format according to NocoDB docs
api_url = settings.NOCODB_API_URL
table_id = settings.NOCODB_PROJECTS_TABLE_ID
headers = {"xc-token": settings.NOCODB_API_TOKEN}

# According to docs: Payload should be array of objects with Id
# Testing with AudioDuration2 (newly created test column)
payload = [{
    "Id": 5,
    "AudioDuration2": 179.49
}]

print(f"Testing PATCH to {api_url}/api/v2/tables/{table_id}/records")
print(f"Payload: {payload}")

resp = requests.patch(
    f"{api_url}/api/v2/tables/{table_id}/records",
    json=payload,
    headers=headers
)

print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

# Verify via GET
print("\nVerifying...")
get_resp = requests.get(
    f"{api_url}/api/v2/tables/{table_id}/records/5",
    headers=headers
)
data = get_resp.json()
print(f"AudioDuration2: {data.get('AudioDuration2')}")
print(f"Word Count: {data.get('Word Count')}")
