import requests
from config import settings
from utils.logger import logger
import json

def add_audio_fields():
    """Add all required audio fields to Projects table"""
    
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    base_url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{table_id}/columns"
    
    fields_to_add = [
        {
            "title": "TTS Audio",
            "column_name": "TTS_Audio",  # No spaces in column_name
            "uidt": "Attachment"
        },
        {
            "title": "Audio Timestamps",
            "column_name": "Audio_Timestamps",
            "uidt": "LongText"  # For JSON data
        },
        {
            "title": "Audio Duration",
            "column_name": "Audio_Duration",
            "uidt": "Number",
            "meta": {
                "precision": 2  # 2 decimal places for seconds
            }
        }
    ]
    
    logger.info(f"Adding {len(fields_to_add)} audio fields to table {table_id}...")
    
    for field in fields_to_add:
        logger.info(f"Adding field: {field['title']}...")
        
        try:
            response = requests.post(base_url, json=field, headers=headers)
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"SUCCESS: '{field['title']}' added!")
            elif response.status_code == 400:
                error_data = response.json()
                if "already exists" in response.text.lower():
                    logger.warning(f"Field '{field['title']}' already exists, skipping.")
                else:
                    logger.error(f"FAILED: {response.status_code}")
                    logger.error(f"Response: {response.text}")
            else:
                logger.error(f"FAILED: {response.status_code}")
                logger.error(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"Error adding '{field['title']}': {e}")
    
    logger.info("Field addition complete. Verifying...")
    
    # Verify by fetching table schema
    try:
        schema_url = f"{settings.NOCODB_API_URL}/api/v2/meta/tables/{table_id}"
        resp = requests.get(schema_url, headers=headers)
        if resp.status_code == 200:
            schema = resp.json()
            fields = schema.get("fields", [])
            audio_fields = [f for f in fields if "Audio" in f.get("title", "") or "TTS" in f.get("title", "")]
            logger.info(f"Found {len(audio_fields)} audio-related fields:")
            for f in audio_fields:
                logger.info(f"  - {f.get('title')} ({f.get('type')})")
    except Exception as e:
        logger.error(f"Verification error: {e}")

if __name__ == "__main__":
    add_audio_fields()
    print("Check logs/system_events.json for full output.")
