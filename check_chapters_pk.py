import requests
from config import settings

def check_table_columns():
    TABLE_ID = "mqjrioorje0nx53a"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{TABLE_ID}/columns"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Columns in Table {TABLE_ID}:")
            has_pk = False
            for col in data.get("list", []):
                print(f"- {col['title']} (Type: {col['uidt']}, PK: {col.get('pk', False)})")
                if col.get('pk'): has_pk = True
            
            if not has_pk:
                print("❌ NO PRIMARY KEY FOUND!")
            else:
                print("✅ Primary Key exists.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_table_columns()
