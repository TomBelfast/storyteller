# CREATE CHAPTERS TABLE - Manual Steps

## Problem:
Chapters table (mim0e5mdtlc401j) is in DIFFERENT base than Projects table!
- Projects base_id: `p5ubgijahnzy0xd` (Ulka base - visible in UI)
- Chapters base_id: `pmcr6sel7s7gjwj` (different base - NOT visible)

## Solution: Create Chapters table in Ulka base

### Steps in NocoDB UI:

1. **Open NocoDB** → Base "Ulka"

2. **Click "+ Create New" → "Table"**

3. **Table Name:** `Chapters`

4. **Add these columns (fields):**
   - ✅ `Id` - Auto-generated (Primary Key) - Already exists
   - `Title` - SingleLineText
   - `Content` - LongText
   - `Project` - LinkToAnotherRecord → Link to "Projects" table (Many-to-One)
   - `StartTime` - Decimal
   - `EndTime` - Decimal  
   - `VisualDesc` - LongText
   - `ImagePath` - Attachment

5. **After creating, get the new table ID:**
   - Click on table settings (⋮)
   - Look for table ID in URL or settings
   - Should look like: `m...` (14 chars)

6. **Update config.py:**
   ```python
   NOCODB_CHAPTERS_TABLE_ID: str = "NEW_TABLE_ID_HERE"
   ```

## Alternative: I can create it via API?

Want me to create a script that creates the table via NocoDB REST API instead?
