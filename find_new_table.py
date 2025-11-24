import requests
from config import settings

def list_tables():
    TARGET_BASE_ID = "p5ubgijahnzy0xd"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/bases/{TARGET_BASE_ID}/tables"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Tables in Base {TARGET_BASE_ID}:")
            for table in data.get("list", []):
                print(f"- {table['title']} (ID: {table['id']})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()
