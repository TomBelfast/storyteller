import os
import sys
import time
from loguru import logger
from models import Project
from modules.pipeline_manager import PipelineManager
from utils.database import db

# Mock Streamlit Sink to capture logs
class MockSink:
    def __init__(self):
        self.logs = []

    def write(self, message):
        print(f"[UI LOG] {message.strip()}")
        self.logs.append(message)

def simulate_workflow():
    print("--- Starting Streamlit Workflow Simulation ---")

    # 1. Setup Logging
    print("1. Setting up Logging...")
    sink = MockSink()
    handler_id = logger.add(sink.write, format="{time:HH:mm:ss} | {level} | {message}")

    # 2. Initialize Pipeline
    print("2. Initializing Pipeline...")
    pipeline = PipelineManager()

    # 3. Create Project Data (Simulating Form Input)
    topic = "The Secret Life of Bees"
    print(f"3. Creating Project Data for topic: '{topic}'...")
    project_data = Project(
        topic=topic,
        target_duration=1, # Short duration for testing
        voice_id="am_michael",
        image_provider="ComfyUI", # or Mock if ComfyUI is not available/wanted
        lora1_name="macro_photography",
        lora1_strength=0.8
    )

    # 4. Run Production
    print("4. Running Full Production (this may take a moment)...")
    try:
        project = pipeline.run_full_production(project_data)
        print("   Production finished successfully.")
    except Exception as e:
        print(f"   Production FAILED: {e}")
        logger.exception("Simulation failed")
        return

    # 5. Verify Database Persistence
    print("5. Verifying Database Persistence...")
    
    # Check Project
    saved_project = db.get_project(int(project.id))
    if saved_project:
        print(f"   [OK] Project found in DB: ID {saved_project['id']}")
        print(f"        Status: {saved_project['status']}")
        print(f"        Audio Path: {saved_project['full_audio_path']}")
        print(f"        Audio Duration: {saved_project['audio_duration']}")
    else:
        print("   [FAIL] Project NOT found in DB.")
        return

    # Check Chapters
    chapters = db.get_chapters(int(project.id))
    if chapters:
        print(f"   [OK] Found {len(chapters)} chapters in DB.")
        for i, chap in enumerate(chapters):
            print(f"        - Chapter {i+1}: {chap['title']} ({chap['start_time']}s - {chap['end_time']}s)")
    else:
        print("   [FAIL] No chapters found in DB.")

    # 6. Verify Files
    print("6. Verifying Files...")
    if saved_project['full_audio_path'] and os.path.exists(saved_project['full_audio_path']):
        print(f"   [OK] Audio file exists: {saved_project['full_audio_path']}")
    else:
        print(f"   [FAIL] Audio file missing: {saved_project['full_audio_path']}")

    # Cleanup
    logger.remove(handler_id)
    print("--- Simulation Complete ---")

if __name__ == "__main__":
    simulate_workflow()
