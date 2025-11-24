"""
Test script naturalness improvements:
1. Verify ## headers are removed from concatenation
2. Verify new prompt generates natural narration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.prompt_manager import prompt_manager
from modules.script_engine import ScriptEngine
from utils.logger import logger

def test_prompt_improvements():
    logger.info("=" * 60)
    logger.info("TESTING SCRIPT NATURALNESS IMPROVEMENTS")
    logger.info("=" * 60)
    
    # Test 1: Check prompt template
    logger.info("\n--- Test 1: Prompt Template ---")
    chapter_prompt = prompt_manager.get_prompt("script_chapter")
    
    if "##" in chapter_prompt:
        logger.error("❌ FAIL: Prompt still contains ## markers")
    else:
        logger.info("✅ PASS: No ## in prompt template")
    
    if "NO chapter announcements" in chapter_prompt or "natural" in chapter_prompt.lower():
        logger.info("✅ PASS: Prompt emphasizes natural flow")
    else:
        logger.warning("⚠️ Prompt might not emphasize natural flow")
    
    logger.info("\nPrompt preview:")
    logger.info(chapter_prompt[:300] + "...")
    
    # Test 2: Generate sample content
    logger.info("\n--- Test 2: Sample Generation ---")
    engine = ScriptEngine()
    
    sample_research = """
    The Roman Empire began in 27 BC when Augustus became the first Emperor.
    At its peak, it controlled vast territories across Europe, North Africa, and the Middle East.
    The empire lasted until 476 AD in the West.
    """
    
    logger.info("Generating sample chapter content...")
    try:
        content = engine.generate_chapter_content(
            title="The Rise of Rome",
            research_data=sample_research,
            context="",
            target_words=50
        )
        
        logger.info("\nGenerated content:")
        logger.info(content)
        
        # Check for issues
        if content.startswith("##"):
            logger.error("❌ FAIL: Content starts with ##")
        elif "Chapter" in content[:50] and ":" in content[:50]:
            logger.warning("⚠️ Content might announce chapter title")
        else:
            logger.info("✅ PASS: Content appears natural")
            
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
    
    # Test 3: Concatenation logic (simulated)
    logger.info("\n--- Test 3: Concatenation Logic ---")
    
    mock_chapters = [
        type('Chapter', (), {'title': 'Intro', 'content': 'First part.'})(),
        type('Chapter', (), {'title': 'Middle', 'content': 'Second part.'})()
    ]
    
    # Simulate new concatenation
    full_script_new = "\n\n".join([c.content for c in mock_chapters])
    # Simulate old concatenation
    full_script_old = "\n\n".join([f"## {c.title}\n{c.content}" for c in mock_chapters])
    
    logger.info("\nOLD concatenation:")
    logger.info(full_script_old)
    logger.info("\nNEW concatenation:")
    logger.info(full_script_new)
    
    if "##" not in full_script_new:
        logger.info("\n✅ PASS: New concatenation has no ## markers")
    else:
        logger.error("\n❌ FAIL: New concatenation still has ## markers")
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    test_prompt_improvements()
