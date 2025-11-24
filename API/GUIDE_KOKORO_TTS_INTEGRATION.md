# Przewodnik Integracji: Kokoro TTS

## Spis Treści

1. [Kokoro TTS - Przegląd](#kokoro-tts---przegląd)
2. [Konfiguracja](#konfiguracja)
3. [Struktura Implementacji](#struktura-implementacji)
4. [Model Danych (Pydantic)](#model-danych-pydantic)
5. [Service Layer](#service-layer)
6. [API Endpoints](#api-endpoints)
7. [Integracja z Orchestratorem](#integracja-z-orchestratorem)
8. [Przykłady Użycia](#przykłady-użycia)
9. [Schemat do Replikacji dla Innych Serwisów](#schemat-do-replikacji-dla-innych-serwisów)

---

## Kokoro TTS - Przegląd

Kokoro TTS to serwis syntezy mowy (Text-to-Speech) zintegrowany z Poly-Scribe Engine, oferujący:
- Generowanie audio z tekstu
- Wyodrębnianie timestampów dla każdego słowa
- Obsługę wielu głosów
- Kontrolę prędkości syntezy
- Format odpowiedzi zgodny z OpenAI API

---

## Konfiguracja

### Wymagane Zmienne Środowiskowe (.env)

```env
# Kokoro TTS Configuration
KOKORO_TTS_BASE_URL=http://192.168.0.14:8880
KOKORO_TTS_URL=http://192.168.0.14:8880/dev/captioned_speech
KOKORO_TTS_VOICE=am_adam
KOKORO_TTS_SPEED=1
KOKORO_TTS_STREAM=false

# Timeout Configuration
TTS_TIMEOUT_SECONDS=120
```

### Konfiguracja w Settings (src/poly_scribe/core/config.py)

```python
class Settings(BaseSettings):
    # Kokoro TTS Configuration
    kokoro_tts_base_url: str
    kokoro_tts_url: str  # Keep for backward compatibility
    kokoro_tts_voice: str = Field(default="am_adam")
    kokoro_tts_speed: float = Field(default=1.0)
    kokoro_tts_stream: bool = Field(default=False)
    
    # Timeout Configuration
    tts_timeout_seconds: int = Field(default=120)
```

---

## Struktura Implementacji

Integracja Kokoro TTS składa się z następujących komponentów:

1. **Models** (`src/poly_scribe/models/__init__.py`) - Modele Pydantic dla request/response
2. **Service** (`src/poly_scribe/services/tts_service.py`) - Logika biznesowa i komunikacja z API
3. **API Endpoints** (`src/poly_scribe/api/v1/tts_endpoints.py`) - FastAPI router z endpointami
4. **Orchestrator Integration** (`src/poly_scribe/services/orchestrator.py`) - Integracja z głównym workflow

---

## Model Danych (Pydantic)

### Request Model

```python
class KokoroTTSRequest(BaseModel):
    """Request model for Kokoro TTS API."""
    input: str
    voice: str = "default"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    stream: bool = False
```

**Lokalizacja:** `src/poly_scribe/models/__init__.py` (linia 474-479)

### Response Model

```python
class KokoroTTSResponse(BaseModel):
    """Response model for Kokoro TTS API."""
    audio: str  # Base64 encoded audio or data URL
    timestamps: List[Dict[str, Any]] = Field(default_factory=list)
    duration: Optional[float] = None
    word_count: Optional[int] = None
```

**Lokalizacja:** `src/poly_scribe/models/__init__.py` (linia 492-497)

### Custom Exception

```python
class KokoroTTSError(Exception):
    """Custom exception for Kokoro TTS API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
```

**Lokalizacja:** `src/poly_scribe/services/tts_service.py` (linia 21-27)

---

## Service Layer

### Struktura Klasy Service

```python
class KokoroTTSService:
    """Service for interacting with Kokoro TTS API."""
    
    def __init__(self, settings: Settings):
        """Initialize Kokoro TTS service."""
        self.settings = settings
        self.base_url = settings.kokoro_tts_url
        self.timeout = settings.tts_timeout_seconds
        self.max_retries = settings.max_retries
        
        # Default TTS parameters
        self.default_voice = settings.kokoro_tts_voice
        self.default_speed = settings.kokoro_tts_speed
        self.default_stream = settings.kokoro_tts_stream
```

**Lokalizacja:** `src/poly_scribe/services/tts_service.py` (linia 30-43)

### Główne Metody

#### 1. _make_request() - Podstawowa metoda HTTP z retry logic

```python
async def _make_request(
    self,
    method: str,
    url: str,
    data: Optional[Dict[str, Any]] = None,
    retries: Optional[int] = None
) -> Response:
    """Make HTTP request with retry logic."""
    # Exponential backoff retry mechanism
    # Error handling with custom exceptions
    # Timeout handling
```

**Cechy:**
- Exponential backoff retry (2^attempt * delay)
- Custom exception handling (KokoroTTSError)
- Timeout management
- Status code validation

**Lokalizacja:** `src/poly_scribe/services/tts_service.py` (linia 45-91)

#### 2. synthesize_speech() - Podstawowa synteza mowy

```python
async def synthesize_speech(
    self,
    text: str,
    voice: Optional[str] = None,
    speed: Optional[float] = None,
    stream: Optional[bool] = None
) -> KokoroTTSResponse:
    """Synthesize speech from text using Kokoro TTS API."""
```

**Zwraca:**
- `KokoroTTSResponse` z audio (base64) i timestampami

**Lokalizacja:** `src/poly_scribe/services/tts_service.py` (linia 93-141)

#### 3. generate_audio_with_timestamps() - Kompleksowa generacja audio

```python
async def generate_audio_with_timestamps(
    self,
    narrator_script: str,
    voice: Optional[str] = None,
    speed: Optional[float] = None
) -> Tuple[bytes, Dict[str, Any], float]:
    """Generate audio file and extract timestamps.
    
    Returns:
        Tuple of (audio_bytes, timestamps_dict, duration_seconds)
    """
```

**Zwraca:**
- `bytes` - surowe dane audio
- `Dict[str, Any]` - timestamps jako słownik
- `float` - długość audio w sekundach

**Lokalizacja:** `src/poly_scribe/services/tts_service.py` (linia 143-199)

#### 4. Metody Pomocnicze

- `_clean_script_for_tts()` - Czyszczenie tekstu przed syntezą
- `_decode_audio()` - Dekodowanie base64 audio
- `_calculate_duration()` - Obliczanie długości z timestampów
- `get_supported_voices()` - Lista dostępnych głosów
- `get_voice_info()` - Informacje o konkretnym głosie

**Lokalizacja:** `src/poly_scribe/services/tts_service.py` (linia 315-458)

---

## API Endpoints

### Struktura Routera

```python
from fastapi import APIRouter, Depends
from ...services.tts_service import KokoroTTSService

router = APIRouter(tags=["TTS"])

def get_tts_service(settings: Settings = Depends(get_settings)) -> KokoroTTSService:
    """Get TTS service instance."""
    return KokoroTTSService(settings)
```

**Lokalizacja:** `src/poly_scribe/api/v1/tts_endpoints.py` (linia 22-27)

### Dostępne Endpointy

#### 1. Health Check

```python
@router.get("/health")
async def health_check():
    """Health check endpoint for TTS service."""
    return {"status": "healthy", "service": "kokoro-tts"}
```

**Endpoint:** `GET /api/v1/tts/health`

#### 2. OpenAI-Compatible Speech

```python
@router.post("/audio/speech")
async def openai_compatible_speech(
    request: Request,
    response: Response,
    tts_service: KokoroTTSService = Depends(get_tts_service)
):
    """OpenAI-compatible TTS endpoint."""
```

**Endpoint:** `POST /api/v1/tts/audio/speech`

**Request Body:**
```json
{
    "input": "Text to synthesize",
    "voice": "am_adam",
    "speed": 1.0,
    "model": "tts-1"
}
```

**Response:** Streaming audio (audio/mpeg)

#### 3. Captioned Speech (Main TTS Endpoint)

```python
@router.post("/dev/captioned_speech")
async def captioned_speech(
    request: Request,
    tts_service: KokoroTTSService = Depends(get_tts_service)
):
    """Generate speech with captions/timestamps."""
```

**Endpoint:** `POST /api/v1/tts/dev/captioned_speech`

**Request Body:**
```json
{
    "input": "Text to synthesize",
    "voice": "am_adam",
    "speed": 1.0
}
```

**Response:**
```json
{
    "audio": "data:audio/mpeg;base64,...",
    "timestamps": [...],
    "duration": 10.5,
    "word_count": 20
}
```

#### 4. Get Available Voices

```python
@router.get("/voices")
async def get_voices(tts_service: KokoroTTSService = Depends(get_tts_service)):
    """Get available voices."""
```

**Endpoint:** `GET /api/v1/tts/voices`

**Response:**
```json
{
    "voices": {
        "am_adam": {
            "name": "Adam",
            "gender": "male",
            "language": "en-US",
            "description": "Professional male voice"
        },
        ...
    },
    "default_voice": "am_adam"
}
```

**Lokalizacja:** `src/poly_scribe/api/v1/tts_endpoints.py`

---

## Integracja z Orchestratorem

### Inicjalizacja w Orchestratorze

```python
from poly_scribe.services.tts_service import KokoroTTSService, KokoroTTSError

class WorkflowOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_client = get_extended_database_client(settings)
        self.llm_service = OpenRouterService(settings)
        self.tts_service = KokoroTTSService(settings)  # <-- Inicjalizacja
```

**Lokalizacja:** `src/poly_scribe/services/orchestrator.py` (linia 27, 38)

### Użycie w Workflow

```python
# Przykład użycia w Phase 3 (TTS Generation)
async def execute_phase3_tts_generation(self, project_id: int):
    # ... pobranie narrator_script z Baserow ...
    
    # Generowanie audio z timestampami
    audio_bytes, timestamps_data, duration = await self.tts_service.generate_audio_with_timestamps(
        narrator_script=narrator_script,
        voice=self.settings.kokoro_tts_voice,
        speed=self.settings.kokoro_tts_speed
    )
    
    # ... zapis audio i timestampów do Baserow ...
```

---

## Przykłady Użycia

### 1. Podstawowe Użycie Service

```python
from poly_scribe.services.tts_service import KokoroTTSService
from poly_scribe.core.config import get_settings

settings = get_settings()
tts_service = KokoroTTSService(settings)

# Synteza mowy
response = await tts_service.synthesize_speech(
    text="Hello, this is a test.",
    voice="am_adam",
    speed=1.0
)

print(f"Audio: {response.audio[:50]}...")  # Base64 preview
print(f"Timestamps: {len(response.timestamps)} entries")
```

### 2. Kompleksowa Generacja z Timestampami

```python
# Generowanie audio z pełnymi danymi
audio_bytes, timestamps, duration = await tts_service.generate_audio_with_timestamps(
    narrator_script="Long narrator script text...",
    voice="am_emma",
    speed=1.1
)

print(f"Audio size: {len(audio_bytes)} bytes")
print(f"Duration: {duration:.2f} seconds")
print(f"Timestamps: {timestamps}")
```

### 3. Użycie przez API Endpoint

```python
import httpx

# Request do API
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://127.0.0.1:8001/api/v1/tts/dev/captioned_speech",
        json={
            "input": "Text to synthesize",
            "voice": "am_adam",
            "speed": 1.0
        }
    )
    
    result = response.json()
    audio_data = result["audio"]
    timestamps = result["timestamps"]
    duration = result["duration"]
```

### 4. Error Handling

```python
from poly_scribe.services.tts_service import KokoroTTSError

try:
    response = await tts_service.synthesize_speech("Test")
except KokoroTTSError as e:
    print(f"TTS Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response Data: {e.response_data}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Schemat do Replikacji dla Innych Serwisów

Aby zaimplementować podobną integrację dla **Robbie** (lub innego serwisu), wykonaj następujące kroki:

### Krok 1: Modele Pydantic

Utwórz modele request/response w `src/poly_scribe/models/__init__.py`:

```python
class RobbieRequest(BaseModel):
    """Request model for Robbie API."""
    input: str
    # ... inne pola specyficzne dla Robbie ...

class RobbieResponse(BaseModel):
    """Response model for Robbie API."""
    # ... pola odpowiedzi ...
```

### Krok 2: Custom Exception

Utwórz wyjątek w `src/poly_scribe/services/robbie_service.py`:

```python
class RobbieError(Exception):
    """Custom exception for Robbie API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
```

### Krok 3: Service Class

Utwórz klasę service w `src/poly_scribe/services/robbie_service.py`:

```python
class RobbieService:
    """Service for interacting with Robbie API."""
    
    def __init__(self, settings: Settings):
        """Initialize Robbie service."""
        self.settings = settings
        self.base_url = settings.robbie_api_url
        self.timeout = settings.robbie_timeout_seconds
        self.max_retries = settings.max_retries
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        retries: Optional[int] = None
    ) -> Response:
        """Make HTTP request with retry logic."""
        # Skopiuj implementację z KokoroTTSService._make_request()
        # Dostosuj do specyfiki Robbie API
    
    async def main_method(self, ...):
        """Główna metoda serwisu."""
        # Implementacja specyficzna dla Robbie
```

**Szablon Service:**

```python
"""
Robbie Service Module

This module provides integration with Robbie API.
"""

import asyncio
from typing import Any, Dict, Optional

import httpx
from httpx import AsyncClient, Response

from ..logger_config import logger
from ..core.config import Settings
from ..models import RobbieRequest, RobbieResponse


class RobbieError(Exception):
    """Custom exception for Robbie API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RobbieService:
    """Service for interacting with Robbie API."""
    
    def __init__(self, settings: Settings):
        """Initialize Robbie service."""
        self.settings = settings
        self.base_url = settings.robbie_api_url
        self.timeout = settings.robbie_timeout_seconds
        self.max_retries = settings.max_retries
        
        # Default parameters
        self.default_param = settings.robbie_default_param
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        retries: Optional[int] = None
    ) -> Response:
        """Make HTTP request with retry logic."""
        if retries is None:
            retries = self.max_retries
            
        async with AsyncClient(timeout=self.timeout) as client:
            for attempt in range(retries):
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data
                    )
                    
                    if response.status_code >= 400:
                        error_data = None
                        try:
                            error_data = response.json()
                        except:
                            error_data = {"error": response.text}
                        
                        raise RobbieError(
                            f"Robbie API error: {response.status_code}",
                            status_code=response.status_code,
                            response_data=error_data
                        )
                    
                    return response
                    
                except httpx.TimeoutException:
                    if attempt == retries - 1:
                        raise RobbieError("Request timeout after retries")
                    await asyncio.sleep(self.settings.retry_delay_seconds * (2 ** attempt))
                    
                except httpx.RequestError as e:
                    if attempt == retries - 1:
                        raise RobbieError(f"Request error: {str(e)}")
                    await asyncio.sleep(self.settings.retry_delay_seconds * (2 ** attempt))
            
            raise RobbieError("Unexpected error: all retries exhausted")
    
    async def main_method(self, param: str) -> RobbieResponse:
        """Main method for Robbie service."""
        request_data = RobbieRequest(
            input=param,
            # ... inne pola ...
        )
        
        try:
            response = await self._make_request(
                "POST",
                self.base_url,
                data=request_data.dict()
            )
            
            response_data = response.json()
            
            # Validate response structure
            if "expected_field" not in response_data:
                raise RobbieError("No expected_field in response")
            
            return RobbieResponse(
                # ... mapowanie pól ...
            )
            
        except Exception as e:
            logger.error(f"Robbie operation failed: {str(e)}")
            raise RobbieError(f"Robbie operation failed: {str(e)}")
```

### Krok 4: Konfiguracja w Settings

Dodaj konfigurację do `src/poly_scribe/core/config.py`:

```python
class Settings(BaseSettings):
    # Robbie Configuration
    robbie_api_url: str
    robbie_timeout_seconds: int = Field(default=120)
    robbie_default_param: str = Field(default="default_value")
```

### Krok 5: API Endpoints

Utwórz router w `src/poly_scribe/api/v1/robbie_endpoints.py`:

```python
"""
Robbie API Endpoints

This module provides FastAPI endpoints for Robbie integration.
"""

from fastapi import APIRouter, HTTPException, Depends
from ...logger_config import logger
from ...core.config import get_settings, Settings
from ...models import RobbieRequest, RobbieResponse
from ...services.robbie_service import RobbieService, RobbieError

router = APIRouter(tags=["Robbie"])

def get_robbie_service(settings: Settings = Depends(get_settings)) -> RobbieService:
    """Get Robbie service instance."""
    return RobbieService(settings)


@router.get("/health")
async def health_check():
    """Health check endpoint for Robbie service."""
    return {"status": "healthy", "service": "robbie"}


@router.post("/main-endpoint")
async def main_endpoint(
    request: RobbieRequest,
    robbie_service: RobbieService = Depends(get_robbie_service)
):
    """Main endpoint for Robbie service."""
    try:
        result = await robbie_service.main_method(request.input)
        return result
    except RobbieError as e:
        logger.error(f"Robbie service error: {str(e)}")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
    except Exception as e:
        logger.error(f"Robbie endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
```

### Krok 6: Rejestracja Routera

Dodaj router do głównego pliku API w `src/poly_scribe/api/main.py`:

```python
from .v1 import robbie_endpoints

app.include_router(
    robbie_endpoints.router,
    prefix="/api/v1/robbie",
    tags=["Robbie"]
)
```

### Krok 7: Integracja z Orchestratorem (opcjonalnie)

Dodaj serwis do orchestratora w `src/poly_scribe/services/orchestrator.py`:

```python
from poly_scribe.services.robbie_service import RobbieService, RobbieError

class WorkflowOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_client = get_extended_database_client(settings)
        self.llm_service = OpenRouterService(settings)
        self.tts_service = KokoroTTSService(settings)
        self.robbie_service = RobbieService(settings)  # <-- Dodaj
```

---

## Checklist dla Nowej Integracji

- [ ] Utworzono modele Pydantic (Request/Response)
- [ ] Utworzono Custom Exception class
- [ ] Utworzono Service class z metodą `_make_request()` (retry logic)
- [ ] Zaimplementowano główne metody serwisu
- [ ] Dodano konfigurację do Settings
- [ ] Utworzono API Endpoints (router)
- [ ] Zarejestrowano router w main.py
- [ ] Dodano zmienne środowiskowe do .env
- [ ] Dodano integrację z Orchestratorem (jeśli potrzebne)
- [ ] Dodano error handling i logging
- [ ] Utworzono testy jednostkowe
- [ ] Zaktualizowano dokumentację

---

## Porównanie z Innymi Integracjami

| Element | Kokoro TTS | NCA Toolkit | NocoDB |
|---------|------------|-------------|--------|
| **Authentication** | None (URL-based) | API Key (X-API-Key) | Token (xc-token) |
| **Request Format** | JSON body | JSON body | JSON body |
| **Response Format** | JSON + Base64 audio | JSON | JSON |
| **Retry Logic** | Exponential backoff | Exponential backoff | Exponential backoff |
| **Error Handling** | Custom Exception | Custom Exception | Custom Exception |
| **Service Layer** | Tak | Tak | Tak |
| **API Endpoints** | FastAPI Router | FastAPI Router | FastAPI Router |

**Wspólny schemat:**
1. Service class z `_make_request()` metodą
2. Custom exception class
3. Pydantic models dla request/response
4. FastAPI router z dependency injection
5. Konfiguracja przez Settings
6. Integracja z Orchestratorem (jeśli potrzebne)

---

## Podsumowanie

Integracja Kokoro TTS pokazuje standardowy schemat implementacji zewnętrznych serwisów w Poly-Scribe Engine:

1. **Service Layer** - Enkapsulacja logiki biznesowej i komunikacji z API
2. **Models** - Typowane modele Pydantic dla request/response
3. **API Endpoints** - FastAPI router z dependency injection
4. **Error Handling** - Custom exceptions z informacją o błędach
5. **Retry Logic** - Exponential backoff dla niezawodności
6. **Configuration** - Centralna konfiguracja przez Settings

Ten schemat może być użyty do implementacji **Robbie** lub innego podobnego serwisu.

