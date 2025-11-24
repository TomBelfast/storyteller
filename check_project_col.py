import requests
from config import settings

def check_columns():
    TABLE_ID = "m3bzlwwkrgoaxb36"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{TABLE_ID}/columns"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Columns in Table {TABLE_ID}:")
            found_project = False
            for col in data.get("list", []):
                print(f"- {col['title']} (Type: {col['uidt']})")
                if col['title'] == "Project":
                    found_project = True
            
            if not found_project:
                print("\n❌ 'Project' column is MISSING!")
                print("You need to add it manually in NocoDB UI:")
                print("1. Add new column")
                print("2. Type: LinkToAnotherRecord")
                print("3. Table: Projects")
                print("4. Name: Project")
            else:
                print("\n✅ 'Project' column exists.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
