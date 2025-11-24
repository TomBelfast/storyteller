# Przewodnik Integracji: NCA Toolkit

## Spis Treści

1. [NCA Toolkit - Podstawowe Połączenie](#nca-toolkit---podstawowe-połączenie)
2. [API Endpoints](#api-endpoints)
3. [Przykłady Użycia](#przykłady-użycia)
4. [Troubleshooting](#troubleshooting)

---

## NCA Toolkit - Podstawowe Połączenie

### Przegląd

NCA Toolkit (No Code Architects Toolkit) to API do przetwarzania wideo i audio, oferujące:
- Konwersję obrazów na wideo (Image to Video)
- Łączenie klipów wideo (Video Concatenation)
- Kompozycję wideo z audio (FFmpeg Compose)
- Pobieranie długości audio (Audio Duration)

### Konfiguracja

**Wymagane dane:**
- `NCA_API_URL` - Adres API NCA Toolkit (np. `http://192.168.0.18:8080`)
- `NCA_API_KEY` - Klucz API (np. `Swiat1976@#$`)
- `AUDIO_DURATION_API_URL` - Adres API Audio Duration (np. `http://192.168.0.18:8081/get-audio-duration`)
- `AUDIO_DURATION_API_KEY` - Klucz API Audio Duration (np. `Swiat1976@#$`)

**Przykład konfiguracji:**
```python
NCA_API_URL = "http://192.168.0.18:8080"
NCA_API_KEY = "Swiat1976@#$"
AUDIO_DURATION_API_URL = "http://192.168.0.18:8081/get-audio-duration"
AUDIO_DURATION_API_KEY = "Swiat1976@#$"
```

### Autentykacja

NCA Toolkit używa API key authentication przez header `X-API-Key`:

```python
headers = {
    "X-API-Key": NCA_API_KEY,
    "Content-Type": "application/json"
}
```

### Podstawowa Struktura Klienta

```python
import httpx
from typing import Dict, Any, Optional, List

class NCAToolkitClient:
    def __init__(self, api_url: str, api_key: str):
        self.base_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: float = 3600.0
    ) -> Dict[str, Any]:
        """Wykonaj request HTTP do NCA Toolkit API."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "POST":
                response = await client.post(url, headers=self.headers, json=data)
            elif method.upper() == "GET":
                response = await client.get(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
```

---

## API Endpoints

### 1. Image to Video (Transform Image to Video)

**Endpoint:**
```
POST /v1/image/transform/video
```

**Opis:** Konwertuje obraz statyczny na klip wideo z efektem zoom in.

**Headers:**
```
Content-Type: application/json
X-API-Key: {api_key}
```

**Request Body:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "length": 6.5,
  "frame_rate": 25,
  "zoom_speed": 3,
  "id": "scene_123"
}
```

**Parametry:**
- `image_url` (string, required) - URL obrazu do konwersji
- `length` (float, required) - Długość klipu w sekundach
- `frame_rate` (int, optional) - Frame rate (domyślnie 25)
- `zoom_speed` (int, optional) - Prędkość zoom (0 = static, 1-100 = zoom in speed, domyślnie 3)
- `id` (string, optional) - ID identyfikujące request (używane w nazwie pliku wyjściowego)

**Response:**
```json
{
  "response": "https://minio2-api.aihub.ovh/nca-toolkit/videos/clip_123.mp4",
  "duration": 6.5
}
```

**Response Fields:**
- `response` (string) - URL wygenerowanego klipu wideo
- `duration` (float, optional) - Rzeczywista długość klipu (może różnić się od żądanej)

**Przykład użycia:**
```python
async def transform_image_to_video(
    self,
    image_url: str,
    length: float,
    frame_rate: int = 25,
    zoom_speed: int = 3,
    scene_id: Optional[str] = None
) -> Dict[str, Any]:
    """Konwertuj obraz na wideo."""
    request_data = {
        "image_url": image_url,
        "length": length,
        "frame_rate": frame_rate,
        "zoom_speed": zoom_speed,
        "id": scene_id or "video"
    }
    
    return await self._make_request("POST", "/v1/image/transform/video", data=request_data)
```

### 2. Video Concatenation (Łączenie Klipów)

**Endpoint:**
```
POST /v1/video/concatenate
```

**Opis:** Łączy wiele klipów wideo w jeden finalny film.

**Headers:**
```
Content-Type: application/json
X-API-Key: {api_key}
```

**Request Body:**
```json
{
  "video_urls": [
    {"video_url": "https://example.com/clip1.mp4"},
    {"video_url": "https://example.com/clip2.mp4"},
    {"video_url": "https://example.com/clip3.mp4"}
  ],
  "id": "project_16"
}
```

**Parametry:**
- `video_urls` (array, required) - Lista obiektów z `video_url` (klipy są łączone w kolejności)
- `id` (string, optional) - ID identyfikujące request (używane w nazwie pliku wyjściowego)

**Response:**
```json
{
  "response": "https://minio2-api.aihub.ovh/nca-toolkit/videos/raw_video_16.mp4"
}
```

**Response Fields:**
- `response` (string) - URL połączonego filmu

**Przykład użycia:**
```python
async def concatenate_videos(
    self,
    video_urls: List[str],
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Połącz wiele klipów wideo w jeden film."""
    # Normalizuj URL (usuń podwójne slashy)
    import re
    normalized_urls = []
    for url in video_urls:
        normalized_url = re.sub(r'([^:])\/\/+', r'\1/', url)
        normalized_urls.append({"video_url": normalized_url})
    
    request_data = {
        "video_urls": normalized_urls,
        "id": project_id or "concatenated"
    }
    
    return await self._make_request("POST", "/v1/video/concatenate", data=request_data)
```

### 3. FFmpeg Compose (Video + Audio Composition)

**Endpoint:**
```
POST /v1/ffmpeg/compose
```

**Opis:** Łączy wideo z audio używając FFmpeg, tworząc finalny film z zsynchronizowanym audio.

**Headers:**
```
Content-Type: application/json
X-API-Key: {api_key}
```

**Request Body:**
```json
{
  "id": "audio-layering",
  "inputs": [
    {
      "file_url": "https://example.com/video.mp4"
    },
    {
      "file_url": "https://example.com/audio.mp3"
    }
  ],
  "filters": [
    {
      "filter": "[1:a]volume=1[outa]"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-map", "argument": "0:v"},
        {"option": "-map", "argument": "[outa]"},
        {"option": "-c:v", "argument": "copy"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ]
}
```

**Parametry:**
- `id` (string, required) - ID identyfikujące request
- `inputs` (array, required) - Lista plików wejściowych (wideo jako pierwszy, audio jako drugi)
  - `file_url` (string) - URL pliku
- `filters` (array, optional) - Lista filtrów FFmpeg
  - `filter` (string) - Filtr FFmpeg (np. `[1:a]volume=1[outa]` dla normalizacji audio)
- `outputs` (array, required) - Lista opcji wyjściowych
  - `options` (array) - Lista opcji FFmpeg
    - `option` (string) - Opcja FFmpeg (np. `-map`, `-c:v`, `-c:a`)
    - `argument` (string) - Argument opcji

**Response:**
```json
{
  "response": [
    {
      "file_url": "https://minio2-api.aihub.ovh/nca-toolkit/videos/video_audio_16.mp4"
    }
  ]
}
```

**Response Fields:**
- `response` (array) - Lista obiektów z `file_url` (URL finalnego filmu z audio)

**Przykład użycia:**
```python
async def compose_video_audio(
    self,
    video_url: str,
    audio_url: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Połącz wideo z audio."""
    request_data = {
        "id": project_id or "audio-layering",
        "inputs": [
            {"file_url": video_url},
            {"file_url": audio_url}
        ],
        "filters": [
            {"filter": "[1:a]volume=1[outa]"}  # Normalizacja audio
        ],
        "outputs": [
            {
                "options": [
                    {"option": "-map", "argument": "0:v"},  # Mapuj wideo z pierwszego inputu
                    {"option": "-map", "argument": "[outa]"},  # Mapuj audio z filtra
                    {"option": "-c:v", "argument": "copy"},  # Kopiuj wideo bez re-encoding
                    {"option": "-c:a", "argument": "aac"}  # Konwertuj audio do AAC
                ]
            }
        ]
    }
    
    return await self._make_request("POST", "/v1/ffmpeg/compose", data=request_data)
```

### 4. Audio Duration (Pobieranie Długości Audio)

**Endpoint:**
```
POST /get-audio-duration
```

**Opis:** Pobiera długość pliku audio w sekundach.

**Uwaga:** Ten endpoint jest na osobnym serwerze (`AUDIO_DURATION_API_URL`), nie na głównym NCA API.

**Headers:**
```
Content-Type: application/json
X-API-Key: {api_key}
```

**Request Body:**
```json
{
  "audio_url": "https://example.com/audio.mp3",
  "id": "get-audio-duration"
}
```

**Parametry:**
- `audio_url` (string, required) - URL pliku audio
- `id` (string, optional) - ID identyfikujące request

**Response:**
```json
{
  "duration": 125.5
}
```

**Response Fields:**
- `duration` (float) - Długość audio w sekundach

**Przykład użycia:**
```python
class AudioDurationClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    async def get_audio_duration(self, audio_url: str) -> float:
        """Pobierz długość pliku audio."""
        request_data = {
            "audio_url": audio_url,
            "id": "get-audio-duration"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json=request_data
            )
            response.raise_for_status()
            result = response.json()
            return float(result.get("duration", 0))
```

---

## Przykłady Użycia

### Przykład 1: Konwersja Obrazu na Wideo

```python
import asyncio
from nca_toolkit_client import NCAToolkitClient

async def convert_image_to_video():
    client = NCAToolkitClient(
        api_url="http://192.168.0.18:8080",
        api_key="Swiat1976@#$"
    )
    
    result = await client.transform_image_to_video(
        image_url="https://example.com/scene_123.jpg",
        length=6.5,
        frame_rate=25,
        zoom_speed=3,
        scene_id="123"
    )
    
    clip_url = result.get("response")
    duration = result.get("duration", 6.5)
    
    print(f"Video generated: {clip_url}")
    print(f"Duration: {duration}s")

asyncio.run(convert_image_to_video())
```

### Przykład 2: Łączenie Klipów Wideo

```python
async def concatenate_clips():
    client = NCAToolkitClient(
        api_url="http://192.168.0.18:8080",
        api_key="Swiat1976@#$"
    )
    
    video_urls = [
        "https://minio2-api.aihub.ovh/nca-toolkit/videos/clip_1.mp4",
        "https://minio2-api.aihub.ovh/nca-toolkit/videos/clip_2.mp4",
        "https://minio2-api.aihub.ovh/nca-toolkit/videos/clip_3.mp4"
    ]
    
    result = await client.concatenate_videos(
        video_urls=video_urls,
        project_id="16"
    )
    
    final_video_url = result.get("response")
    print(f"Final video: {final_video_url}")

asyncio.run(concatenate_clips())
```

### Przykład 3: Kompozycja Wideo z Audio

```python
async def compose_video_with_audio():
    client = NCAToolkitClient(
        api_url="http://192.168.0.18:8080",
        api_key="Swiat1976@#$"
    )
    
    result = await client.compose_video_audio(
        video_url="https://minio2-api.aihub.ovh/nca-toolkit/videos/raw_video_16.mp4",
        audio_url="https://example.com/speech_16.mp3",
        project_id="16"
    )
    
    # Response jest listą
    response_data = result.get("response", [])
    if response_data and len(response_data) > 0:
        video_audio_url = response_data[0].get("file_url")
        print(f"Video with audio: {video_audio_url}")

asyncio.run(compose_video_with_audio())
```

### Przykład 4: Pobieranie Długości Audio

```python
from audio_duration_client import AudioDurationClient

async def get_audio_length():
    client = AudioDurationClient(
        api_url="http://192.168.0.18:8081/get-audio-duration",
        api_key="Swiat1976@#$"
    )
    
    duration = await client.get_audio_duration(
        audio_url="https://example.com/speech_16.mp3"
    )
    
    print(f"Audio duration: {duration}s")
    print(f"Audio duration: {int(duration // 60)}m {int(duration % 60)}s")

asyncio.run(get_audio_length())
```

### Przykład 5: Kompletny Workflow (Image → Video → Concatenate → Compose)

```python
async def complete_video_workflow():
    nca_client = NCAToolkitClient(
        api_url="http://192.168.0.18:8080",
        api_key="Swiat1976@#$"
    )
    
    audio_duration_client = AudioDurationClient(
        api_url="http://192.168.0.18:8081/get-audio-duration",
        api_key="Swiat1976@#$"
    )
    
    # Krok 1: Konwertuj obrazy na klipy wideo
    image_urls = [
        "https://example.com/scene_1.jpg",
        "https://example.com/scene_2.jpg",
        "https://example.com/scene_3.jpg"
    ]
    
    clip_urls = []
    for i, image_url in enumerate(image_urls, 1):
        result = await nca_client.transform_image_to_video(
            image_url=image_url,
            length=6.0,
            zoom_speed=3,
            scene_id=str(i)
        )
        clip_urls.append(result.get("response"))
        print(f"Clip {i} generated: {clip_urls[-1]}")
    
    # Krok 2: Połącz klipy w jeden film
    concatenate_result = await nca_client.concatenate_videos(
        video_urls=clip_urls,
        project_id="16"
    )
    raw_video_url = concatenate_result.get("response")
    print(f"Raw video: {raw_video_url}")
    
    # Krok 3: Pobierz długość audio
    audio_url = "https://example.com/speech_16.mp3"
    audio_duration = await audio_duration_client.get_audio_duration(audio_url)
    print(f"Audio duration: {audio_duration}s")
    
    # Krok 4: Połącz wideo z audio
    compose_result = await nca_client.compose_video_audio(
        video_url=raw_video_url,
        audio_url=audio_url,
        project_id="16"
    )
    
    response_data = compose_result.get("response", [])
    if response_data and len(response_data) > 0:
        final_video_url = response_data[0].get("file_url")
        print(f"Final video with audio: {final_video_url}")

asyncio.run(complete_video_workflow())
```

### Przykład 6: Batch Processing z Error Handling

```python
async def batch_process_scenes():
    client = NCAToolkitClient(
        api_url="http://192.168.0.18:8080",
        api_key="Swiat1976@#$"
    )
    
    scenes = [
        {"id": 1, "image_url": "https://example.com/scene_1.jpg", "duration": 5.0},
        {"id": 2, "image_url": "https://example.com/scene_2.jpg", "duration": 6.5},
        {"id": 3, "image_url": "https://example.com/scene_3.jpg", "duration": 4.0}
    ]
    
    results = []
    errors = []
    
    for scene in scenes:
        try:
            result = await client.transform_image_to_video(
                image_url=scene["image_url"],
                length=scene["duration"],
                scene_id=str(scene["id"])
            )
            results.append({
                "scene_id": scene["id"],
                "status": "success",
                "clip_url": result.get("response")
            })
        except Exception as e:
            errors.append({
                "scene_id": scene["id"],
                "status": "error",
                "error": str(e)
            })
            print(f"Error processing scene {scene['id']}: {e}")
    
    print(f"Processed: {len(results)}/{len(scenes)}")
    print(f"Errors: {len(errors)}")
    
    # Połącz wszystkie udane klipy
    if results:
        clip_urls = [r["clip_url"] for r in results if r["status"] == "success"]
        if clip_urls:
            concatenate_result = await client.concatenate_videos(
                video_urls=clip_urls,
                project_id="batch_1"
            )
            print(f"Batch video: {concatenate_result.get('response')}")

asyncio.run(batch_process_scenes())
```

---

## Konfiguracja Środowiska

### Zmienne Środowiskowe

```env
# NCA Toolkit
NCA_API_URL=http://192.168.0.18:8080
NCA_API_KEY=Swiat1976@#$

# Audio Duration Service
AUDIO_DURATION_API_URL=http://192.168.0.18:8081/get-audio-duration
AUDIO_DURATION_API_KEY=Swiat1976@#$
```

### Wymagane Biblioteki

```txt
httpx>=0.24.0
asyncio
```

### Instalacja

```bash
pip install httpx
```

---

## Troubleshooting

### Problem: Connection refused

```
Error: Failed to connect to NCA Toolkit
```

**Rozwiązanie:**
- Sprawdź czy NCA Toolkit działa: `curl http://192.168.0.18:8080/health` (jeśli dostępny)
- Sprawdź `NCA_API_URL` w konfiguracji
- Sprawdź firewall/network settings
- Sprawdź czy serwer jest dostępny z Twojej sieci

### Problem: 401 Unauthorized

```
Error: 401 Unauthorized
```

**Rozwiązanie:**
- Sprawdź czy `X-API-Key` header jest ustawiony
- Sprawdź czy klucz API jest poprawny
- Sprawdź czy klucz nie wygasł

### Problem: Timeout

```
Error: Request timed out
```

**Rozwiązanie:**
- Zwiększ timeout w `httpx.AsyncClient` (domyślnie 3600s dla długich operacji)
- Sprawdź czy serwer nie jest przeciążony
- Sprawdź rozmiar plików (duże pliki wymagają więcej czasu)

### Problem: Invalid image_url

```
Error: Image URL not accessible
```

**Rozwiązanie:**
- Sprawdź czy URL jest dostępny publicznie
- Sprawdź czy URL nie wymaga autentykacji
- Sprawdź czy plik istnieje i jest dostępny

### Problem: Video concatenation failed

```
Error: Failed to concatenate videos
```

**Rozwiązanie:**
- Sprawdź czy wszystkie URL klipów są dostępne
- Sprawdź czy klipy mają ten sam format (codec, resolution)
- Sprawdź czy URL nie zawierają podwójnych slashy (użyj normalizacji)
- Sprawdź czy lista `video_urls` nie jest pusta

### Problem: FFmpeg compose failed

```
Error: FFmpeg composition failed
```

**Rozwiązanie:**
- Sprawdź czy URL wideo i audio są dostępne
- Sprawdź czy format audio jest obsługiwany przez FFmpeg
- Sprawdź czy filtry FFmpeg są poprawne
- Sprawdź logi NCA Toolkit dla szczegółów błędu

### Problem: Audio duration not returned

```
Error: Duration not in response
```

**Rozwiązanie:**
- Sprawdź czy URL audio jest dostępny
- Sprawdź czy format audio jest obsługiwany
- Sprawdź czy endpoint Audio Duration działa
- Sprawdź czy `AUDIO_DURATION_API_URL` jest poprawny

---

## Uwagi Techniczne

### Timeouty

- **Image to Video:** 3600s (60 minut) - długie operacje mogą wymagać więcej czasu
- **Video Concatenation:** 3600s (60 minut) - zależy od liczby i rozmiaru klipów
- **FFmpeg Compose:** 3600s (60 minut) - zależy od rozmiaru plików
- **Audio Duration:** 60s - szybka operacja

### Normalizacja URL

Zawsze normalizuj URL przed wysłaniem do NCA Toolkit (usuń podwójne slashy):

```python
import re

def normalize_url(url: str) -> str:
    """Usuń podwójne slashy z URL (zachowując :// w protokole)."""
    return re.sub(r'([^:])\/\/+', r'\1/', url)
```

### Format Plików

**Obsługiwane formaty wideo:**
- MP4 (H.264, H.265)
- AVI
- MOV

**Obsługiwane formaty audio:**
- MP3
- WAV
- AAC
- M4A

**Obsługiwane formaty obrazów:**
- JPG/JPEG
- PNG
- WebP

### Storage

NCA Toolkit zapisuje wygenerowane pliki w MinIO storage:
- URL format: `https://minio2-api.aihub.ovh/nca-toolkit/videos/{filename}.mp4`
- Pliki są dostępne publicznie przez URL
- Pliki są trwałe (nie są automatycznie usuwane)

### Zoom Speed

- `0` - Brak zoom (statyczny obraz)
- `1-10` - Powolny zoom in
- `10-50` - Średni zoom in
- `50-100` - Szybki zoom in

Rekomendowane wartości: `3-5` dla naturalnego efektu.

---

## Dodatkowe Zasoby

### Endpointy NCA Toolkit

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/v1/image/transform/video` | POST | Konwersja obrazu na wideo |
| `/v1/video/concatenate` | POST | Łączenie klipów wideo |
| `/v1/ffmpeg/compose` | POST | Kompozycja wideo z audio |

### Endpointy Audio Duration

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/get-audio-duration` | POST | Pobieranie długości audio |

---

**Ostatnia aktualizacja:** 2025-11-21

