import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from config import settings
from utils.logger import logger

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize the database with required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Projects Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    status TEXT DEFAULT 'New',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    target_duration INTEGER DEFAULT 3,
                    voice_id TEXT DEFAULT 'am_michael',
                    image_provider TEXT DEFAULT 'ComfyUI',
                    
                    -- Research Phase
                    research_content TEXT,
                    research_sources TEXT,
                    
                    -- Script Phase
                    script_content TEXT, -- Raw JSON or Markdown script
                    narrator_script TEXT, -- Just the spoken text
                    
                    -- Audio Phase
                    full_audio_path TEXT,
                    audio_duration REAL,
                    audio_timestamps TEXT, -- JSON string of timestamps
                    
                    -- ComfyUI Params
                    lora1_name TEXT,
                    lora1_strength REAL,
                    lora2_name TEXT,
                    lora2_strength REAL
                )
            """)

            # Chapters Table (for structured script storage)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    title TEXT,
                    content TEXT,
                    start_time REAL,
                    end_time REAL,
                    visual_desc TEXT,
                    image_path TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            conn.close()

    # --- Project Operations ---

    def create_project(self, topic: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO projects (topic, status) VALUES (?, ?)",
                (topic, "New")
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None
        finally:
            conn.close()

    def get_all_projects(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM projects ORDER BY id DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []
        finally:
            conn.close()

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None
        finally:
            conn.close()

    def update_project(self, project_id: int, data: Dict[str, Any]) -> bool:
        if not data:
            return False
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values())
        values.append(project_id)
        
        try:
            cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
            conn.commit()
            logger.info(f"Updated project {project_id}: {list(data.keys())}")
            return True
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return False
        finally:
            conn.close()

    def delete_project(self, project_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False
        finally:
            conn.close()

    # --- Chapter Operations ---
    
    def save_chapters(self, project_id: int, chapters: List[Dict[str, Any]]):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # First, clear existing chapters for this project (simple replacement strategy)
            cursor.execute("DELETE FROM chapters WHERE project_id = ?", (project_id,))
            
            for chap in chapters:
                cursor.execute("""
                    INSERT INTO chapters (
                        project_id, title, content, start_time, end_time, visual_desc, image_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    chap.get('title'),
                    chap.get('content'),
                    chap.get('start_time', 0.0),
                    chap.get('end_time', 0.0),
                    chap.get('visual_desc'),
                    chap.get('image_path')
                ))
            conn.commit()
            logger.info(f"Saved {len(chapters)} chapters for project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save chapters for project {project_id}: {e}")
            return False
        finally:
            conn.close()

    def get_chapters(self, project_id: int) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM chapters WHERE project_id = ? ORDER BY start_time ASC", (project_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get chapters for project {project_id}: {e}")
            return []
        finally:
            conn.close()

# Global instance
db = DatabaseManager()
