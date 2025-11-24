from typing import List, Optional, Union
from pydantic import BaseModel, Field
from config import settings

class Shot(BaseModel):
    visual_desc: str = Field(..., description="Visual description of the shot")
    comfy_prompt: str = Field(..., description="Prompt for ComfyUI")
    start_time: float = Field(..., description="Start time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    image_path: Optional[str] = Field(None, description="Path to generated image")

class Chapter(BaseModel):
    id: Optional[Union[str, int]] = None
    title: str = Field(..., description="Chapter title")
    content: str = Field(..., description="Chapter narration text")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    visual_desc: Optional[str] = None
    shots: List[Shot] = Field(default_factory=list)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    # NocoDB Mapping Helper - REMOVED (SQLite Migration)
    # def to_nocodb_json(self, project_id: str):
    #     ...

class Project(BaseModel):
    id: Optional[Union[str, int]] = None
    topic: str
    status: str = "New"
    target_duration: int = 3
    voice_id: str = "am_michael"
    full_audio_path: Optional[str] = None
    image_provider: str = "ComfyUI"
    
    # ComfyUI Specifics
    lora1_name: Optional[str] = None
    lora1_strength: float = 1.0
    lora2_name: Optional[str] = None
    lora2_strength: float = 1.0
    
    # Research
    research_content: Optional[str] = None
    research_sources: Optional[str] = None
    
    # Script
    narrator_script: Optional[str] = None
    
    chapters: List[Chapter] = Field(default_factory=list)
    
    # NocoDB Mapping Helper - REMOVED (SQLite Migration)
    # def to_nocodb_json(self):
    #     ...
