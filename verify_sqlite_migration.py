import os
import sys
from utils.database import db
from services import create_story, update_story, delete_story, get_all_stories

def test_sqlite_migration():
    print("--- Starting SQLite Migration Verification ---")
    
    # 1. Initialize DB
    print("1. Initializing Database...")
    try:
        db.init_db()
        print("   Database initialized.")
    except Exception as e:
        print(f"   FAILED to initialize database: {e}")
        return

    # 2. Create Project
    topic = "Test SQLite Migration"
    print(f"2. Creating Project: '{topic}'...")
    project_id = create_story(topic)
    if project_id:
        print(f"   Project created with ID: {project_id}")
    else:
        print("   FAILED to create project.")
        return

    # 3. Verify Project Exists
    print("3. Verifying Project Exists...")
    projects = get_all_stories()
    found = False
    for p in projects:
        if p['id'] == project_id and p['topic'] == topic:
            found = True
            print(f"   Found project: {p}")
            break
    if not found:
        print("   FAILED to find created project.")
        return

    # 4. Update Project (Research & Script)
    print("4. Updating Project (Research & Script)...")
    success = update_story(project_id, research_data="Some research content", script_content="Some script content")
    if success:
        print("   Update successful.")
    else:
        print("   FAILED to update project.")
        return

    # 5. Update Project (Audio Fields - The Critical Test)
    print("5. Updating Project (Audio Fields)...")
    audio_duration = 123.45
    audio_timestamps = '[{"word": "hello", "start": 0, "end": 1}]'
    success = update_story(project_id, audio_duration=audio_duration, audio_timestamps=audio_timestamps)
    if success:
        print("   Audio update successful.")
    else:
        print("   FAILED to update audio fields.")
        return

    # 6. Verify Persistence
    print("6. Verifying Persistence...")
    project = db.get_project(project_id)
    if project:
        print(f"   Retrieved Project: {project}")
        if project['audio_duration'] == audio_duration and project['audio_timestamps'] == audio_timestamps:
            print("   SUCCESS: Audio fields persisted correctly!")
        else:
            print(f"   FAILURE: Audio fields mismatch. Expected {audio_duration}, got {project.get('audio_duration')}")
    else:
        print("   FAILED to retrieve project.")

    # 7. Delete Project
    print("7. Deleting Project...")
    success = delete_story(project_id)
    if success:
        print("   Delete successful.")
    else:
        print("   FAILED to delete project.")

    # 8. Verify Deletion
    print("8. Verifying Deletion...")
    project = db.get_project(project_id)
    if project is None:
        print("   SUCCESS: Project deleted.")
    else:
        print("   FAILURE: Project still exists.")

    print("--- Verification Complete ---")

if __name__ == "__main__":
    test_sqlite_migration()
