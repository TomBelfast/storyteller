from config import settings
import json

# Print exact field names being used
print("=== FIELD MAPPINGS ===")
print(f"audio_url -> '{settings.NOCODB_FIELDS['project']['audio_url']}'")
print(f"audio_timestamps -> '{settings.NOCODB_FIELDS['project']['audio_timestamps']}'")
print(f"audio_duration -> '{settings.NOCODB_FIELDS['project']['audio_duration']}'")

# Simulate payload
payload = [{
    "Id": 5,
    settings.NOCODB_FIELDS["project"]["audio_url"]: "http://test.example.com/audio.mp3",
    settings.NOCODB_FIELDS["project"]["audio_timestamps"]: json.dumps([{"word": "test", "start_time": 0.0, "end_time": 1.0}]),
    settings.NOCODB_FIELDS["project"]["audio_duration"]: 179.49
}]

print("\n=== PAYLOAD ===")
print(json.dumps(payload, indent=2, ensure_ascii=False))
