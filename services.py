import os
import requests
import logging
# import google.generativeai as genai # Unused
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from utils.database import db

def init_db():
    """
    Initializes the SQLite database.
    """
    try:
        db.init_db()
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def get_nocodb_config():
    """Deprecated."""
    return None

def get_all_stories():
    """
    Fetches all stories from SQLite.
    """
    return db.get_all_projects()

def create_story(topic: str):
    """
    Creates a new record in SQLite with the topic.
    Returns the Record ID.
    """
    return db.create_project(topic)

def get_story(story_id: int):
    """
    Fetches a single story by ID.
    """
    return db.get_project(story_id)

def update_story(story_id: int, research_data: str = None, script_content: str = None, **kwargs):
    """
    Updates an existing SQLite record.
    Accepts arbitrary kwargs to update any field in the projects table.
    """
    data = {}
    if research_data:
        data["research_content"] = research_data
        data["status"] = "Researched"
    if script_content:
        data["script_content"] = script_content
        data["status"] = "Scripted"
        
    # Merge any other fields passed in kwargs (e.g. audio_duration, audio_timestamps)
    data.update(kwargs)
    
    return db.update_project(story_id, data)

def delete_story(story_id: int):
    """
    Deletes a record from SQLite.
    """
    return db.delete_project(story_id)

def research_topic(topic: str):
    """
    Uses Perplexity API to research the topic.
    """
    logger.info(f"Starting research for: {topic}")
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("Perplexity API key missing.")
        return "Error: Missing API Key"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a helpful research assistant. Provide detailed, factual information about the requested topic suitable for a documentary script."},
            {"role": "user", "content": f"Research the following topic in detail: {topic}"}
        ]
    }

    try:
        response = requests.post("https://api.perplexity.ai/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        logger.info("Research completed successfully.")
        return content
    except Exception as e:
        logger.error(f"Research failed: {e}")
        if 'response' in locals():
             logger.error(f"Response: {response.text}")
        return f"Research failed: {str(e)}"

def generate_script(topic: str, research_data: str):
    """
    Generates a structured script using OpenRouter (Gemini via OpenRouter).
    """
    logger.info("Generating script with OpenRouter...")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OpenRouter API key missing.")
        return "Error: Missing API Key"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Visual Storyteller"
    }

    prompt = f"""
    You are a professional documentary scriptwriter.
    
    Topic: {topic}
    
    Research Data:
    {research_data}
    
    Task:
    Write a detailed script for a visual documentary.
    The script should be formatted as a structured table or list with the following columns:
    1. Time (approximate timestamp)
    2. Narration (The text spoken by the narrator)
    3. Visual Prompt (A detailed description of the visual scene for an AI image generator like ComfyUI)
    
    The script should be engaging, factual, and visually evocative.
    Aim for a comprehensive coverage of the topic.
    
    Format the output as Markdown.
    """

    payload = {
        "model": "google/gemini-2.5-flash", # Using Gemini 2.5 Flash via OpenRouter
        "messages": [
            {"role": "system", "content": "You are an expert scriptwriter."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        logger.info("Script generation completed.")
        return content
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        if 'response' in locals():
             logger.error(f"Response: {response.text}")
        return f"Script generation failed: {str(e)}"
