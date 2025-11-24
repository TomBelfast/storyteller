import requests
from config import settings
import json

def verify_chapters(project_id):
    # Use the CORRECT table ID from config
    TABLE_ID = settings.NOCODB_CHAPTERS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    print(f"Checking chapters for Project ID {project_id} in Table {TABLE_ID}...")
    
    # List all records and filter by project (inefficient but reliable for small data)
    url = f"{settings.NOCODB_API_URL}/api/v2/tables/{TABLE_ID}/records"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            records = data.get("list", [])
            print(f"Total records in table: {len(records)}")
            
            project_chapters = []
            for rec in records:
                # Check link field "Projects"
                # NocoDB returns links as object or list
                link = rec.get("Projects")
                print(f"Record {rec['Id']} - Link: {link}")
                
                # Check if linked to our project
                if link:
                    if isinstance(link, dict) and str(link.get("Id")) == str(project_id):
                        project_chapters.append(rec)
                    elif isinstance(link, list) and any(str(l.get("Id")) == str(project_id) for l in link):
                        project_chapters.append(rec)
                        
            print(f"Found {len(project_chapters)} chapters for Project {project_id}")
            for ch in project_chapters:
                print(f" - {ch['Title']} (ID: {ch['Id']})")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Redirect stdout to file
    import sys
    with open("verification_result.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        verify_chapters(5)
        sys.stdout = sys.__stdout__
    
    # Print content to console for tool to capture (hopefully)
    with open("verification_result.txt", "r", encoding="utf-8") as f:
        print(f.read())
