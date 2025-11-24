"""
Test script to verify audio generation fix.
This will generate audio for a test project and verify:
1. All audio chunks are concatenated
2. File size is reasonable
3. Audio duration matches expected value
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.audio_engine import AudioEngine
from utils.logger import logger
from services import get_story
import json

def get_audio_duration_ffprobe(file_path):
    """Use ffprobe to get accurate audio duration"""
    import subprocess
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
             '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"ffprobe failed: {e}")
        return None

def get_audio_duration_mutagen(file_path):
    """Use mutagen to get audio duration (fallback)"""
    try:
        from mutagen.mp3 import MP3
        audio = MP3(file_path)
        return audio.info.length
    except Exception as e:
        logger.warning(f"mutagen failed: {e}")
        return None

def main():
    logger.info("=" * 60)
    logger.info("AUDIO GENERATION VERIFICATION TEST")
    logger.info("=" * 60)
    
    # Get project 7 (the test project from logs)
    project_id = 7
    project = get_story(project_id)
    
    if not project:
        logger.error(f"Project {project_id} not found!")
        return
    
    logger.info(f"Testing with project: {project['topic']}")
    
    # Get script content
    script_content = project.get('script_content', '')
    
    if not script_content:
        logger.error("No script_content found!")
        return
        
    logger.info(f"Script length: {len(script_content)} chars")
    logger.info(f"Word count: {len(script_content.split())} words")
    
    # Generate audio
    logger.info("\n--- Starting Audio Generation ---")
    engine = AudioEngine()
    audio_path, timestamps = engine.generate_master_audio(script_content, "am_michael")
    
    logger.info(f"\n--- Verification Results ---")
    logger.info(f"Audio saved to: {audio_path}")
    logger.info(f"Timestamps count: {len(timestamps)}")
    
    # Check file exists and size
    if os.path.exists(audio_path):
        file_size = os.path.getsize(audio_path)
        logger.info(f"✅ File exists: {audio_path}")
        logger.info(f"✅ File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    else:
        logger.error(f"❌ File not found: {audio_path}")
        return
    
    # Calculate expected duration from timestamps
    if timestamps:
        last_ts = timestamps[-1]
        expected_duration = last_ts.get('end', last_ts.get('end_time', 0.0))
        logger.info(f"Expected duration (from timestamps): {expected_duration:.2f}s")
    else:
        expected_duration = None
        logger.warning("No timestamps to calculate expected duration")
    
    # Get actual duration
    actual_duration = get_audio_duration_ffprobe(audio_path)
    if actual_duration is None:
        actual_duration = get_audio_duration_mutagen(audio_path)
    
    if actual_duration:
        logger.info(f"Actual audio duration: {actual_duration:.2f}s")
        
        if expected_duration:
            diff = abs(actual_duration - expected_duration)
            percentage_diff = (diff / expected_duration) * 100
            
            logger.info(f"\n--- Comparison ---")
            logger.info(f"Expected: {expected_duration:.2f}s")
            logger.info(f"Actual:   {actual_duration:.2f}s")
            logger.info(f"Difference: {diff:.2f}s ({percentage_diff:.1f}%)")
            
            if percentage_diff < 5:
                logger.info("✅ PASS: Duration matches expected value (within 5%)")
            else:
                logger.warning(f"⚠️ WARNING: Duration difference is {percentage_diff:.1f}%")
    else:
        logger.error("❌ Could not determine audio duration")
        logger.info("Install ffmpeg or mutagen to verify duration:")
        logger.info("  pip install mutagen")
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
