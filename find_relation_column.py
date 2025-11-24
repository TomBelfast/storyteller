import requests
from config import settings
import json

def find_relation_column():
    TABLE_ID = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{TABLE_ID}"
    
    print(f"Fetching meta for Projects table {TABLE_ID}...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            columns = data.get("columns", [])
            
            print("Columns found:")
            for col in columns:
                if col.get("uidt") == "LinkToAnotherRecord":
                    print(f"LINK COLUMN: Title='{col.get('title')}', ID='{col.get('id')}', ColName='{col.get('col_name')}'")
                    # Check relation
                    print(f"  -> Related Table: {col.get('ref_table_id')}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    with open("meta_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        find_relation_column()
        sys.stdout = sys.__stdout__
    
    with open("meta_output.txt", "r", encoding="utf-8") as f:
        print(f.read())
