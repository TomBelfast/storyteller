"""
DIAGNOSTIC TEST: Sprawdzenie całego procesu audio generation
1. Co jest w bazie (Narrator Script)
2. Co wysyłamy do Kokoro TTS
3. Co Kokoro zwraca (timestamps)
4. Weryfikacja długości
"""

import requests
import json
from config import settings
from modules.audio_engine import AudioEngine
from mutagen.mp3 import MP3

project_id = 5
api_url = settings.NOCODB_API_URL
table_id = settings.NOCODB_PROJECTS_TABLE_ID
headers = {"xc-token": settings.NOCODB_API_TOKEN}

print("=" * 80)
print("DIAGNOSTIC TEST: Audio Generation Analysis")
print("=" * 80)

# STEP 1: Get Narrator Script from DB
print("\n[STEP 1] Fetching Narrator Script from NocoDB...")
resp = requests.get(
    f"{api_url}/api/v2/tables/{table_id}/records/{project_id}",
    headers=headers
)

if resp.status_code != 200:
    print(f"❌ Failed: {resp.status_code}")
    exit(1)

project_data = resp.json()
narrator_script = project_data.get(settings.NOCODB_FIELDS["project"]["narrator_script"])

if not narrator_script:
    print("❌ Narrator Script is NULL!")
    exit(1)

print(f"✅ Narrator Script retrieved")
print(f"   - Characters: {len(narrator_script)}")
print(f"   - Words: {len(narrator_script.split())}")
print(f"   - Expected duration @ 2.5 words/sec: {len(narrator_script.split()) / 2.5:.1f}s (~{len(narrator_script.split()) / 150:.1f} min)")
print(f"\n   First 300 chars:")
print(f"   {narrator_script[:300]}...")
print(f"\n   Last 100 chars:")
print(f"   ...{narrator_script[-100:]}")

# STEP 2: Generate Audio
print("\n[STEP 2] Sending to Kokoro TTS...")
print(f"   Input text length: {len(narrator_script)} chars")
print(f"   Input word count: {len(narrator_script.split())} words")

audio_engine = AudioEngine()
audio_path, timestamps = audio_engine.generate_master_audio(
    narrator_script,
    voice_id="am_michael"
)

if not audio_path:
    print("❌ Audio generation failed!")
    exit(1)

print(f"✅ Audio generated: {audio_path}")

# STEP 3: Analyze MP3 file
print("\n[STEP 3] Analyzing MP3 file...")
try:
    import os
    file_size = os.path.getsize(audio_path)
    audio_file = MP3(audio_path)
    mp3_duration = audio_file.info.length
    
    print(f"   File size: {file_size} bytes ({file_size/1024:.1f} KB)")
    print(f"   MP3 duration: {mp3_duration:.2f}s")
    print(f"   Bitrate: {audio_file.info.bitrate / 1000:.0f} kbps")
except Exception as e:
    print(f"❌ Failed to read MP3: {e}")
    mp3_duration = 0

# STEP 4: Analyze Timestamps
print("\n[STEP 4] Analyzing timestamps...")
print(f"   Timestamps count: {len(timestamps)}")

if timestamps and len(timestamps) > 0:
    first_ts = timestamps[0]
    last_ts = timestamps[-1]
    
    print(f"   First timestamp: {first_ts}")
    print(f"   Last timestamp: {last_ts}")
    
    # Calculate timestamp duration
    if "end_time" in last_ts:
        ts_duration = last_ts["end_time"]
        print(f"   Timestamp duration: {ts_duration:.2f}s")
    else:
        print(f"   ❌ No 'end_time' in timestamps!")
        ts_duration = 0
    
    # Count words in timestamps
    words_in_ts = [ts.get("word", "") for ts in timestamps if ts.get("word")]
    unique_words = len(words_in_ts)
    total_chars_in_ts = sum(len(word) for word in words_in_ts)
    
    print(f"   Words with timestamps: {unique_words}")
    print(f"   Total chars in timestamps: {total_chars_in_ts}")
    
    # Sample timestamps
    print(f"\n   First 5 timestamps:")
    for i, ts in enumerate(timestamps[:5]):
        print(f"     {i+1}. {ts}")
    
    print(f"\n   Last 5 timestamps:")
    for i, ts in enumerate(timestamps[-5:]):
        print(f"     {len(timestamps)-4+i}. {ts}")
else:
    print("   ❌ No timestamps returned!")
    ts_duration = 0
    unique_words = 0
    total_chars_in_ts = 0

# STEP 5: VERIFICATION & DIAGNOSIS
print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)

input_words = len(narrator_script.split())
input_chars = len(narrator_script)

print(f"\n📊 INPUT:")
print(f"   {input_chars} chars, {input_words} words")

print(f"\n📊 KOKORO OUTPUT:")
print(f"   {unique_words} words with timestamps")
print(f"   {total_chars_in_ts} chars in timestamps")
print(f"   Duration from timestamps: {ts_duration:.2f}s")

print(f"\n📊 MP3 FILE:")
print(f"   Duration from file: {mp3_duration:.2f}s")

print(f"\n📊 COMPARISON:")
print(f"   Input words: {input_words}")
print(f"   Timestamped words: {unique_words}")
print(f"   Word coverage: {unique_words/input_words*100 if input_words > 0 else 0:.1f}%")
print(f"   Char coverage: {total_chars_in_ts/input_chars*100 if input_chars > 0 else 0:.1f}%")

# DIAGNOSIS
print(f"\n🔍 DIAGNOSIS:")
if unique_words < input_words * 0.5:
    print(f"   ❌ PROBLEM: Only {unique_words}/{input_words} words timestamped!")
    print(f"   🔴 Kokoro TTS received INCOMPLETE text or stopped early")
    print(f"   🔴 Expected ~{input_words/2.5:.0f}s audio, got {mp3_duration:.0f}s")
elif abs(mp3_duration - ts_duration) > 0.5:
    print(f"   ⚠️  WARNING: MP3 duration ({mp3_duration:.2f}s) != Timestamp duration ({ts_duration:.2f}s)")
else:
    print(f"   ✅ Audio generation looks OK")
    print(f"   Duration: {mp3_duration:.2f}s for {input_words} words ({input_words/mp3_duration:.1f} words/sec)")

print("\n" + "=" * 80)
