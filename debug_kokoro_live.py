import requests
import json
import base64
import os
import sys
from config import settings
from utils.logger import logger

def debug_kokoro_live():
    logger.info("="*80)
    logger.info("🚀 STARTING LIVE KOKORO DEBUG")
    logger.info("="*80)

    # 1. Fetch Script
    api_url = settings.NOCODB_API_URL
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    project_id = 5

    logger.info(f"Fetching record {project_id} from table {table_id}...")
    try:
        resp = requests.get(f"{api_url}/api/v2/tables/{table_id}/records/{project_id}", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        narrator_script = data.get(settings.NOCODB_FIELDS["project"]["narrator_script"])
        
        if not narrator_script:
            logger.error("❌ Narrator script is EMPTY in NocoDB!")
            return
            
        logger.info(f"✅ Script fetched. Length: {len(narrator_script)} chars")
        logger.info(f"Script preview (first 100): {narrator_script[:100]}")
        logger.info(f"Script preview (last 100): {narrator_script[-100:]}")
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch script: {e}")
        return

    # 2. Prepare Payload
    payload = {
        "input": narrator_script,
        "voice": "am_michael",
        "speed": 1.0
    }
    
    # Log EXACT payload details
    logger.info("📦 PAYLOAD PREPARATION:")
    logger.info(f"Input length in payload: {len(payload['input'])}")
    logger.info(f"Voice: {payload['voice']}")
    logger.info(f"Speed: {payload['speed']}")
    
    # 3. Send to Kokoro
    logger.info(f"📡 Sending request to {settings.KOKORO_TTS_URL}...")
    try:
        # Increased timeout to 300s just in case
        response = requests.post(settings.KOKORO_TTS_URL, json=payload, timeout=300)
        
        logger.info(f"⬅️ Response Status: {response.status_code}")
        logger.info(f"⬅️ Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"❌ API Error: {response.text[:1000]}")
            return

        # 4. Analyze Response
        content_length = len(response.content)
        logger.info(f"⬅️ Response Content Length: {content_length} bytes")
        
        # Try parsing
        try:
            # Check if it's NDJSON or standard JSON
            text_content = response.text
            lines = text_content.strip().split('\n')
            logger.info(f"📄 Response Line Count: {len(lines)}")
            
            all_timestamps = []
            audio_found = False
            
            for i, line in enumerate(lines):
                if not line.strip(): continue
                
                try:
                    line_json = json.loads(line)
                    
                    # Check for audio
                    if "audio" in line_json:
                        audio_len = len(line_json["audio"])
                        logger.info(f"   Line {i}: Found AUDIO data (length: {audio_len})")
                        audio_found = True
                        
                    # Check for timestamps
                    if "timestamps" in line_json:
                        ts = line_json["timestamps"]
                        count = len(ts)
                        all_timestamps.extend(ts)
                        first_word = ts[0]['word'] if count > 0 else "N/A"
                        last_word = ts[-1]['word'] if count > 0 else "N/A"
                        logger.info(f"   Line {i}: Found {count} timestamps. Range: '{first_word}' ... '{last_word}'")
                        
                except json.JSONDecodeError:
                    logger.error(f"   Line {i}: Failed to parse JSON")

            logger.info(f"📊 TOTAL TIMESTAMPS RECEIVED: {len(all_timestamps)}")
            
            if len(all_timestamps) > 0:
                last_ts = all_timestamps[-1]
                logger.info(f"⏱️ Final Timestamp: {last_ts}")
                logger.info(f"⏱️ Calculated Duration: {last_ts.get('end_time', last_ts.get('end', 0))}s")
            
            if not audio_found:
                logger.error("❌ NO AUDIO DATA FOUND IN RESPONSE")
            
        except Exception as e:
            logger.error(f"❌ Error parsing response: {e}")
            
    except Exception as e:
        logger.error(f"❌ Request failed: {e}")

if __name__ == "__main__":
    debug_kokoro_live()
    
    # READ BACK THE LOGS TO STDOUT so we can see them in the tool output
    print("\n" + "="*40 + " LOG OUTPUT " + "="*40)
    try:
        with open('logs/system_events.json', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Filter for our specific logs from this run
            for line in lines[-50:]:
                if "debug_kokoro_live" in line or "KOKORO" in line or "Response" in line or "Script" in line:
                    data = json.loads(line)
                    print(f"{data['record']['time']['repr']} - {data['record']['message']}")
    except Exception as e:
        print(f"Could not read logs: {e}")
