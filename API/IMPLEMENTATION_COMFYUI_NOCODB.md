# Dokumentacja Implementacji: ComfyUI i NocoDB

## Spis Treści

1. [Implementacja NocoDB](#implementacja-nocodb)
2. [Implementacja ComfyUI](#implementacja-comfyui)
3. [Migracja z Baserow](#migracja-z-baserow)
4. [Konfiguracja](#konfiguracja)
5. [Przykłady Użycia](#przykłady-użycia)
6. [Troubleshooting](#troubleshooting)

---

## Implementacja NocoDB

### Przegląd

NocoDB został zaimplementowany jako główna baza danych dla Poly-Scribe Engine, zastępując Baserow. Implementacja zapewnia pełną kompatybilność z istniejącym kodem poprzez warstwę abstrakcji `UnifiedDatabaseClient`.

### Architektura

```
┌─────────────────────────────────────────────────────────┐
│              WorkflowOrchestrator                        │
│              (Business Logic)                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         ExtendedDatabaseClient                          │
│         (Workflow-specific methods)                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         UnifiedDatabaseClient                           │
│         (Database abstraction layer)                    │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
               ▼                      ▼
    ┌──────────────────┐    ┌──────────────────┐
    │  NocoDBClient    │    │  BaserowClient   │
    │  (Primary)       │    │  (Legacy)        │
    └──────────────────┘    └──────────────────┘
```

### Komponenty

#### 1. NocoDBClient (`src/poly_scribe/services/nocodb_client.py`)

Główny klient do komunikacji z API NocoDB.

**Funkcjonalności:**
- CRUD operations (Create, Read, Update, Delete)
- Schema management (tworzenie tabel i kolumn)
- File upload (z fallback do lokalnego storage)
- Retry logic i error handling
- Caching dla optymalizacji

**Kluczowe metody:**

```python
# CRUD Operations
async def get_row(table_name: str, row_id: Union[str, int]) -> Dict[str, Any]
async def get_rows(table_name: str, limit: int = 25, offset: int = 0, ...) -> Dict[str, Any]
async def create_row(table_name: str, fields: Dict[str, Any]) -> Dict[str, Any]
async def update_row(table_name: str, row_id: Union[str, int], fields: Dict[str, Any]) -> Dict[str, Any]
async def delete_row(table_name: str, row_id: Union[str, int]) -> bool

# Schema Management
async def create_table(table_definition: Dict[str, Any]) -> Dict[str, Any]
async def create_column(table_name: str, column_definition: Dict[str, Any]) -> Dict[str, Any]
async def get_table_id(table_name: str) -> Optional[str]
async def list_columns(table_name: str) -> List[Dict[str, Any]]

# File Upload
async def upload_file(file_path: str, file_name: Optional[str] = None) -> Dict[str, Any]
```

**Przykład użycia:**

```python
from poly_scribe.core.config import get_settings
from poly_scribe.services.nocodb_client import NocoDBClient

settings = get_settings()
client = NocoDBClient(settings)

# Pobierz projekt
project = await client.get_row("video", 1)

# Utwórz nowy rekord
new_chapter = await client.create_row("chapters", {
    "Title": "Chapter 1",
    "Video": 1,  # Link to video
    "Chapter Number": 1
})

# Aktualizuj rekord
await client.update_row("video", 1, {
    "Status": "Complete",
    "Title": "Updated Title"
})
```

#### 2. UnifiedDatabaseClient (`src/poly_scribe/services/db_client.py`)

Warstwa abstrakcji umożliwiająca przełączanie między NocoDB a Baserow.

**Funkcjonalności:**
- Automatyczne przełączanie między bazami na podstawie `use_nocodb` flag
- Kompatybilność z istniejącym kodem (BaserowRow-like interface)
- Mapowanie nazw tabel (Baserow table IDs → NocoDB table names)

**Konfiguracja:**

```python
# W .env
USE_NOCODB=true
USE_BASEROW=false

# W kodzie
settings = get_settings()
client = UnifiedDatabaseClient(settings)  # Automatycznie używa NocoDB jeśli use_nocodb=True
```

#### 3. ExtendedDatabaseClient (`src/poly_scribe/services/db_client_extended.py`)

Rozszerzenie `UnifiedDatabaseClient` o metody specyficzne dla workflow.

**Dodatkowe metody:**

```python
async def get_chapters_for_project_dict(project_id: Union[str, int]) -> List[Dict[str, Any]]
async def get_scenes_for_project_dict(project_id: Union[str, int]) -> List[Dict[str, Any]]
async def create_chapter_dict(chapter_data: Dict[str, Any]) -> Dict[str, Any]
async def create_scene_phase9(scene_data: Dict[str, Any]) -> Dict[str, Any]
async def update_project_status(project_id: Union[str, int], status: ProjectStatus) -> Dict[str, Any]
```

#### 4. Schema Definition (`src/poly_scribe/db/schema.py`)

Programatyczna definicja schematu bazy danych.

**Struktura:**

```python
def get_video_table_schema() -> TableDefinition:
    """Define the Video table schema (main projects table)."""
    return {
        "table_name": "video",
        "title": "Video",
        "description": "Main table for video projects",
        "columns": [
            {
                "column_name": "title",
                "title": "Title",
                "data_type": "SingleLineText",
                "required": True,
            },
            # ... więcej kolumn
        ]
    }
```

**Dostępne typy danych:**
- `SingleLineText` - Tekst jednoliniowy
- `LongText` - Tekst wieloliniowy
- `Number` - Liczba
- `Decimal` - Liczba dziesiętna
- `Date` - Data
- `DateTime` - Data i czas
- `SingleSelect` - Wybór pojedynczy
- `MultiSelect` - Wybór wielokrotny
- `Attachment` - Załącznik (plik)
- `URL` - Adres URL
- `JSON` - Dane JSON
- `LinkToAnotherRecord` - Relacja do innej tabeli

**Utworzenie schematu:**

```bash
python scripts/create_nocodb_schema.py
```

### Mapowanie Tabel Baserow → NocoDB

| Baserow Table ID | Baserow Table Name | NocoDB Table Name | Opis |
|------------------|-------------------|-------------------|------|
| 766 | Money Video | `video` | Główna tabela projektów |
| 767 | Money Chapters | `chapters` | Rozdziały projektów |
| 765 | Money Scenes | `scenes` | Sceny w rozdziałach |
| 750 | Money Style | `style` | Style malarskie |
| 764 | Character | `character` | Postacie |
| 763 | Location | `location` | Lokalizacje |
| 760 | Story Board Act 1 | `storyboard_act1` | Akt 1 storyboard |
| 761 | Story Board Act 2 | `storyboard_act2` | Akt 2 storyboard |
| 762 | Story Board Act 3 | `storyboard_act3` | Akt 3 storyboard |

### Różnice między NocoDB a Baserow

#### 1. Nazwy Pól

**Baserow:**
- Używa Field IDs (np. `field_7084`, `field_7089`)
- Wymaga mapowania ID → nazwa

**NocoDB:**
- Używa nazw pól (titles) z `user_field_names=true`
- Bezpośrednie użycie nazw (np. `"Title"`, `"Status"`)

**Przykład:**

```python
# Baserow
update_data = {
    "field_7084": "Project Title",
    "field_7087": "Complete"
}

# NocoDB
update_data = {
    "Title": "Project Title",
    "Status": "Complete"
}
```

#### 2. Attachment Fields

**Baserow:**
- File field: `[{"name": "file.mp3"}]`
- Wymaga osobnego pola dla URL

**NocoDB:**
- Attachment field: JSON string z pełnymi informacjami
- Format: `[{"title": "file.mp3", "url": "http://...", "mimetype": "audio/mpeg", "size": 12345}]`

**Przykład:**

```python
# NocoDB Attachment field
attachment_data = [{
    "title": "speech_1.mp3",
    "url": "http://127.0.0.1:8001/storage/uploads/speech_1.mp3",
    "mimetype": "audio/mpeg",
    "size": 2020268
}]
update_data = {
    "TTS Audio": json.dumps(attachment_data)
}
```

#### 3. Auto-increment ID

**Baserow:**
- Automatycznie generuje ID

**NocoDB:**
- Wymaga ręcznego generowania ID (jeśli pole `Id` jest required)
- `NocoDBClient.create_row()` automatycznie generuje ID (max existing + 1)

#### 4. Single Select Fields

**Baserow:**
- Można używać wartości tekstowej lub ID opcji

**NocoDB:**
- Zawsze używać ID opcji (najbardziej niezawodne)
- Sprawdzić dostępne opcje przez API przed użyciem

### File Upload

NocoDB Client implementuje inteligentny system uploadu plików:

1. **Próba uploadu przez API NocoDB:**
   - `/api/v2/storage/upload`
   - `/api/v1/db/storage/upload`
   - `/api/v1/db/storage/upload/multi`

2. **Fallback do lokalnego storage:**
   - Jeśli API nie działa, plik zapisywany lokalnie w `storage/uploads/`
   - URL wskazuje na FastAPI server: `http://127.0.0.1:8001/storage/uploads/filename.mp3`
   - FastAPI serwuje pliki przez `StaticFiles` mount

**Przykład:**

```python
# Upload pliku
file_info = await client.upload_file(
    file_path="/path/to/audio.mp3",
    file_name="speech_1.mp3"
)

# file_info = {
#     "name": "speech_1.mp3",
#     "url": "http://127.0.0.1:8001/storage/uploads/speech_1.mp3",
#     "mimetype": "audio/mpeg",
#     "size": 2020268
# }
```

### Error Handling

NocoDB Client implementuje zaawansowane error handling:

```python
class NocoDBError(Exception):
    """Custom exception for NOcoDB API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
```

**Retry Logic:**
- Automatyczne retry (domyślnie 3 próby)
- Exponential backoff
- Timeout handling

---

## Implementacja ComfyUI

### Przegląd

ComfyUI jest zintegrowany jako serwis generacji obrazów dla Phase 22 (Image Generation). Serwis obsługuje wiele modeli (Flux Dev, Flux Krea, SDXL, SDXL Lora) i automatycznie zapisuje wyniki do bazy danych.

### Architektura

```
┌─────────────────────────────────────────────────────────┐
│         Phase 22 Endpoint                               │
│         /api/v1/workflow/phase-22/image-generation      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         ImageGeneratorService                           │
│         - Build workflow                                │
│         - Send to ComfyUI                               │
│         - Poll for completion                           │
│         - Save to database                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         ComfyUI API                                     │
│         http://192.168.0.14:8188                        │
└─────────────────────────────────────────────────────────┘
```

### Komponenty

#### 1. ImageGeneratorService (`src/poly_scribe/services/image_generator_service.py`)

Główny serwis do generacji obrazów.

**Funkcjonalności:**
- Budowanie workflow dla różnych modeli
- Wysyłanie promptów do ComfyUI
- Polling statusu generacji
- Automatyczne zapisywanie wyników do bazy
- Retry logic i error handling

**Obsługiwane modele:**

| Model | Provider | Czas generacji | Jakość |
|-------|----------|----------------|--------|
| Flux Dev | `Flux Dev` | 45-60s | Wysoka |
| Flux Krea | `Flux Krea` | 25-35s | Średnia-Wysoka |
| SDXL | `SDXL` | 30-45s | Średnia |
| SDXL Lora | `SDXL Lora` | 30-45s | Średnia (z LoRA) |

**Kluczowe metody:**

```python
async def generate(request: ImageGenerateRequest) -> ImageGenerateResponse:
    """Start image generation in ComfyUI."""
    # 1. Build workflow
    # 2. Send to ComfyUI
    # 3. Return prompt_id immediately

async def check_status(prompt_id: str) -> ImageStatusResponse:
    """Check generation status."""
    # Poll ComfyUI for completion

async def _build_workflow(request: ImageGenerateRequest) -> Dict[str, Any]:
    """Build ComfyUI workflow JSON."""
    # Construct workflow based on model/provider
```

**Przykład użycia:**

```python
from poly_scribe.services.image_generator_service import ImageGeneratorService, ImageGenerateRequest, ImageProvider

service = ImageGeneratorService(settings, db_client)

request = ImageGenerateRequest(
    scene_id=123,
    positive_prompt="A beautiful landscape in Rembrandt style",
    negative_prompt="modern, digital, blurry",
    style_name="Rembrandt Golden",
    image_provider=ImageProvider.FLUX_KREA,
    save_to_baserow=True
)

response = await service.generate(request)
# response.prompt_id - użyj do sprawdzania statusu
```

#### 2. ComfyUI Workflow Structure

Workflow jest budowany dynamicznie w zależności od wybranego modelu:

**Flux Dev/Krea:**
```json
{
  "1": {
    "inputs": {
      "text": "positive_prompt",
      "clip": ["4", 0]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {"title": "CLIP Text Encode (Prompt)"}
  },
  "2": {
    "inputs": {
      "text": "negative_prompt",
      "clip": ["4", 0]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {"title": "CLIP Text Encode (Negative)"}
  },
  "4": {
    "inputs": {
      "ckpt_name": "flux1-dev-fp8.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {"title": "Load Checkpoint"}
  },
  "5": {
    "inputs": {
      "seed": 12345,
      "steps": 28,
      "cfg": 3.5,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1,
      "model": ["4", 0],
      "positive": ["1", 0],
      "negative": ["2", 0],
      "latent_image": ["6", 0]
    },
    "class_type": "KSampler",
    "_meta": {"title": "KSampler"}
  }
}
```

**SDXL z LoRA:**
```json
{
  "7": {
    "inputs": {
      "lora_name": "style_lora.safetensors",
      "strength_model": 0.8,
      "strength_clip": 0.8,
      "model": ["4", 0],
      "clip": ["4", 1]
    },
    "class_type": "LoraLoader",
    "_meta": {"title": "Load LoRA"}
  }
}
```

#### 3. API Endpoints (`src/poly_scribe/api/v1/image_generator_endpoints.py`)

**POST `/api/v1/image-generator/generate`**

Generuje obraz i zwraca `prompt_id`.

**Request:**
```json
{
  "scene_id": 123,
  "positive_prompt": "A beautiful landscape",
  "negative_prompt": "blurry, low quality",
  "style_name": "Rembrandt Golden",
  "image_provider": "Flux Krea",
  "save_to_baserow": true
}
```

**Response:**
```json
{
  "success": true,
  "prompt_id": "abc123",
  "message": "Image generation started",
  "estimated_time_seconds": 30
}
```

**GET `/api/v1/image-generator/status/{prompt_id}`**

Sprawdza status generacji.

**Response:**
```json
{
  "status": "completed",
  "progress": 100,
  "image_url": "http://192.168.0.14:8188/view?filename=image_123.png",
  "error": null
}
```

### Konfiguracja ComfyUI

**W `.env`:**
```env
COMFYUI_API_URL=http://192.168.0.14:8188
COMFYUI_POLLING_INTERVAL=10
COMFYUI_MAX_POLLING_TIME=300
```

**W `config.py`:**
```python
comfyui_api_url: str = Field(default="http://192.168.0.14:8188")
comfyui_polling_interval: int = Field(default=10)  # seconds between status checks
comfyui_max_polling_time: int = Field(default=300)  # max seconds to wait
```

### Workflow Generation

Workflow jest budowany w metodzie `_build_workflow()`:

1. **Wybór konfiguracji modelu:**
   ```python
   model_configs = {
       "Flux Dev": {
           "name": "flux1-dev-fp8.safetensors",
           "steps": 28,
           "cfg": 3.5,
           "sampler": "euler",
           "scheduler": "simple"
       },
       "Flux Krea": {
           "name": "flux1-krea-fp8.safetensors",
           "steps": 20,
           "cfg": 3.5,
           "sampler": "euler",
           "scheduler": "simple"
       },
       # ... więcej konfiguracji
   }
   ```

2. **Budowanie workflow:**
   - Load Checkpoint
   - CLIP Text Encode (positive/negative)
   - KSampler
   - VAE Decode
   - Save Image

3. **Dodawanie LoRA (jeśli potrzebne):**
   - LoraLoader node
   - Połączenie z model i clip

### Polling i Status Checking

```python
async def check_status(prompt_id: str) -> ImageStatusResponse:
    """Check generation status by polling ComfyUI."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.comfyui_url}/history/{prompt_id}"
        )
        # Parse response and return status
```

**Statusy:**
- `pending` - Oczekuje na rozpoczęcie
- `processing` - W trakcie generacji
- `completed` - Zakończone pomyślnie
- `failed` - Błąd generacji

### Zapis do Bazy Danych

Po zakończeniu generacji, obraz jest automatycznie zapisywany:

1. **Pobranie obrazu z ComfyUI:**
   ```python
   image_url = f"{comfyui_url}/view?filename={filename}"
   ```

2. **Upload do bazy (NocoDB/Baserow):**
   ```python
   # NocoDB
   attachment_data = [{
       "title": filename,
       "url": image_url,
       "mimetype": "image/png",
       "size": file_size
   }]
   await db_client.update_row("scenes", scene_id, {
       "Image": json.dumps(attachment_data)
   })
   ```

3. **Aktualizacja statusu sceny:**
   ```python
   await db_client.update_row("scenes", scene_id, {
       "Status": "Image Generated"
   })
   ```

---

## Migracja z Baserow

### Proces Migracji

1. **Przygotowanie:**
   - Utworzenie schematu NocoDB (`scripts/create_nocodb_schema.py`)
   - Konfiguracja `.env` (`USE_NOCODB=true`)

2. **Migracja Danych (opcjonalna):**
   - Export z Baserow
   - Transformacja danych
   - Import do NocoDB

3. **Aktualizacja Kodu:**
   - Wszystkie endpointy używają `ExtendedDatabaseClient`
   - Automatyczne przełączanie na podstawie `use_nocodb` flag

4. **Testowanie:**
   - Test wszystkich faz (Phase 1-26)
   - Weryfikacja zapisu danych
   - Weryfikacja odczytu danych

### Feature Flag

```python
# W config.py
use_nocodb: bool = Field(default=True)  # True = NocoDB, False = Baserow
use_baserow: bool = Field(default=False)  # Legacy support
```

**Przełączanie:**
```env
# .env
USE_NOCODB=true
USE_BASEROW=false
```

### Kompatybilność

Kod jest w pełni kompatybilny z obiema bazami dzięki `UnifiedDatabaseClient`:

```python
# Ten sam kod działa z NocoDB i Baserow
client = ExtendedDatabaseClient(settings)
project = await client.get_project(1)  # Automatycznie używa odpowiedniej bazy
```

---

## Konfiguracja

### NocoDB

**W `.env`:**
```env
# NocoDB Configuration
NOCODB_API_URL=http://192.168.0.4:30183
NOCODB_API_TOKEN=nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw
NOCODB_PROJECT_ID=pmcr6sel7s7gjwj

# Database Selection
USE_NOCODB=true
USE_BASEROW=false
```

**W `config.py`:**
```python
nocodb_api_url: str = Field(default="http://192.168.0.4:30183")
nocodb_api_token: str = Field(default="nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw")
nocodb_project_id: str = Field(default="pmcr6sel7s7gjwj")
use_nocodb: bool = Field(default=True)
use_baserow: bool = Field(default=False)
```

### ComfyUI

**W `.env`:**
```env
# ComfyUI Configuration
COMFYUI_API_URL=http://192.168.0.14:8188
COMFYUI_POLLING_INTERVAL=10
COMFYUI_MAX_POLLING_TIME=300
```

**W `config.py`:**
```python
comfyui_api_url: str = Field(default="http://192.168.0.14:8188")
comfyui_polling_interval: int = Field(default=10)
comfyui_max_polling_time: int = Field(default=300)
```

---

## Przykłady Użycia

### NocoDB - Podstawowe Operacje

```python
from poly_scribe.core.config import get_settings
from poly_scribe.services.db_client_extended import get_extended_database_client

settings = get_settings()
client = get_extended_database_client(settings)

# Pobierz projekt
project = await client.get_project(1)
print(f"Title: {project.title}")
print(f"Status: {project.status}")

# Utwórz rozdział
chapter = await client.create_chapter_dict({
    "Video": 1,
    "Chapter Number": 1,
    "Chapter Title": "Introduction",
    "Narrator Script": "This is the introduction..."
})

# Aktualizuj projekt
await client.update_project(1, {
    "Status": "Complete",
    "Title": "Updated Title"
})

# Pobierz wszystkie rozdziały projektu
chapters = await client.get_chapters_for_project_dict(1)
for chapter in chapters:
    print(f"Chapter {chapter['fields']['Chapter Number']}: {chapter['fields']['Chapter Title']}")
```

### ComfyUI - Generacja Obrazu

```python
from poly_scribe.core.config import get_settings
from poly_scribe.services.image_generator_service import ImageGeneratorService, ImageGenerateRequest, ImageProvider
from poly_scribe.services.db_client_extended import get_extended_database_client

settings = get_settings()
db_client = get_extended_database_client(settings)
service = ImageGeneratorService(settings, db_client)

# Generuj obraz
request = ImageGenerateRequest(
    scene_id=123,
    positive_prompt="A dramatic scene in Caravaggio style with chiaroscuro lighting",
    negative_prompt="modern, digital, blurry, low quality",
    style_name="Caravaggio Dramatic",
    image_provider=ImageProvider.FLUX_KREA,
    save_to_baserow=True
)

response = await service.generate(request)
print(f"Prompt ID: {response.prompt_id}")
print(f"Estimated time: {response.estimated_time_seconds}s")

# Sprawdź status
status = await service.check_status(response.prompt_id)
if status.status == "completed":
    print(f"Image URL: {status.image_url}")
```

### Phase 22 - Automatyczna Generacja Obrazów

```python
# Endpoint: POST /api/v1/workflow/phase-22/image-generation
# Request:
{
    "project_id": 1,
    "scene_id": 123  # Opcjonalne - jeśli podane, przetwarza tylko tę scenę
}

# Automatycznie:
# 1. Pobiera sceny z master_prompt
# 2. Generuje obrazy dla każdej sceny
# 3. Zapisuje obrazy do bazy
# 4. Aktualizuje status scen
```

---

## Troubleshooting

### NocoDB

**Problem: Field not found**
```
Error: Field 'Title' not found in table 'video'
```
**Rozwiązanie:**
- Sprawdź czy kolumna istnieje: `python scripts/create_nocodb_schema.py`
- Sprawdź czy używasz `user_field_names=true` w URL

**Problem: ID field required**
```
Error: A value is required for this field (Id)
```
**Rozwiązanie:**
- `NocoDBClient.create_row()` automatycznie generuje ID
- Jeśli problem pozostaje, sprawdź czy pole `Id` jest required w schemacie

**Problem: File upload failed**
```
Error: File upload failed on all endpoints
```
**Rozwiązanie:**
- Sprawdź czy NocoDB storage jest skonfigurowane
- Plik zostanie zapisany lokalnie jako fallback
- Sprawdź czy FastAPI serwuje pliki z `storage/uploads/`

### ComfyUI

**Problem: Connection refused**
```
Error: Failed to connect to ComfyUI
```
**Rozwiązanie:**
- Sprawdź czy ComfyUI działa: `curl http://192.168.0.14:8188/`
- Sprawdź `COMFYUI_API_URL` w `.env`
- Sprawdź firewall/network settings

**Problem: Generation timeout**
```
Error: Generation timed out after 300 seconds
```
**Rozwiązanie:**
- Zwiększ `COMFYUI_MAX_POLLING_TIME` w `.env`
- Sprawdź logi ComfyUI czy generacja się rozpoczęła
- Sprawdź czy model jest załadowany w ComfyUI

**Problem: Invalid workflow**
```
Error: Invalid workflow structure
```
**Rozwiązanie:**
- Sprawdź czy model istnieje w ComfyUI (`models/checkpoints/`)
- Sprawdź czy LoRA istnieje (jeśli używane)
- Sprawdź logi ComfyUI dla szczegółów błędu

---

## Dodatkowe Zasoby

### Dokumentacja NocoDB
- API Documentation: https://docs.nocodb.com/
- Schema Management: https://docs.nocodb.com/developer-resources/rest-apis

### Dokumentacja ComfyUI
- API Documentation: https://github.com/comfyanonymous/ComfyUI
- Workflow Examples: https://github.com/comfyanonymous/ComfyUI_examples

### Pliki w Projekcie
- `src/poly_scribe/services/nocodb_client.py` - NocoDB Client
- `src/poly_scribe/services/db_client.py` - Unified Database Client
- `src/poly_scribe/services/db_client_extended.py` - Extended Database Client
- `src/poly_scribe/db/schema.py` - Schema Definitions
- `src/poly_scribe/services/image_generator_service.py` - ComfyUI Service
- `src/poly_scribe/api/v1/image_generator_endpoints.py` - ComfyUI Endpoints
- `scripts/create_nocodb_schema.py` - Schema Creation Script
- `scripts/add_phase7_columns.py` - Example: Adding Columns

---

## Changelog

### 2025-11-21
- ✅ Dodano pełną implementację NocoDB
- ✅ Dodano migrację z Baserow
- ✅ Dodano ComfyUI integration
- ✅ Dodano file upload z fallback
- ✅ Dodano Voice Time Formatted field
- ✅ Dodano Phase 7 columns

---

**Ostatnia aktualizacja:** 2025-11-21

