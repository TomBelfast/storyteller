import requests
from config import settings
import json

def check_columns_robust():
    TABLE_ID = "m3bzlwwkrgoaxb36"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    # Try listing columns
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{TABLE_ID}/columns"
    
    print(f"Checking columns for Table {TABLE_ID}...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            columns = data.get("list", [])
            print(f"Found {len(columns)} columns:")
            
            project_col_exists = False
            for col in columns:
                print(f" - {col['title']} ({col['uidt']})")
                if col['title'] == "Project":
                    project_col_exists = True
            
            if not project_col_exists:
                print("\n⚠️ 'Project' column is MISSING!")
                create_project_column(TABLE_ID, headers)
            else:
                print("\n✅ 'Project' column exists.")
                
        else:
            print(f"❌ Failed to list columns: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

def create_project_column(table_id, headers):
    print("Attempting to create 'Project' column...")
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{table_id}/columns"
    
    payload = {
        "title": "Project",
        "column_name": "Project",
        "uidt": "LinkToAnotherRecord",
        "colOptions": {
            "type": "hm",
            "relatedTableId": settings.NOCODB_PROJECTS_TABLE_ID,
            "relationship": "Mm" # Try Mm if hm fails, or vice versa. Usually 'hm' is correct for One-to-Many
        }
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            print("✅ Successfully created 'Project' column!")
        else:
            print(f"❌ Failed to create column: {resp.text}")
    except Exception as e:
        print(f"❌ Error creating column: {e}")

if __name__ == "__main__":
    check_columns_robust()
