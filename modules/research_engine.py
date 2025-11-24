import requests
import json
from typing import Dict
from utils.logger import logger
from utils.ai_supervisor import ai_supervisor
from config import settings
from utils.prompt_manager import prompt_manager

class ResearchEngine:
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-reasoning-pro" # Or "sonar-pro"

    @ai_supervisor()
    def run_research(self, topic: str) -> Dict[str, str]:
        """
        Conducts research on the given topic using Perplexity API.
        Returns: {"content": "...", "sources": "..."}
        """
        logger.info(f"Starting research on topic: {topic} using model {self.model}")
        
        if not self.api_key:
            logger.error("PERPLEXITY_API_KEY is missing in settings.")
            raise ValueError("PERPLEXITY_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = prompt_manager.get_prompt("research_system")
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Research topic: {topic}"
                }
            ]
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract content
            content = data['choices'][0]['message']['content']
            
            # Extract citations if available (Perplexity specific)
            citations = data.get('citations', [])
            formatted_sources = "\n".join([f"{i+1}. {c}" for i, c in enumerate(citations)])
            
            if not formatted_sources:
                formatted_sources = "No specific citations returned by API."

            logger.info("Research completed successfully")
            return {
                "content": content,
                "sources": formatted_sources
            }
            
        except Exception as e:
            logger.error(f"Perplexity API failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"API Response: {e.response.text}")
            raise e
