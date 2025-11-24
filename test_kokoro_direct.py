"""
Direct Kokoro TTS API test with full logging
"""
import requests
import json
from config import settings
from utils.logger import logger

# Get Narrator Script
api_url = settings.NOCODB_API_URL
headers = {"xc-token": settings.NOCODB_API_TOKEN}
resp = requests.get(
    f"{api_url}/api/v2/tables/{settings.NOCODB_PROJECTS_TABLE_ID}/records/5",
    headers=headers
)
data = resp.json()
narrator_script = data.get(settings.NOCODB_FIELDS["project"]["narrator_script"])

logger.info("=" * 60)
logger.info("DIRECT KOKORO TTS API TEST")
logger.info("=" * 60)
logger.info(f"Narrator Script: {len(narrator_script)} chars, {len(narrator_script.split())} words")
logger.debug(f"First 300 chars: {narrator_script[:300]}...")
logger.debug(f"Last 100 chars: ...{narrator_script[-100:]}")

# Prepare payload
payload = {
    "input": narrator_script,
    "voice": "am_michael",
    "speed": 1.0
}

logger.info(f"Sending request to: {settings.KOKORO_TTS_URL}")
logger.debug(f"Payload: input={len(payload['input'])} chars, voice={payload['voice']}, speed={payload['speed']}")

# Send request
try:
    response = requests.post(settings.KOKORO_TTS_URL, json=payload, timeout=120)
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    logger.info(f"Response size: {len(response.content)} bytes")
    
    # Log first 500 chars of response
    logger.debug(f"Response text (first 500 chars): {response.text[:500]}")
    
    # Try to parse
    try:
        json_data = response.json()
        logger.info("Response parsed as single JSON")
        logger.info(f"Keys: {list(json_data.keys())}")
        
        if "timestamps" in json_data:
            ts_count = len(json_data["timestamps"])
            logger.info(f"Timestamps count: {ts_count}")
            if ts_count > 0:
                logger.debug(f"First timestamp: {json_data['timestamps'][0]}")
                logger.debug(f"Last timestamp: {json_data['timestamps'][-1]}")
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSONDecodeError: {e}")
        logger.info("Attempting NDJSON parsing...")
        
        lines = response.text.strip().split('\n')
        logger.info(f"Response has {len(lines)} lines")
        
        for i, line in enumerate(lines[:5]):  # First 5 lines
            logger.debug(f"Line {i+1} (first 200 chars): {line[:200]}")
            
except Exception as e:
    logger.error(f"Request failed: {e}")
    logger.exception("Full traceback:")

logger.info("=" * 60)
logger.info("TEST COMPLETE")
logger.info("=" * 60)
