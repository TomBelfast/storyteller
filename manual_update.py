import requests
import json
from config import settings

def manual_update():
    api_url = settings.NOCODB_API_URL
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}

    print(f"Updating table {table_id}, record 5...")

    payload = [{
        "Id": 5,
        "Word Count": 123
    }]

    try:
        resp = requests.patch(f"{api_url}/api/v2/tables/{table_id}/records", json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    manual_update()
