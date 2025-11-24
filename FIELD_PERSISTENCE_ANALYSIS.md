# Field Persistence Analysis

## Current State (Project ID=4)

### ✅ SAVED:
- Topic: "The history of coffe"
- Status: "New"  
- Research Data: 9,528 chars (full research)
- Script Content: URLs (research sources)

### ❌ NULL (Missing):
- Title
- Description
- Narrator Script (combined narration from all chapters)
- Polish Narrator
- Production Script
- Generative Style
- Word Count
- Captions URL
- Video + Audio URL (should have `output\master_audio.mp3`)
- Visual Screenplay
- Storyboard Data
- Visual Story JSON
- Style Consistency Notes
- Key Visual Motifs

## Root Cause:

**models.py `Project.to_nocodb_json()`** only maps 2 fields:
```python
data = {
    "Topic": self.topic,
    "Status": self.status,
}
```

But it should save fields at each pipeline phase!

## Solution:

Update pipeline to PATCH the project after each phase:

1. **Phase 1 (Initialize)**: Topic, Status
2. **Phase 2 (Research)**: Research Data, Script Content (sources)
3. **Phase 3 (Script)**: Chapters → Narrator Script (combined), Production Script, Word Count
4. **Phase 4 (Audio)**: Video + Audio URL, duration
5. **Phase 5 (Visual)**: Visual fields, image paths

Currently: Only Phase 1 & 2 working!
