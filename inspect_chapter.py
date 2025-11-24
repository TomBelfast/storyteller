import requests
from config import settings
import json

def inspect_chapter_record(record_id):
    TABLE_ID = "m3bzlwkrgoaxb36"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    # Get single record
    url = f"{settings.NOCODB_API_URL}/api/v2/tables/{TABLE_ID}/records/{record_id}"
    
    print(f"Inspecting Record {record_id}...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            link = data.get("Projects")
            print(f"\nProjects field type: {type(link)}")
            print(f"Projects field value: {link}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Inspect record ID 3 (from previous output)
    inspect_chapter_record(3)
