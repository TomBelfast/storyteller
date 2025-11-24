import requests
from config import settings

def create_test_col():
    api_url = settings.NOCODB_API_URL
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    
    col = {
        "title": "AudioDuration2",
        "uidt": "Number",
        "meta": {"precision": 2}
    }
    
    print(f"Creating column {col['title']}...")
    try:
        resp = requests.post(f"{api_url}/api/v2/meta/tables/{table_id}/columns", json=col, headers=headers)
        print(f"Status: {resp.status_code}")
        print(resp.text)
    except Exception as e:
        print(f"Error creating {col['title']}: {e}")

if __name__ == "__main__":
    create_test_col()
