import requests
import os
from typing import List, Dict, Any
from utils.logger import logger
from utils.ai_supervisor import ai_supervisor
from modules.research_engine import ResearchEngine
from modules.script_engine import ScriptEngine
from modules.audio_engine import AudioEngine
from modules.visual_director import VisualDirector
from models import Project
from config import settings

import os
import json
from typing import List, Dict, Any
from utils.logger import logger
from utils.ai_supervisor import ai_supervisor
from modules.research_engine import ResearchEngine
from modules.script_engine import ScriptEngine
from modules.audio_engine import AudioEngine
from modules.visual_director import VisualDirector
from models import Project
from services import create_story, update_story
from utils.database import db

class PipelineManager:
    def __init__(self):
        self.research_engine = ResearchEngine()
        self.script_engine = ScriptEngine()
        self.audio_engine = AudioEngine()
        self.visual_director = VisualDirector()

    @ai_supervisor()
    def initialize_project(self, project: Project) -> Project:
        """
        Creates a new project record in SQLite.
        """
        logger.info(f"Initializing project in SQLite: {project.topic}")
        
        project_id = create_story(project.topic)
        if project_id:
            project.id = str(project_id)
            logger.info(f"Created SQLite record: {project.id}")
        else:
            logger.error("Failed to create SQLite record")
            project.id = "ERROR"
            
        return project

    @ai_supervisor()
    def run_research_phase(self, project: Project) -> Project:
        logger.info(f"Starting Research Phase for: {project.topic}")
        research_data = self.research_engine.run_research(project.topic)
        project.research_content = research_data["content"]
        project.research_sources = research_data["sources"]
        
        update_story(
            int(project.id), 
            research_data=project.research_content,
            research_sources=project.research_sources
        )
        return project

    @ai_supervisor()
    def run_script_phase(self, project: Project) -> Project:
        logger.info(f"Starting Script Phase for: {project.topic}")
        chapters = self.script_engine.generate_scripts(project.id, project.research_content, project.target_duration)
        project.chapters = chapters
        
        # Save Chapters to SQLite
        chapters_data = [c.dict() for c in chapters]
        db.save_chapters(int(project.id), chapters_data)
        
        # Update script content in project record (NO markdown headers)
        full_script = "\n\n".join([c.content for c in chapters])
        update_story(int(project.id), script_content=full_script)
        return project

    @ai_supervisor()
    def run_audio_phase(self, project: Project) -> Project:
        logger.info(f"Starting Audio Phase for: {project.topic}")
        
        # CRITICAL: Use script_content from DB (the full, edited script)
        # NOT chapters, as chapters might be stale or incomplete
        from services import get_story
        project_data = get_story(int(project.id))
        
        if not project_data:
            logger.error(f"Project {project.id} not found in database.")
            return project
            
        full_text = project_data.get('script_content', '')
        
        if not full_text:
            logger.error("No script_content available for audio generation.")
            logger.warning("Attempting fallback: concatenating chapters...")
            
            # Fallback to chapters if script_content is missing
            if not project.chapters:
                chapters_data = db.get_chapters(int(project.id))
                if chapters_data:
                    full_text = "\n\n".join([c.get('content', '') for c in chapters_data])
            else:
                full_text = "\n\n".join([c.content for c in project.chapters])
                
        if not full_text:
            logger.error("Still no script content after fallback. Aborting audio generation.")
            return project

        audio_path, timestamps = self.audio_engine.generate_master_audio(full_text, project.voice_id)
        project.full_audio_path = audio_path
        
        # Calculate total duration
        if timestamps and isinstance(timestamps, list) and len(timestamps) > 0:
            last_ts = timestamps[-1]
            duration = last_ts.get('end', last_ts.get('end_time', 0.0))
        else:
            duration = 0.0
        
        update_story(
            int(project.id),
            full_audio_path=audio_path,
            audio_duration=duration,
            audio_timestamps=json.dumps(timestamps)
        )
        logger.info(f"Saved audio data for project {project.id}")

        # Map timestamps
        if not project.chapters:
            logger.info("Loading chapters from DB for timestamp mapping...")
            chapters_data = db.get_chapters(int(project.id))
            if chapters_data:
                from models import Chapter
                project.chapters = [Chapter(**c) for c in chapters_data]
        
        if project.chapters:
            project.chapters = self.audio_engine.map_timestamps_to_chapters(timestamps, project.chapters)
            
            # Update chapters with new timings
            chapters_data = [c.dict() for c in project.chapters]
            db.save_chapters(int(project.id), chapters_data)
        
        return project

    @ai_supervisor()
    def run_visuals_phase(self, project: Project) -> Project:
        logger.info(f"Starting Visuals Phase for: {project.topic}")
        if project.chapters:
            project.chapters = self.visual_director.create_shots(project.chapters, project.id)
            
            # Final Chapter Update with Visuals
            chapters_data = [c.dict() for c in project.chapters]
            db.save_chapters(int(project.id), chapters_data)
        return project

    @ai_supervisor()
    def run_full_production(self, project: Project) -> Project:
        """
        Runs the full video production pipeline sequentially.
        """
        logger.info(f"Starting full production for topic: {project.topic}")
        
        # 0. Init (SQLite)
        project = self.initialize_project(project)
        if project.id == "ERROR":
            return project
        
        # 1. Research
        project = self.run_research_phase(project)
        
        # 2. Script
        project = self.run_script_phase(project)
        
        # 3. Audio
        project = self.run_audio_phase(project)
        
        # 4. Visuals
        project = self.run_visuals_phase(project)
        
        logger.info("Full production completed successfully.")
        return project
