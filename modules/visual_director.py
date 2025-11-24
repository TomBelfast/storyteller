import requests
import json
import time
import os
import random
from typing import List, Dict, Any
from utils.logger import logger
from utils.ai_supervisor import ai_supervisor
from models import Chapter, Shot
from config import settings
from utils.prompt_manager import prompt_manager

class VisualDirector:
    def __init__(self):
        self.comfy_url = settings.COMFYUI_API_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.5-flash"

    @ai_supervisor()
    def plan_shots(self, chapters: List[Chapter], audio_timestamps: str = None) -> List[Chapter]:
        """
        Uses AI to plan coherent visual story for each chapter (like a comic/storyboard).
        AI decides scene transitions based on narrative flow, not arbitrary time segments.
        """
        logger.info("Director planning visual story with AI...")
        
        # Parse timestamps if available
        timestamps_data = None
        if audio_timestamps:
            try:
                timestamps_data = json.loads(audio_timestamps)
                logger.info(f"Loaded {len(timestamps_data)} word timestamps")
            except:
                logger.warning("Failed to parse audio timestamps, using fallback")
        
        for chapter in chapters:
            chapter.shots = []
            
            logger.info(f"Planning visual story for chapter: {chapter.title}")
            
            # Get AI to plan ALL scenes for this chapter at once
            scenes_plan = self._plan_chapter_visual_story(
                chapter=chapter,
                timestamps_data=timestamps_data
            )
            
            # Convert AI's scene plan to Shot objects
            for scene in scenes_plan:
                prompt_template = prompt_manager.get_prompt("visual_comfy_template")
                comfy_prompt = prompt_template.format(
                    title=chapter.title, 
                    visual_desc=scene.get("visual_description", "")
                )
                
                shot = Shot(
                    visual_desc=scene.get("visual_description", ""),
                    comfy_prompt=comfy_prompt,
                    start_time=scene.get("start_time", 0),
                    duration=scene.get("duration", 5.0)
                )
                
                chapter.shots.append(shot)
            
            logger.info(f"Created {len(chapter.shots)} shots for {chapter.title}")
                
        return chapters
    
    def _plan_chapter_visual_story(self, chapter: Chapter, timestamps_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Uses AI to plan complete visual narrative for a chapter.
        Returns list of scenes with timing and descriptions.
        """
        try:
            # Build full narrator text with timestamps
            narrator_segments = self._build_timestamped_narration(
                chapter, 
                timestamps_data
            )
            
            # Prepare prompt for AI
            chapter_duration = chapter.end_time - chapter.start_time
            
            prompt = f"""You are a visual director planning a documentary storyboard.

CHAPTER: {chapter.title}
CHAPTER START: {chapter.start_time:.1f}s
CHAPTER END: {chapter.end_time:.1f}s  
TOTAL CHAPTER DURATION: {chapter_duration:.1f} seconds

FULL NARRATION WITH TIMESTAMPS:
{narrator_segments}

TASK: Plan 4-8 visual scenes that cover THE ENTIRE CHAPTER DURATION ({chapter_duration:.1f}s).

CRITICAL RULES:
1. Each scene should be 4-8 seconds long (adjust based on content)
2. Scenes must be CONTINUOUS - no gaps!
3. First scene starts at {chapter.start_time:.1f}s
4. Last scene must end EXACTLY at {chapter.end_time:.1f}s
5. Each scene illustrates what the narrator says during that time
6. Create visual continuity like a comic/storyboard

EXAMPLE for a 30-second chapter:
[
  {{"start_time": 0.0, "duration": 7.5, "narrator_text": "...", "visual_description": "...", "shot_type": "wide"}},
  {{"start_time": 7.5, "duration": 6.0, "narrator_text": "...", "visual_description": "...", "shot_type": "medium"}},
  {{"start_time": 13.5, "duration": 8.5, "narrator_text": "...", "visual_description": "...", "shot_type": "close-up"}},
  {{"start_time": 22.0, "duration": 8.0, "narrator_text": "...", "visual_description": "...", "shot_type": "wide"}}
]

Return ONLY valid JSON array. No markdown, no explanations:
[
  {{
    "start_time": {chapter.start_time},
    "duration": 6.5,
    "narrator_text": "exact words from timestamps",
    "visual_description": "Detailed scene for AI image generator",
    "visual_continuity": "How this connects to previous/next",
    "shot_type": "wide/medium/close-up"
  }},
  ...
]
"""

            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Visual Storyteller"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(
                self.base_url, 
                json=payload, 
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            content = response.json()['choices'][0]['message']['content']
            
            # Parse JSON response
            content = content.replace("```json", "").replace("```", "").strip()
            scenes = json.loads(content)
            
            logger.info(f"AI planned {len(scenes)} scenes for chapter")
            logger.debug(f"Scene plan: {json.dumps(scenes, indent=2)}")
            
            return scenes
            
        except Exception as e:
            logger.error(f"AI visual story planning failed: {e}")
            logger.exception("Full error:")
            
            # Fallback: simple division
            duration = chapter.end_time - chapter.start_time
            num_scenes = max(1, int(duration / 5))
            scene_duration = duration / num_scenes
            
            fallback_scenes = []
            current_time = chapter.start_time
            
            for i in range(num_scenes):
                fallback_scenes.append({
                    "start_time": current_time,
                    "duration": scene_duration,
                    "narrator_text": f"Segment {i+1}",
                    "visual_description": f"Scene illustrating {chapter.title}, part {i+1}",
                    "shot_type": "medium"
                })
                current_time += scene_duration
            
            return fallback_scenes
    
    def _build_timestamped_narration(self, chapter: Chapter, timestamps_data: List[Dict]) -> str:
        """
        Builds a text representation of the narration with timestamps.
        """
        if not timestamps_data:
            # Fallback: just return content
            return chapter.content
        
        # Filter timestamps for this chapter's time range
        chapter_words = []
        for entry in timestamps_data:
            word_time = entry.get("start", 0)
            if chapter.start_time <= word_time <= chapter.end_time:
                chapter_words.append({
                    "time": word_time,
                    "word": entry.get("word", "")
                })
        
        # Build readable format
        if not chapter_words:
            return chapter.content
        
        # Group into ~10 second segments for readability
        segments = []
        current_segment = []
        last_time = chapter_words[0]["time"]
        
        for entry in chapter_words:
            current_segment.append(entry["word"])
            
            # New segment every ~10 seconds or 50 words
            if entry["time"] - last_time >= 10 or len(current_segment) >= 50:
                text = " ".join(current_segment)
                segments.append(f"[{last_time:.1f}s - {entry['time']:.1f}s] {text}")
                current_segment = []
                last_time = entry["time"]
        
        # Add remaining words
        if current_segment:
            text = " ".join(current_segment)
            segments.append(f"[{last_time:.1f}s - {chapter.end_time:.1f}s] {text}")
        
        return "\n\n".join(segments)

    @ai_supervisor()
    def generate_images_for_chapters(self, chapters: List[Chapter], project_id: str) -> List[Chapter]:
        """
        Iterates through chapters and shots, generating images for each.
        """
        logger.info("Director generating images for planned shots...")
        
        for chapter in chapters:
            for i, shot in enumerate(chapter.shots):
                if not shot.image_path: # Only generate if missing
                    logger.info(f"Generating image for shot {i} in chapter {chapter.title}")
                    image_path = self.generate_image(shot.comfy_prompt, project_id, f"{chapter.title}_{i}")
                    shot.image_path = image_path
                    
        return chapters

    # Keep backward compatibility for now if needed, or remove create_shots
    def create_shots(self, chapters: List[Chapter], project_id: str) -> List[Chapter]:
        """Legacy wrapper"""
        chapters = self.plan_shots(chapters)
        return self.generate_images_for_chapters(chapters, project_id)

    def generate_image(self, prompt_text: str, project_id: str, filename_prefix: str) -> str:
        """
        Sends prompt to ComfyUI and waits for image.
        """
        try:
            # 1. Build Workflow (Flux Dev Mockup - simplified for stability)
            # In real usage, we would load the full JSON workflow here
            workflow = self._build_workflow(prompt_text)
            
            # 2. Queue Prompt
            p = {"prompt": workflow}
            response = requests.post(f"{self.comfy_url}/prompt", json=p)
            response.raise_for_status()
            prompt_id = response.json().get("prompt_id")
            logger.info(f"ComfyUI Prompt Queued: {prompt_id}")
            
            # 3. Wait for Generation (Simplified polling)
            # For MVP, we'll wait a fixed time or implement status check
            # Real implementation needs WebSocket or polling /history
            time.sleep(2) # Wait for generation (MOCK WAIT for stability if server is slow)
            
            # 4. Retrieve Image (Mocking the retrieval for now as we don't have WebSocket listener implemented yet)
            # To do this properly requires listening to WS for 'execution_success'
            # For now, we will return a placeholder path or try to fetch latest
            
            # TODO: Implement full WebSocket listener for ComfyUI
            logger.warning("ComfyUI Image Retrieval not fully implemented (requires WebSocket). Returning placeholder.")
            return f"output/{filename_prefix}.png"
            
        except Exception as e:
            logger.error(f"ComfyUI Generation Failed: {e}")
            return "output/placeholder.png"

    def _build_workflow(self, text: str) -> Dict[str, Any]:
        """
        Returns a simplified ComfyUI workflow JSON.
        """
        # This is a minimal valid workflow structure
        # User needs to provide their specific workflow JSON structure
        # I will use a generic placeholder structure based on the guide
        return {
            "3": {
                "inputs": {
                    "seed": random.randint(1, 1000000000),
                    "steps": 20,
                    "cfg": 8,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "ckpt_name": "flux1-dev-fp8.safetensors" # Updated to available model
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {
                    "text": text,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": "text, watermark",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage"
            }
        }
