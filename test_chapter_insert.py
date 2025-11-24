import requests
from config import settings
import json

def test_chapter_insert():
    TABLE_ID = "m3bzlwwkrgoaxb36"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    url = f"{settings.NOCODB_API_URL}/api/v2/tables/{TABLE_ID}/records"
    
    # Try to insert a record with Project link
    # We need a valid Project ID. Let's use ID 5 (History of Coffee)
    PROJECT_ID = 5
    
    payload = {
        "Title": "Test Chapter",
        "Content": "Test Content",
        "Project": {"Id": PROJECT_ID}, # Link format
        "StartTime": 0,
        "EndTime": 10
    }
    
    print(f"Attempting to insert test record into {TABLE_ID}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("✅ SUCCESS! Record inserted.")
            print(response.json())
        else:
            print(f"❌ Failed to insert: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chapter_insert()
