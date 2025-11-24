import requests
import json
from typing import List, Dict, Any
from utils.logger import logger
from utils.ai_supervisor import ai_supervisor
from models import Chapter
from config import settings
from utils.prompt_manager import prompt_manager

class ScriptEngine:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.5-flash"

    @ai_supervisor()
    def generate_scripts(self, project_id: str, research_data: str, target_duration: int = 3) -> List[Chapter]:
        """
        Generates a full script divided into chapters using Gemini via OpenRouter.
        """
        logger.info(f"Generating scripts for Project {project_id} with duration {target_duration} min")
        
        # 1. Calculate Constraints
        total_words = target_duration * 150 # Approx 150 words per minute
        
        # 2. Generate Outline
        outline = self.generate_outline(research_data, target_duration)
        logger.info(f"Generated Outline: {len(outline)} chapters")
        
        chapters = []
        context_buffer = ""
        
        # 3. Generate Content for each Chapter
        current_time = 0.0
        
        for i, chapter_title in enumerate(outline):
            # Calculate target words for this chapter
            chapter_words = int(total_words / len(outline))
            
            content = self.generate_chapter_content(
                title=chapter_title,
                research_data=research_data,
                context=context_buffer,
                target_words=chapter_words
            )
            
            # Estimate duration for this chapter
            actual_words = len(content.split())
            duration = actual_words / 2.5 # Rough estimate: 2.5 words per second
            
            chapter = Chapter(
                title=chapter_title,
                content=content,
                start_time=current_time,
                end_time=current_time + duration
            )
            
            chapters.append(chapter)
            
            # Update context and time
            context_buffer += f"\nChapter {i+1} ({chapter_title}): {content[:200]}..." # Keep it brief
            current_time += duration
            
        return chapters

    def generate_outline(self, research_data: str, duration: int) -> List[str]:
        """
        Asks AI to plan the structure of the video.
        """
        prompt_template = prompt_manager.get_prompt("script_outline")
        prompt = prompt_template.format(duration=duration, research_data=research_data[:2000])
        
        response = self._call_llm(prompt)
        try:
            # Clean up potential markdown code blocks
            clean_response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_response)
        except Exception as e:
            logger.error(f"Failed to parse outline JSON: {e}. Response: {response}")
            return ["Introduction", "Main Body", "Conclusion"] # Fallback

    def generate_chapter_content(self, title: str, research_data: str, context: str, target_words: int) -> str:
        """
        Generates the narration text for a specific chapter.
        """
        prompt_template = prompt_manager.get_prompt("script_chapter")
        prompt = prompt_template.format(
            title=title, 
            context=context, 
            research_data=research_data[:1500], 
            target_words=target_words
        )
        
        raw_content = self._call_llm(prompt)
        return self._clean_content(raw_content)

    def _clean_content(self, text: str) -> str:
        """Removes unwanted artifacts like 'Narrator:' prefixes."""
        import re
        # Remove (Narrator):, Narrator: prefixes (line start only)
        text = re.sub(r"^\s*\(?Narrator\)?:\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
        # Remove [Scene...] tags
        text = re.sub(r"\[.*?\]", "", text)
        # Remove ** markdown (keep text, remove only markers)
        text = re.sub(r"\*\*", "", text)
        # Remove _ markdown
        text = re.sub(r"_", "", text)
        return text.strip()

    def _call_llm(self, prompt: str) -> str:
        """
        Helper to call OpenRouter API.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Storyteller v2.0"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
