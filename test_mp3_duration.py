from mutagen.mp3 import MP3
import json

# Test reading MP3 duration
audio_path = "output/master_audio.mp3"

print("Testing MP3 duration reading...")
print(f"File: {audio_path}\n")

try:
    audio_file = MP3(audio_path)
    duration = audio_file.info.length
    duration_rounded = round(duration, 2)
    
    print(f"✅ SUCCESS!")
    print(f"Duration (raw): {duration}s")
    print(f"Duration (2 decimal): {duration_rounded}s")
    print(f"Type: {type(duration_rounded)}")
    print(f"\nJSON test: {json.dumps({'duration': duration_rounded})}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
