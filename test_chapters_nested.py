import requests
from config import settings
import json

def check_chapters_nested():
    TABLE_ID = "m3bzlwkrgoaxb36" # Correct Chapters ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    # Get records with nested data
    url = f"{settings.NOCODB_API_URL}/api/v2/tables/{TABLE_ID}/records?nested=true&limit=10"
    
    print(f"Fetching chapters from {TABLE_ID} with nested=true...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            records = data.get("list", [])
            print(f"Found {len(records)} records.")
            
            for r in records:
                print(f"\nID: {r['Id']}, Title: {r.get('Title')}")
                projects = r.get("Projects")
                print(f"Projects field ({type(projects)}): {projects}")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_chapters_nested()
