import requests
import base64
import os
import json
from typing import Tuple, List, Dict, Any
from config import settings
from utils.logger import logger
from pydantic import ValidationError, BaseModel, Field
from utils.ai_supervisor import ai_supervisor
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Chapter

# Kokoro TTS Pydantic Models
class KokoroTTSRequest(BaseModel):
    input: str = Field(..., min_length=1)
    voice: str = "am_michael"
    speed: float = 1.0

class TimestampModel(BaseModel):
    word: str
    start_time: float
    end_time: float

class KokoroTTSResponse(BaseModel):
    audio: str
    timestamps: List[TimestampModel] = []

class AudioEngine:
    @ai_supervisor()
    def generate_master_audio(self, full_text: str, voice_id: str = "am_michael") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generates audio using Kokoro TTS API with Pydantic validation.
        Returns: (audio_path, timestamps)
        """
        logger.info(f"Generating Master Audio (Kokoro) for text length: {len(full_text)}")
        logger.debug(f"Text preview (first 200 chars): {full_text[:200]}...")
        logger.debug(f"Word count: {len(full_text.split())}")
        
        # Validate and prepare request using Pydantic
        try:
            request_model = KokoroTTSRequest(
                input=full_text,
                voice=voice_id,
                speed=1.0
            )
            payload = request_model.dict()
            logger.debug(f"Request validated: {len(payload['input'])} chars to Kokoro")
        except ValidationError as e:
            logger.error(f"Request validation failed: {e}")
            raise
        
        try:
            # Use stream=True to handle large responses/NDJSON correctly
            response = requests.post(settings.KOKORO_TTS_URL, json=payload, timeout=120, stream=True)
            response.raise_for_status()
            
            logger.info("Response stream opened")
            
            # Parse and merge response
            # CRITICAL FIX: Collect ALL audio chunks, not just the first one
            all_audio_chunks = []
            all_timestamps = []
            line_count = 0
            
            for line in response.iter_lines():
                line_count += 1
                if not line:
                    continue
                    
                try:
                    line_text = line.decode('utf-8').strip()
                    if not line_text:
                        continue
                    
                    # Handle concatenated JSON objects
                    decoder = json.JSONDecoder()
                    pos = 0
                    
                    while pos < len(line_text):
                        try:
                            obj, end = decoder.raw_decode(line_text[pos:])
                            pos += end
                            
                            # Process the object
                            line_data = obj
                            
                            # Collect audio chunks from ALL lines (not just first)
                            if "audio" in line_data:
                                all_audio_chunks.append(line_data["audio"])
                                logger.debug(f"Audio chunk {len(all_audio_chunks)} found in line {line_count}")
                            
                            # Collect timestamps from all lines
                            if "timestamps" in line_data:
                                line_timestamps = line_data["timestamps"]
                                all_timestamps.extend(line_timestamps)
                                
                            # Skip whitespace
                            while pos < len(line_text) and line_text[pos].isspace():
                                pos += 1
                                
                        except json.JSONDecodeError:
                            # If we can't parse the rest, log and break inner loop
                            logger.warning(f"Failed to parse remaining content in line {line_count} at pos {pos}")
                            break
                        
                except Exception as e:
                    logger.warning(f"Failed to process line {line_count}: {e}")
                    continue
            
            logger.info(f"Stream processing complete: {line_count} lines, {len(all_audio_chunks)} audio chunks, {len(all_timestamps)} timestamps")
            
            if not all_audio_chunks:
                raise ValueError("No audio data received from Kokoro API")
            
            # CRITICAL: Concatenate ALL audio chunks
            if len(all_audio_chunks) == 1:
                audio_base64 = all_audio_chunks[0]
                logger.info("Single audio chunk received")
            else:
                # Decode all chunks, concatenate bytes, then re-encode
                logger.info(f"Concatenating {len(all_audio_chunks)} audio chunks...")
                all_audio_bytes = b''.join([base64.b64decode(chunk) for chunk in all_audio_chunks])
                audio_base64 = base64.b64encode(all_audio_bytes).decode('utf-8')
            
            # Decode and Save
            audio_bytes = base64.b64decode(audio_base64)
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            audio_path = os.path.join(output_dir, "master_audio.mp3")
            
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
                
            logger.info(f"Audio saved to: {audio_path}")
            logger.info(f"Final audio size: {len(audio_bytes)} bytes")
            logger.info(f"Final timestamp count: {len(all_timestamps)}")
            
            # Return merged timestamps with rounding
            timestamps = []
            for ts in all_timestamps:
                if "start" in ts: ts["start"] = round(ts["start"], 2)
                if "end" in ts: ts["end"] = round(ts["end"], 2)
                if "start_time" in ts: ts["start_time"] = round(ts["start_time"], 2)
                if "end_time" in ts: ts["end_time"] = round(ts["end_time"], 2)
                timestamps.append(ts)
                
            return audio_path, timestamps
            
        except Exception as e:
            logger.error(f"Kokoro TTS Failed: {e}")
            logger.exception("Full exception traceback:")
            # Fallback for testing if API fails
            logger.warning("Using Mock Audio due to failure")
            return "output/mock_audio.mp3", []

    @ai_supervisor()
    def map_timestamps_to_chapters(self, timestamps: List[Dict[str, Any]], chapters: List[Chapter]) -> List[Chapter]:
        """
        Maps word-level timestamps to chapters to determine start/end times.
        """
        if not timestamps:
            logger.warning("No timestamps provided. Using fallback duration estimation.")
            current_time = 0.0
            for chapter in chapters:
                chapter.start_time = current_time
                estimated_duration = len(chapter.content.split()) / 2.5 # Rough estimate
                chapter.end_time = current_time + estimated_duration
                current_time = chapter.end_time
            return chapters

        # Logic to map timestamps to chapters based on text matching
        # This is a simplified version. In production, we need robust text alignment.
        
        current_word_index = 0
        total_words = len(timestamps)
        
        for chapter in chapters:
            chapter_words = chapter.content.split()
            word_count = len(chapter_words)
            
            if current_word_index < total_words:
                start_time = timestamps[current_word_index].get("start", 0.0)
            else:
                start_time = chapters[-1].end_time if chapters else 0.0
                
            end_word_index = min(current_word_index + word_count, total_words - 1)
            
            if end_word_index >= 0 and end_word_index < total_words:
                end_time = timestamps[end_word_index].get("end", start_time + 1.0)
            else:
                end_time = start_time + (word_count * 0.4) # Fallback
                
            chapter.start_time = start_time
            chapter.end_time = end_time
            
            current_word_index += word_count
            
        return chapters
