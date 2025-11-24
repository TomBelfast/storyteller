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

    @ai_supervisor()
    def plan_shots(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Divides chapters into shots and creates prompts (without generating images).
        """
        logger.info("Director planning shots...")
        
        for chapter in chapters:
            # Clear existing shots to avoid duplication if re-planning
            chapter.shots = []
            
            duration = chapter.end_time - chapter.start_time
            # Simple logic: 1 shot every 5 seconds
            num_shots = max(1, int(duration / 5))
            shot_duration = duration / num_shots
            
            current_time = chapter.start_time
            
            for i in range(num_shots):
                # 1. Create Shot Object
                visual_desc = f"Visual for {chapter.title} part {i+1}" # Placeholder for real AI description
                
                prompt_template = prompt_manager.get_prompt("visual_comfy_template")
                prompt = prompt_template.format(title=chapter.title, visual_desc=visual_desc)
                
                shot = Shot(
                    visual_desc=visual_desc,
                    comfy_prompt=prompt,
                    start_time=current_time,
                    duration=shot_duration
                )
                
                chapter.shots.append(shot)
                current_time += shot_duration
                
        return chapters

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
