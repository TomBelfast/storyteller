import requests
from config import settings

def fix_columns():
    api_url = settings.NOCODB_API_URL
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    # 1. Delete old columns (Audio Duration, Audio Timestamps)
    old_cols = ["c35e7ntd99hmy2f", "c7bx8t6cvr9dpz7"]
    for col_id in old_cols:
        print(f"Deleting column {col_id}...")
        try:
            resp = requests.delete(f"{api_url}/api/v2/meta/columns/{col_id}", headers=headers)
            print(f"Status: {resp.status_code}")
        except Exception as e:
            print(f"Error deleting {col_id}: {e}")

    # 2. Create new columns (without spaces)
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    
    new_cols = [
        {
            "title": "AudioDuration",
            "uidt": "Number",
            "meta": {"precision": 2}
        },
        {
            "title": "AudioTimestamps",
            "uidt": "LongText"
        }
    ]
    
    for col in new_cols:
        print(f"Creating column {col['title']}...")
        try:
            resp = requests.post(f"{api_url}/api/v2/meta/tables/{table_id}/columns", json=col, headers=headers)
            print(f"Status: {resp.status_code}")
            print(resp.text)
        except Exception as e:
            print(f"Error creating {col['title']}: {e}")

if __name__ == "__main__":
    fix_columns()
