import json
import os
from typing import Dict
from utils.logger import logger

PROMPTS_FILE = "prompts.json"

DEFAULT_PROMPTS = {
    "research_system": """You are an expert researcher for a documentary series. Provide detailed, factual, and engaging research on the requested topic. Include key dates, figures, and interesting anecdotes. Format the output clearly.""",
    
    "script_outline": """You are an expert documentary director. Plan a {duration}-minute video based on the following research:

{research_data}

Create a list of chapter titles for this video. 
The structure should be logical and engaging.
Return ONLY a JSON array of strings, e.g.: ["Introduction", "The Conflict", "Resolution"]""",

    "script_chapter": """You are a professional documentary narrator writing a seamless, flowing script.

Current Section Focus: {title}

Previous Content (for context):
{context}

Research Material:
{research_data}

Requirements:
- Write approximately {target_words} words of engaging narration
- Continue naturally from the previous section - NO chapter announcements or titles
- Use natural transitions like "As we move forward...", "This leads us to...", or just continue the story
- Tone: Conversational yet informative, like a documentary voiceover
- Focus: Create a smooth, continuous narrative
- Output: ONLY the spoken narration text that flows naturally. No titles, no markers, no "Chapter X".""",

    "visual_comfy_template": """Cinematic shot of {title}, detailed, 8k, {visual_desc}""",
    
    "visual_scene_planner": """You are a visual director for a documentary. Your task is to plan visual scenes that match the narrator's audio.

FULL CHAPTER CONTEXT:
Title: {chapter_title}
Full Narration: {full_content}

CURRENT SEGMENT:
Time: {start_time:.1f}s - {end_time:.1f}s
Narrator says: "{segment_text}"

VISUAL CONTINUITY:
Previous scene: {previous_scene}

Create a DETAILED visual description for this {duration:.1f}-second segment. The visual should:
1. Directly illustrate what the narrator is saying
2. Be cinematically interesting and dynamic
3. Flow naturally from the previous scene
4. Be suitable for AI image generation (specific, concrete visual elements)

Return ONLY a JSON object:
{{
    "visual_description": "Detailed scene description for AI image generator",
    "shot_type": "wide/medium/close-up/etc",
    "mood": "atmospheric descriptor"
}}"""
}

class PromptManager:
    def __init__(self):
        self.prompts = self.load_prompts()

    def load_prompts(self) -> Dict[str, str]:
        """Loads prompts from file or returns defaults."""
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                    saved_prompts = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**DEFAULT_PROMPTS, **saved_prompts}
            except Exception as e:
                logger.error(f"Failed to load prompts: {e}")
                return DEFAULT_PROMPTS.copy()
        return DEFAULT_PROMPTS.copy()

    def save_prompts(self, prompts: Dict[str, str]):
        """Saves prompts to file."""
        try:
            with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
                json.dump(prompts, f, indent=4)
            self.prompts = prompts
            logger.info("Prompts saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save prompts: {e}")

    def get_prompt(self, key: str) -> str:
        """Returns the prompt template for the given key."""
        return self.prompts.get(key, DEFAULT_PROMPTS.get(key, ""))

# Global instance
prompt_manager = PromptManager()
