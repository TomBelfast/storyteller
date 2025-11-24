import requests
from config import settings
from utils.logger import logger
import json

def test_cleanup_and_save():
    """Test the cleanup and save logic without calling LLM"""
    
    api_url = settings.NOCODB_API_URL
    chapters_table_id = "m3bzlwkrgoaxb36"
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    project_id = 5  # Your test project ID
    
    logger.info("=" * 60)
    logger.info("STEP 1: Fetch all existing chapters")
    logger.info("=" * 60)
    
    list_resp = requests.get(
        f"{api_url}/api/v2/tables/{chapters_table_id}/records?limit=100",
        headers=headers
    )
    
    if list_resp.status_code == 200:
        data = list_resp.json()
        all_chapters = data.get("list", [])
        logger.info(f"Found {len(all_chapters)} chapters in table")
        
        if all_chapters:
            logger.info("Chapters:")
            for ch in all_chapters:
                logger.info(f"  - ID: {ch['Id']}, Title: {ch.get('Title', 'N/A')[:50]}")
        
        # STEP 2: Delete all chapters
        if all_chapters:
            logger.info("=" * 60)
            logger.info("STEP 2: Delete all existing chapters")
            logger.info("=" * 60)
            
            all_ids = [r["Id"] for r in all_chapters]
            del_payload = [{"Id": i} for i in all_ids]
            
            logger.debug(f"Delete payload: {del_payload}")
            
            del_resp = requests.delete(
                f"{api_url}/api/v2/tables/{chapters_table_id}/records",
                json=del_payload,
                headers=headers
            )
            
            logger.info(f"DELETE response status: {del_resp.status_code}")
            if del_resp.status_code == 200:
                logger.info(f"Successfully deleted {len(all_ids)} chapters")
            else:
                logger.error(f"DELETE failed: {del_resp.status_code}")
                logger.error(f"Response: {del_resp.text}")
                return
        
        # STEP 3: Verify deletion
        logger.info("=" * 60)
        logger.info("STEP 3: Verify deletion")
        logger.info("=" * 60)
        
        verify_resp = requests.get(
            f"{api_url}/api/v2/tables/{chapters_table_id}/records?limit=100",
            headers=headers
        )
        
        if verify_resp.status_code == 200:
            verify_data = verify_resp.json()
            remaining = verify_data.get("list", [])
            logger.info(f"Remaining chapters in table: {len(remaining)}")
            if len(remaining) == 0:
                logger.info("Table is empty - deletion successful!")
            else:
                logger.warning(f"Still {len(remaining)} chapters remaining")
        
        # STEP 4: Test saving new chapters (mock data)
        logger.info("=" * 60)
        logger.info("STEP 4: Test saving mock chapters")
        logger.info("=" * 60)
        
        mock_chapters = [
            {
                "Title": "Test Chapter 1",
                "Content": "This is test content for chapter 1.",
                "Projects": [{"Id": int(project_id)}],
                "StartTime": 0.0,
                "EndTime": 10.0
            },
            {
                "Title": "Test Chapter 2",
                "Content": "This is test content for chapter 2.",
                "Projects": [{"Id": int(project_id)}],
                "StartTime": 10.0,
                "EndTime": 20.0
            }
        ]
        
        saved_count = 0
        for i, chapter_payload in enumerate(mock_chapters):
            logger.info(f"Saving chapter {i+1}...")
            logger.debug(f"Payload: {json.dumps(chapter_payload, indent=2)}")
            
            resp = requests.post(
                f"{api_url}/api/v2/tables/{chapters_table_id}/records",
                json=chapter_payload,
                headers=headers
            )
            
            logger.info(f"POST response status: {resp.status_code}")
            if resp.status_code == 200:
                chapter_data = resp.json()
                logger.info(f"Saved with ID: {chapter_data.get('Id')}")
                saved_count += 1
            else:
                logger.error(f"Failed to save chapter {i+1}: {resp.status_code}")
                logger.error(f"Response: {resp.text}")
        
        logger.info("=" * 60)
        logger.info(f"RESULT: Saved {saved_count}/{len(mock_chapters)} chapters")
        logger.info("=" * 60)
        
    else:
        logger.error(f"Failed to list chapters: {list_resp.status_code}")
        logger.error(f"Response: {list_resp.text}")

if __name__ == "__main__":
    test_cleanup_and_save()
    print("✅ Test completed. Check logs/system_events.json for full output.")
