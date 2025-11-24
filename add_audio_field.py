import requests
from config import settings
from utils.logger import logger

def add_audio_attachment_field():
    """Add Attachment field for TTS Audio to Projects table"""
    
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{table_id}/columns"
    
    payload = {
        "title": "TTS Audio",
        "column_name": "TTS Audio",
        "uidt": "Attachment",  # Attachment type
        "system": False
    }
    
    logger.info(f"Adding 'TTS Audio' field to table {table_id}...")
    logger.debug(f"Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("SUCCESS: Field added successfully!")
            logger.info(f"Field details: {data}")
        else:
            logger.error(f"FAILED: {response.status_code}")
            logger.error(f"Response text: {response.text}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    add_audio_attachment_field()
