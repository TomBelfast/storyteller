import requests
from config import settings
from utils.logger import logger

def test_phase_35():
    """Test Phase 3.5 - Consolidate & Save Narrator Script"""
    
    project_id = 5  # Your test project
    api_url = settings.NOCODB_API_URL
    chapters_table_id = "m3bzlwkrgoaxb36"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    logger.info("=" * 60)
    logger.info("PHASE 3.5 TEST: Consolidate Narrator Script")
    logger.info("=" * 60)
    
    # STEP 1: Fetch all chapters
    logger.info(f"Step 1: Fetching chapters from table {chapters_table_id}...")
    resp = requests.get(
        f"{api_url}/api/v2/tables/{chapters_table_id}/records?limit=100",
        headers=headers
    )
    
    if resp.status_code != 200:
        logger.error(f"Failed to fetch chapters: {resp.status_code}")
        logger.error(f"Response: {resp.text}")
        return
    
    data = resp.json()
    all_chapters = data.get("list", [])
    logger.info(f"Fetched {len(all_chapters)} total chapters from table")
    
    # STEP 2: Filter & Consolidate
    # Note: We're getting ALL chapters - in production would filter by project
    project_chapters = [ch for ch in all_chapters if ch.get("Id") is not None and ch.get("Content")]
    
    logger.info(f"Found {len(project_chapters)} chapters with content")
    
    if not project_chapters:
        logger.error("No chapters found!")
        return
    
    # Consolidate text
    consolidated_text = " ".join([ch.get("Content", "") for ch in project_chapters])
    
    # STEP 3: Validate
    word_count = len(consolidated_text.split())
    char_count = len(consolidated_text)
    
    logger.info(f"Step 2: Consolidated text stats:")
    logger.info(f"  - Characters: {char_count}")
    logger.info(f"  - Words: {word_count}")
    logger.info(f"  - Estimated duration: {word_count / 2.5:.1f}s (~{word_count / 150:.1f} min)")
    logger.info(f"  - Preview (first 200 chars): {consolidated_text[:200]}...")
    
    # Validation checks
    validation_ok = True
    if char_count < 100:
        logger.error("Validation FAILED: Text too short (< 100 chars)")
        validation_ok = False
    if word_count < 50:
        logger.error("Validation FAILED: Too few words (< 50)")
        validation_ok = False
    
    if not validation_ok:
        logger.error("Validation failed. Aborting.")
        return
    
    logger.info("Step 3: Validation PASSED!")
    
    # STEP 4: Save to Narrator Script
    logger.info(f"Step 4: Saving to Narrator Script field for Project {project_id}...")
    
    payload = [{
        "Id": project_id,
        settings.NOCODB_FIELDS["project"]["narrator_script"]: consolidated_text
    }]
    
    logger.debug(f"Payload keys: Id={project_id}, field='{settings.NOCODB_FIELDS['project']['narrator_script']}'")
    logger.debug(f"Text length in payload: {len(consolidated_text)} chars")
    
    update_resp = requests.patch(
        f"{api_url}/api/v2/tables/{settings.NOCODB_PROJECTS_TABLE_ID}/records",
        json=payload,
        headers=headers
    )
    
    logger.info(f"PATCH response status: {update_resp.status_code}")
    
    if update_resp.status_code == 200:
        logger.info(f"SUCCESS! Narrator Script saved ({word_count} words)")
        
        # STEP 5: Verify
        logger.info("Step 5: Verifying save...")
        verify_resp = requests.get(
            f"{api_url}/api/v2/tables/{settings.NOCODB_PROJECTS_TABLE_ID}/records/{project_id}",
            headers=headers
        )
        
        if verify_resp.status_code == 200:
            verify_data = verify_resp.json()
            saved_script = verify_data.get(settings.NOCODB_FIELDS["project"]["narrator_script"])
            
            if saved_script:
                saved_word_count = len(saved_script.split())
                logger.info(f"VERIFIED: Narrator Script exists in DB ({saved_word_count} words)")
                logger.info(f"Preview: {saved_script[:200]}...")
                
                if saved_word_count == word_count:
                    logger.info("PERFECT MATCH! Word counts are identical.")
                else:
                    logger.warning(f"Word count mismatch: sent={word_count}, saved={saved_word_count}")
            else:
                logger.error("VERIFICATION FAILED: Narrator Script is NULL in DB!")
        else:
            logger.error(f"Verification GET failed: {verify_resp.status_code}")
    else:
        logger.error(f"FAILED to save: {update_resp.status_code}")
        logger.error(f"Response: {update_resp.text}")
    
    logger.info("=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    test_phase_35()
    print("\n✅ Test complete. Run 'python dump_logs.py' then check LATEST_LOGS.txt for full output.")
