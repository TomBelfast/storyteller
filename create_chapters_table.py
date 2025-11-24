import requests
from config import settings
from utils.logger import logger

def create_chapters_table():
    # Base ID from the Projects table (p5ubgijahnzy0xd)
    # We can get this dynamically or hardcode it since we saw it in the schema
    TARGET_BASE_ID = "p5ubgijahnzy0xd" 
    
    print(f"Creating 'Chapters' table in Base ID: {TARGET_BASE_ID}")
    
    headers = {
        "xc-token": settings.NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    # 1. Define the table
    table_payload = {
        "title": "Chapters",
        "base_id": TARGET_BASE_ID,
        "columns": [
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
    
    # API Endpoint to create table
    # Try v2 first, then v1 if it fails
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/bases/{TARGET_BASE_ID}/tables"
    
    try:
        print(f"POST {url}")
        response = requests.post(url, json=table_payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            new_table_id = data.get("id")
            print(f"✅ SUCCESS! Created table 'Chapters'. ID: {new_table_id}")
            
            # Now we need to create the Link to Projects
            # This is usually a separate call to create a Link Column
            create_link_column(new_table_id, settings.NOCODB_PROJECTS_TABLE_ID, headers)
            
            return new_table_id
        else:
            print(f"❌ Failed to create table: {response.status_code} - {response.text}")
            
            # Fallback to v1 if v2 fails (sometimes paths differ)
            url_v1 = f"{settings.NOCODB_API_URL}/api/v1/db/meta/projects/{TARGET_BASE_ID}/tables"
            print(f"Retrying with v1: {url_v1}")
            response = requests.post(url_v1, json=table_payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                new_table_id = data.get("id")
                print(f"✅ SUCCESS! Created table 'Chapters' (v1). ID: {new_table_id}")
                create_link_column(new_table_id, settings.NOCODB_PROJECTS_TABLE_ID, headers)
                return new_table_id
            else:
                print(f"❌ Failed v1 also: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def create_link_column(chapters_table_id, projects_table_id, headers):
    print("Creating Link to Projects table...")
    
    # Endpoint to add column
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{chapters_table_id}/columns"
    
    link_payload = {
        "title": "Project",
        "column_name": "Project",
        "uidt": "LinkToAnotherRecord",
        "dt": "varchar(255)",
        "colOptions": {
            "type": "hm", # Has Many / Many to One
            "relatedTableId": projects_table_id,
            "relationship": "Mm" # Many to Many or One to Many? Usually hm (Has Many) implies One Project has Many Chapters
            # NocoDB API for links is tricky, let's try standard config
        }
    }
    
    try:
        response = requests.post(url, json=link_payload, headers=headers)
        if response.status_code == 200:
             print("✅ Link column created successfully.")
        else:
             print(f"⚠️ Failed to create link column: {response.text}")
             print("You might need to link it manually in UI.")
    except Exception as e:
        print(f"⚠️ Error creating link: {e}")

if __name__ == "__main__":
    create_chapters_table()
