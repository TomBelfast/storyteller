import asyncio
import httpx
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings
from utils.logger import logger

async def create_tables():
    """
    Creates necessary tables in NocoDB if they don't exist.
    """
    logger.info("Initializing NocoDB Tables...")
    
    if not settings.NOCODB_API_URL or not settings.NOCODB_API_TOKEN:
        logger.error("NocoDB configuration missing.")
        return

    # We need the Project ID (NocoDB Project ID, not our app's project)
    # Usually this is part of the URL or a separate config. 
    # The guide mentions `projects/{project_id}/tables`.
    # Based on the user's .env, we have NOCODB_TABLE_ID but not NOCODB_PROJECT_ID.
    # However, the user provided NOCODB_TABLE_ID 'mfbhc6n0ctzg69o' which looks like a Table ID.
    # To create tables, we need the Project ID (Base ID).
    
    # Let's try to infer or ask.
    # Wait, the user provided a Table ID in .env: `NOCODB_TABLE_ID=mfbhc6n0ctzg69o`.
    # This might be the "Projects" table ID.
    # But to create NEW tables (like Chapters), we need the Base/Project ID.
    
    # Let's assume we can get the Project ID from the Table ID metadata if possible, 
    # OR we assume the user has a Project ID.
    # Looking at the guide: `GET /api/v1/db/meta/projects/{project_id}/tables`
    
    # I'll try to list projects first to find the ID.
    headers = {
        "xc-token": settings.NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Get Project ID (Base ID)
        # Endpoint: /api/v1/db/meta/projects
        try:
            resp = await client.get(f"{settings.NOCODB_API_URL}/api/v1/db/meta/projects", headers=headers)
            resp.raise_for_status()
            projects = resp.json().get("list", [])
            if not projects:
                logger.error("No NocoDB projects found.")
                return
            
            # Use the first project found for now, or match by name if we knew it
            project_id = projects[0]["id"]
            logger.info(f"Using NocoDB Project ID: {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to get NocoDB projects: {e}")
            return

        # 2. Define Tables
        tables_to_create = [
            {
                "table_name": "Projects",
                "title": "Projects",
                "columns": [
                    {"column_name": "id", "title": "Id", "dt": "integer", "dtx": "autoNumber", "pk": True},
                    {"column_name": "topic", "title": "Topic", "dt": "varchar", "dtxp": "255"},
                    {"column_name": "status", "title": "Status", "dt": "varchar", "dtxp": "50"},
                    {"column_name": "voice_id", "title": "Voice ID", "dt": "varchar", "dtxp": "50"},
                    {"column_name": "image_provider", "title": "Image Provider", "dt": "varchar", "dtxp": "50"},
                    {"column_name": "research_content", "title": "Research Content", "dt": "text"},
                    {"column_name": "research_sources", "title": "Research Sources", "dt": "text"},
                    {"column_name": "audio_url", "title": "Audio URL", "dt": "json"}, # Attachment
                    {"column_name": "lora1_name", "title": "LoRA 1 Name", "dt": "varchar", "dtxp": "100"},
                    {"column_name": "lora1_strength", "title": "LoRA 1 Strength", "dt": "decimal", "dtxp": "5,2"},
                ]
            },
            {
                "table_name": "Chapters",
                "title": "Chapters",
                "columns": [
                    {"column_name": "id", "title": "Id", "dt": "integer", "dtx": "autoNumber", "pk": True},
                    {"column_name": "project_id", "title": "Project ID", "dt": "varchar", "dtxp": "255"}, # Link to Project
                    {"column_name": "title", "title": "Title", "dt": "varchar", "dtxp": "255"},
                    {"column_name": "content", "title": "Content", "dt": "text"},
                    {"column_name": "start_time", "title": "Start Time", "dt": "decimal", "dtxp": "10,2"},
                    {"column_name": "end_time", "title": "End Time", "dt": "decimal", "dtxp": "10,2"},
                    {"column_name": "visual_desc", "title": "Visual Desc", "dt": "text"},
                    {"column_name": "image_path", "title": "Image Path", "dt": "varchar", "dtxp": "500"},
                ]
            }
        ]
        
        # 3. Create Tables
        for table_def in tables_to_create:
            try:
                # Check if table exists
                # Simplified: Just try to create and catch error if exists
                url = f"{settings.NOCODB_API_URL}/api/v1/db/meta/projects/{project_id}/tables"
                
                # Ensure ID is first (it is in definition)
                payload = {
                    "table_name": table_def["table_name"],
                    "title": table_def["title"],
                    "columns": table_def["columns"]
                }
                
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    logger.info(f"Table '{table_def['title']}' created successfully.")
                else:
                    logger.warning(f"Table '{table_def['title']}' creation status: {resp.status_code} - {resp.text}")
                    
            except Exception as e:
                logger.error(f"Error creating table '{table_def['title']}': {e}")

if __name__ == "__main__":
    asyncio.run(create_tables())
