import requests
from config import settings
import json

def recreate_chapters_table():
    TARGET_BASE_ID = "p5ubgijahnzy0xd"
    OLD_TABLE_ID = "mqjrioorje0nx53a"
    
    headers = {
        "xc-token": settings.NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    # 0. Find existing table ID
    print("Finding existing 'Chapters' table...")
    list_url = f"{settings.NOCODB_API_URL}/api/v2/meta/bases/{TARGET_BASE_ID}/tables"
    try:
        resp = requests.get(list_url, headers=headers)
        if resp.status_code == 200:
            for table in resp.json().get("list", []):
                if table["title"] == "Chapters":
                    OLD_TABLE_ID = table["id"]
                    print(f"Found existing Chapters table: {OLD_TABLE_ID}")
                    
                    # 1. Delete old table
                    print(f"Deleting old table {OLD_TABLE_ID}...")
                    del_url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{OLD_TABLE_ID}"
                    requests.delete(del_url, headers=headers)
                    print("Old table deleted.")
                    break
    except Exception as e:
        print(f"Find/Delete error: {e}")

    # 2. Create new table with Explicit ID
    print(f"Creating 'Chapters' table in Base {TARGET_BASE_ID}...")
    
    table_payload = {
        "title": "Chapters",
        "base_id": TARGET_BASE_ID,
        "columns": [
            {
                "column_name": "Id",
                "title": "Id",
                "uidt": "ID", # Explicitly ID type
                "pk": True,   # Primary Key
                "ai": True    # Auto Increment
            },
            {
                "column_name": "Title",
                "title": "Title",
                "uidt": "SingleLineText"
            },
            {
                "column_name": "Content",
                "title": "Content",
                "uidt": "LongText"
            },
            {
                "column_name": "StartTime",
                "title": "StartTime",
                "uidt": "Decimal"
            },
            {
                "column_name": "EndTime",
                "title": "EndTime",
                "uidt": "Decimal"
            },
            {
                "column_name": "VisualDesc",
                "title": "VisualDesc",
                "uidt": "LongText"
            },
             {
                "column_name": "ImagePath",
                "title": "ImagePath",
                "uidt": "Attachment"
            }
        ]
    }
    
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/bases/{TARGET_BASE_ID}/tables"
    
    try:
        response = requests.post(url, json=table_payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            new_table_id = data.get("id")
            print(f"✅ SUCCESS! Created table 'Chapters' with PK. ID: {new_table_id}")
            
            # Create Link Column
            create_link_column(new_table_id, settings.NOCODB_PROJECTS_TABLE_ID, headers)
            
            return new_table_id
        else:
            print(f"❌ Failed to create table: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def create_link_column(chapters_table_id, projects_table_id, headers):
    print("Creating Link to Projects table...")
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{chapters_table_id}/columns"
    
    link_payload = {
        "title": "Project",
        "column_name": "Project",
        "uidt": "LinkToAnotherRecord",
        "dt": "varchar(255)",
        "colOptions": {
            "type": "hm", 
            "relatedTableId": projects_table_id,
            "relationship": "Mm"
        }
    }
    
    try:
        response = requests.post(url, json=link_payload, headers=headers)
        if response.status_code == 200:
             print("✅ Link column created successfully.")
        else:
             print(f"⚠️ Failed to create link column: {response.text}")
    except Exception as e:
        print(f"⚠️ Error creating link: {e}")

if __name__ == "__main__":
    recreate_chapters_table()
