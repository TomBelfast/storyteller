import requests
from config import settings
from utils.logger import logger
from modules.audio_engine import AudioEngine
from modules.pipeline_manager import PipelineManager
import json
import os

def test_phase_4():
    """Test Phase 4 - Audio Generation and Save"""
    
    project_id = 5
    api_url = settings.NOCODB_API_URL
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    logger.info("=" * 60)
    logger.info("PHASE 4 TEST: Audio Generation")
    logger.info("=" * 60)
    
    # STEP 1: Fetch Narrator Script
    logger.info(f"Step 1: Fetching Narrator Script from Project {project_id}...")
    resp = requests.get(
        f"{api_url}/api/v2/tables/{table_id}/records/{project_id}",
        headers=headers
    )
    
    if resp.status_code != 200:
        logger.error(f"Failed to fetch project: {resp.status_code}")
        return
    
    project_data = resp.json()
    narrator_script = project_data.get(settings.NOCODB_FIELDS["project"]["narrator_script"])
    
    if not narrator_script:
        logger.error("Narrator Script is NULL! Run Phase 3.5 first.")
        return
    
    logger.info(f"Narrator Script found: {len(narrator_script)} chars, {len(narrator_script.split())} words")
    logger.debug(f"Preview: {narrator_script[:200]}...")
    
    # STEP 2: Generate Audio
    logger.info("Step 2: Generating audio with Kokoro TTS...")
    audio_engine = AudioEngine()
    
    audio_path, timestamps = audio_engine.generate_master_audio(
        narrator_script,
        voice_id="am_michael"
    )
    
    if not audio_path or not os.path.exists(audio_path):
        logger.error(f"Audio generation failed! Path: {audio_path}")
        return
    
    logger.info(f"Audio file generated: {audio_path}")
    logger.info(f"File size: {os.path.getsize(audio_path)} bytes")
    logger.info(f"Timestamps received: {len(timestamps)}")
    logger.debug(f"First 3 timestamps: {timestamps[:3] if len(timestamps) > 0 else 'None'}")
    
    # STEP 3: Upload to NocoDB
    logger.info("Step 3: Uploading audio to NocoDB storage...")
    pipeline = PipelineManager()
    attachment_data = pipeline.upload_file(audio_path)
    
    if not attachment_data:
        logger.error("Audio upload failed!")
        return
    
    logger.info(f"Audio uploaded: {attachment_data}")
    
    # Extract URL
    audio_url = attachment_data[0].get("url") if isinstance(attachment_data, list) and len(attachment_data) > 0 else None
    logger.info(f"Audio URL: {audio_url}")
    
    # STEP 4: Calculate duration with 2 decimal places from MP3 metadata
    from mutagen.mp3 import MP3
    
    try:
        audio_file = MP3(audio_path)
        audio_duration = audio_file.info.length  # Duration in seconds (float)
        logger.info(f"Audio duration from MP3 metadata: {audio_duration}s")
    except Exception as e:
        logger.warning(f"Failed to read MP3 metadata: {e}. Using timestamp fallback.")
        # Fallback: use last timestamp's end_time
        audio_duration = max([t.get("end_time", 0) for t in timestamps]) if timestamps else len(narrator_script.split()) / 2.5
    
    audio_duration_rounded = round(audio_duration, 2)
    logger.info(f"Audio duration (rounded): {audio_duration_rounded}s")
    
    # STEP 5: Save all data to NocoDB
    logger.info(f"Step 4: Saving audio data to Project {project_id}...")
    
    # NOTE: Attachment fields (TTS Audio) cannot be updated via PATCH /records
    # They must be uploaded separately to storage (already done in Step 3)
    # Only update URL, timestamps, and duration
    payload = [{
        "Id": project_id,
        settings.NOCODB_FIELDS["project"]["audio_url"]: audio_url,
        settings.NOCODB_FIELDS["project"]["audio_timestamps"]: json.dumps(timestamps),
        settings.NOCODB_FIELDS["project"]["audio_duration"]: audio_duration_rounded
    }]
    
    logger.debug(f"Payload summary:")
    logger.debug(f"  - TTS Audio: {len(attachment_data)} attachments")
    logger.debug(f"  - Audio URL: {audio_url}")
    logger.debug(f"  - Audio Duration: {audio_duration_rounded}s")
    logger.debug(f"  - Timestamps: {len(timestamps)} items")
    
    update_resp = requests.patch(
        f"{api_url}/api/v2/tables/{table_id}/records",
        json=payload,
        headers=headers
    )
    
    logger.info(f"PATCH response: {update_resp.status_code}")
    
    if update_resp.status_code == 200:
        logger.info("SUCCESS! Audio data saved to NocoDB")
        
        # STEP 6: Verify
        logger.info("Step 5: Verifying saved data...")
        verify_resp = requests.get(
            f"{api_url}/api/v2/tables/{table_id}/records/{project_id}",
            headers=headers
        )
        
        if verify_resp.status_code == 200:
            verify_data = verify_resp.json()
            
            saved_audio = verify_data.get(settings.NOCODB_FIELDS["project"]["tts_audio"])
            saved_url = verify_data.get(settings.NOCODB_FIELDS["project"]["audio_url"])
            saved_duration = verify_data.get(settings.NOCODB_FIELDS["project"]["audio_duration"])
            saved_timestamps = verify_data.get(settings.NOCODB_FIELDS["project"]["audio_timestamps"])
            
            logger.info("VERIFICATION RESULTS:")
            logger.info(f"  - TTS Audio: {saved_audio if saved_audio else 'NULL'}")
            logger.info(f"  - Audio URL: {saved_url if saved_url else 'NULL'}")
            logger.info(f"  - Audio Duration: {saved_duration if saved_duration else 'NULL'}s")
            logger.info(f"  - Audio Timestamps: {'PRESENT' if saved_timestamps else 'NULL'} ({len(saved_timestamps) if saved_timestamps else 0} chars)")
            
            # Check decimal places
            if saved_duration:
                decimal_places = len(str(saved_duration).split('.')[-1]) if '.' in str(saved_duration) else 0
                logger.info(f"  - Duration decimal places: {decimal_places} (expected: 2)")
                
                if decimal_places == 2:
                    logger.info("PERFECT! Duration has 2 decimal places")
                else:
                    logger.warning(f"Duration has {decimal_places} decimal places, expected 2")
        else:
            logger.error(f"Verification GET failed: {verify_resp.status_code}")
    else:
        logger.error(f"FAILED to save: {update_resp.status_code}")
        logger.error(f"Response: {update_resp.text}")
    
    logger.info("=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    test_phase_4()
    print("\n✅ Test complete. Check logs/system_events.json for full output.")
