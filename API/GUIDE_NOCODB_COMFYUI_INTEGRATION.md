# Przewodnik Integracji: NocoDB i ComfyUI

## Spis Treści

1. [NocoDB - Podstawowe Połączenie](#nocodb---podstawowe-połączenie)
2. [NocoDB - API Endpoints](#nocodb---api-endpoints)
3. [NocoDB - Przykłady Użycia](#nocodb---przykłady-użycia)
4. [ComfyUI - Podstawowe Połączenie](#comfyui---podstawowe-połączenie)
5. [ComfyUI - API Endpoints](#comfyui---api-endpoints)
6. [ComfyUI - Workflow z Modelami i LoRA](#comfyui---workflow-z-modelami-i-lora)
7. [Przykłady Kompletne](#przykłady-kompletne)

---

## NocoDB - Podstawowe Połączenie

### Konfiguracja

**Wymagane dane:**
- `NOCODB_API_URL` - Adres API NocoDB (np. `http://192.168.0.4:30183`)
- `NOCODB_API_TOKEN` - Token autentykacji (np. `nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw`)
- `NOCODB_PROJECT_ID` - ID projektu w NocoDB (np. `pmcr6sel7s7gjwj`)

**Przykład konfiguracji:**
```python
NOCODB_API_URL = "http://192.168.0.4:30183"
NOCODB_API_TOKEN = "nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw"
NOCODB_PROJECT_ID = "pmcr6sel7s7gjwj"
```

### Autentykacja

NocoDB używa token-based authentication przez header `xc-token`:

```python
headers = {
    "xc-token": NOCODB_API_TOKEN,
    "Content-Type": "application/json"
}
```

### Podstawowa Struktura Klienta

```python
import httpx
from typing import Dict, Any, Optional, List

class NocoDBClient:
    def __init__(self, api_url: str, api_token: str, project_id: str):
        self.base_url = api_url.rstrip("/")
        self.project_id = project_id
        self.headers = {
            "xc-token": api_token,
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Wykonaj request HTTP do NocoDB API."""
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=self.headers, json=data)
            elif method.upper() == "PATCH":
                response = await client.patch(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
```

---

## NocoDB - API Endpoints

### 1. Pobranie ID Tabeli

**Endpoint:**
```
GET /api/v1/db/meta/projects/{project_id}/tables
```

**Przykład:**
```python
async def get_table_id(self, table_name: str) -> Optional[str]:
    """Pobierz ID tabeli po nazwie."""
    url = f"{self.base_url}/api/v1/db/meta/projects/{self.project_id}/tables"
    response = await self._make_request("GET", url)
    
    for table in response:
        if table.get("title", "").lower() == table_name.lower():
            return table.get("id")
    return None
```

### 2. Pobranie Rekordu

**Endpoint:**
```
GET /api/v1/db/data/noco/{project_id}/{table_id}/{row_id}?user_field_names=true
```

**Przykład:**
```python
async def get_row(self, table_name: str, row_id: str) -> Dict[str, Any]:
    """Pobierz pojedynczy rekord."""
    table_id = await self.get_table_id(table_name)
    if not table_id:
        raise ValueError(f"Table '{table_name}' not found")
    
    url = f"{self.base_url}/api/v1/db/data/noco/{self.project_id}/{table_id}/{row_id}?user_field_names=true"
    return await self._make_request("GET", url)
```

### 3. Pobranie Wszystkich Rekordów

**Endpoint:**
```
GET /api/v1/db/data/noco/{project_id}/{table_id}?user_field_names=true&limit=25&offset=0
```

**Przykład:**
```python
async def get_rows(
    self,
    table_name: str,
    limit: int = 25,
    offset: int = 0,
    where: Optional[str] = None
) -> Dict[str, Any]:
    """Pobierz wiele rekordów."""
    table_id = await self.get_table_id(table_name)
    if not table_id:
        raise ValueError(f"Table '{table_name}' not found")
    
    url = f"{self.base_url}/api/v1/db/data/noco/{self.project_id}/{table_id}?user_field_names=true&limit={limit}&offset={offset}"
    
    if where:
        url += f"&where={where}"
    
    return await self._make_request("GET", url)
```

### 4. Utworzenie Rekordu

**Endpoint:**
```
POST /api/v1/db/data/noco/{project_id}/{table_id}?user_field_names=true
```

**Przykład:**
```python
async def create_row(self, table_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Utwórz nowy rekord."""
    table_id = await self.get_table_id(table_name)
    if not table_id:
        raise ValueError(f"Table '{table_name}' not found")
    
    url = f"{self.base_url}/api/v1/db/data/noco/{self.project_id}/{table_id}?user_field_names=true"
    return await self._make_request("POST", url, data=fields)
```

**Uwaga:** Jeśli tabela ma pole `Id` które jest required, musisz wygenerować ID ręcznie:
```python
# Pobierz maksymalne ID
rows = await client.get_rows(table_name, limit=1000)
max_id = max([int(r.get("Id", 0)) for r in rows.get("list", [])], default=0)
new_id = max_id + 1

# Dodaj ID do fields
fields["Id"] = new_id
await client.create_row(table_name, fields)
```

### 5. Aktualizacja Rekordu

**Endpoint:**
```
PATCH /api/v1/db/data/noco/{project_id}/{table_id}/{row_id}?user_field_names=true
```

**Przykład:**
```python
async def update_row(
    self,
    table_name: str,
    row_id: str,
    fields: Dict[str, Any]
) -> Dict[str, Any]:
    """Aktualizuj istniejący rekord."""
    table_id = await self.get_table_id(table_name)
    if not table_id:
        raise ValueError(f"Table '{table_name}' not found")
    
    url = f"{self.base_url}/api/v1/db/data/noco/{self.project_id}/{table_id}/{row_id}?user_field_names=true"
    return await self._make_request("PATCH", url, data=fields)
```

### 6. Usunięcie Rekordu

**Endpoint:**
```
DELETE /api/v1/db/data/noco/{project_id}/{table_id}/{row_id}
```

**Przykład:**
```python
async def delete_row(self, table_name: str, row_id: str) -> bool:
    """Usuń rekord."""
    table_id = await self.get_table_id(table_name)
    if not table_id:
        raise ValueError(f"Table '{table_name}' not found")
    
    url = f"{self.base_url}/api/v1/db/data/noco/{self.project_id}/{table_id}/{row_id}"
    await self._make_request("DELETE", url)
    return True
```

### 7. Upload Pliku

**Endpointy (próbuj w kolejności):**
1. `POST /api/v2/storage/upload`
2. `POST /api/v1/db/storage/upload`
3. `POST /api/v1/db/storage/upload/multi`

**Przykład:**
```python
import os
from pathlib import Path

async def upload_file(
    self,
    file_path: str,
    file_name: Optional[str] = None
) -> Dict[str, Any]:
    """Upload pliku do NocoDB."""
    if not file_name:
        file_name = os.path.basename(file_path)
    
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Próbuj różne endpointy
    endpoints = [
        f"{self.base_url}/api/v2/storage/upload",
        f"{self.base_url}/api/v1/db/storage/upload",
        f"{self.base_url}/api/v1/db/storage/upload/multi"
    ]
    
    with open(file_path, "rb") as f:
        files = {"file": (file_name, f, "application/octet-stream")}
        headers = {"xc-token": self.headers["xc-token"]}
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                try:
                    response = await client.post(
                        endpoint,
                        files=files,
                        headers=headers,
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        return response.json()
                except Exception as e:
                    continue
            
            # Fallback: zwróć informacje o pliku (możesz zapisać lokalnie)
            file_size = file_path_obj.stat().st_size
            return {
                "name": file_name,
                "url": f"http://your-server/storage/{file_name}",
                "mimetype": "application/octet-stream",
                "size": file_size
            }
```

---

## NocoDB - Przykłady Użycia

### Podstawowe CRUD

```python
import asyncio
from nocodb_client import NocoDBClient

async def main():
    # Inicjalizacja klienta
    client = NocoDBClient(
        api_url="http://192.168.0.4:30183",
        api_token="nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw",
        project_id="pmcr6sel7s7gjwj"
    )
    
    # Pobierz rekord
    project = await client.get_row("video", "1")
    print(f"Title: {project.get('Title')}")
    
    # Utwórz rekord
    new_record = await client.create_row("video", {
        "Title": "New Project",
        "Description": "Test project",
        "Status": "Active"
    })
    print(f"Created: {new_record.get('Id')}")
    
    # Aktualizuj rekord
    await client.update_row("video", "1", {
        "Status": "Complete"
    })
    
    # Pobierz wiele rekordów
    all_projects = await client.get_rows("video", limit=100)
    print(f"Total projects: {len(all_projects.get('list', []))}")
    
    # Filtrowanie (where syntax)
    active_projects = await client.get_rows(
        "video",
        where="(Status,eq,Active)"
    )
    print(f"Active projects: {len(active_projects.get('list', []))}")

asyncio.run(main())
```

### Attachment Field (Pliki)

```python
# Upload pliku
file_info = await client.upload_file(
    file_path="/path/to/image.png",
    file_name="image_123.png"
)

# Zapisz do Attachment field
attachment_data = [{
    "title": file_info["name"],
    "url": file_info["url"],
    "mimetype": "image/png",
    "size": file_info["size"]
}]

import json
await client.update_row("scenes", "123", {
    "Image": json.dumps(attachment_data)
})
```

---

## ComfyUI - Podstawowe Połączenie

### Konfiguracja

**Wymagane dane:**
- `COMFYUI_API_URL` - Adres API ComfyUI (np. `http://192.168.0.14:8188`)

**Przykład konfiguracji:**
```python
COMFYUI_API_URL = "http://192.168.0.14:8188"
```

### Autentykacja

ComfyUI nie wymaga autentykacji (domyślnie), ale można skonfigurować API key w ustawieniach.

### Podstawowa Struktura Klienta

```python
import httpx
import json
from typing import Dict, Any, Optional

class ComfyUIClient:
    def __init__(self, api_url: str):
        self.base_url = api_url.rstrip("/")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Wykonaj request HTTP do ComfyUI API."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
```

---

## ComfyUI - API Endpoints

### 1. Wysłanie Promptu (Generacja Obrazu)

**Endpoint:**
```
POST /prompt
```

**Request Body:**
```json
{
  "prompt": {
    "1": {
      "inputs": {
        "text": "positive prompt",
        "clip": ["4", 0]
      },
      "class_type": "CLIPTextEncode"
    },
    "4": {
      "inputs": {
        "ckpt_name": "model.safetensors"
      },
      "class_type": "CheckpointLoaderSimple"
    }
  },
  "client_id": "unique_client_id"
}
```

**Przykład:**
```python
async def generate_image(self, workflow: Dict[str, Any], client_id: str) -> str:
    """Wyślij workflow do ComfyUI i zwróć prompt_id."""
    response = await self._make_request(
        "POST",
        "/prompt",
        data={"prompt": workflow, "client_id": client_id}
    )
    return response.get("prompt_id")
```

### 2. Sprawdzenie Statusu

**Endpoint:**
```
GET /history/{prompt_id}
```

**Przykład:**
```python
async def check_status(self, prompt_id: str) -> Dict[str, Any]:
    """Sprawdź status generacji."""
    response = await self._make_request("GET", f"/history/{prompt_id}")
    return response
```

### 3. Pobranie Obrazu

**Endpoint:**
```
GET /view?filename={filename}
```

**Przykład:**
```python
async def get_image_url(self, filename: str) -> str:
    """Zwróć URL do wygenerowanego obrazu."""
    return f"{self.base_url}/view?filename={filename}"
```

### 4. Pobranie Listy Modeli

**Endpoint:**
```
GET /object_info
```

**Przykład:**
```python
async def get_models(self) -> Dict[str, Any]:
    """Pobierz listę dostępnych modeli."""
    response = await self._make_request("GET", "/object_info")
    return response.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [])
```

---

## ComfyUI - Workflow z Modelami i LoRA

### Struktura Workflow

Workflow ComfyUI to JSON z węzłami (nodes), gdzie każdy węzeł ma:
- `inputs` - dane wejściowe
- `class_type` - typ węzła
- `_meta` - metadane (opcjonalne)

### Flux Dev - Podstawowy Workflow

```python
def build_flux_dev_workflow(
    positive_prompt: str,
    negative_prompt: str,
    model_name: str = "flux1-dev-fp8.safetensors",
    width: int = 1024,
    height: int = 1024,
    seed: int = 12345,
    steps: int = 28,
    cfg: float = 3.5
) -> Dict[str, Any]:
    """Buduj workflow dla Flux Dev."""
    return {
        "1": {
            "inputs": {
                "text": positive_prompt,
                "clip": ["4", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "2": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["4", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        },
        "4": {
            "inputs": {
                "ckpt_name": model_name
            },
            "class_type": "CheckpointLoaderSimple",
            "_meta": {"title": "Load Checkpoint"}
        },
        "5": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptySD3LatentImage",
            "_meta": {"title": "Empty Latent Image"}
        },
        "6": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["1", 0],
                "negative": ["2", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        "7": {
            "inputs": {
                "samples": ["6", 0],
                "vae": ["4", 1]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "8": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["7", 0]
            },
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        }
    }
```

### Flux Dev z LoRA

```python
def build_flux_dev_lora_workflow(
    positive_prompt: str,
    negative_prompt: str,
    model_name: str = "flux1-dev-fp8.safetensors",
    lora_1_name: str = "flux_turbo.safetensors",
    lora_1_strength: float = 0.8,
    lora_2_name: Optional[str] = None,
    lora_2_strength: float = 0.8,
    width: int = 1024,
    height: int = 1024,
    seed: int = 12345,
    steps: int = 28,
    cfg: float = 3.5
) -> Dict[str, Any]:
    """Buduj workflow dla Flux Dev z LoRA."""
    workflow = {
        "1": {
            "inputs": {
                "text": positive_prompt,
                "clip": ["10", 1]  # Połącz z output LoRA
            },
            "class_type": "CLIPTextEncode"
        },
        "2": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["10", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "ckpt_name": model_name
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "6": {
            "inputs": {
                "lora_name": lora_1_name,
                "strength_model": lora_1_strength,
                "strength_clip": lora_1_strength,
                "model": ["4", 0],
                "clip": ["4", 1]
            },
            "class_type": "LoraLoader"
        },
        "10": {
            "inputs": {
                "lora_name": lora_2_name if lora_2_name else lora_1_name,
                "strength_model": lora_2_strength,
                "strength_clip": lora_2_strength,
                "model": ["6", 0],
                "clip": ["6", 1]
            },
            "class_type": "LoraLoader"
        },
        "5": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptySD3LatentImage"
        },
        "9": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1,
                "model": ["10", 0],
                "positive": ["1", 0],
                "negative": ["2", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "7": {
            "inputs": {
                "samples": ["9", 0],
                "vae": ["10", 2]
            },
            "class_type": "VAEDecode"
        },
        "8": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["7", 0]
            },
            "class_type": "SaveImage"
        }
    }
    
    # Jeśli tylko jedna LoRA, usuń drugą
    if not lora_2_name:
        workflow["10"]["inputs"]["model"] = ["6", 0]
        workflow["10"]["inputs"]["clip"] = ["6", 1]
        workflow["1"]["inputs"]["clip"] = ["6", 1]
        workflow["2"]["inputs"]["clip"] = ["6", 1]
        workflow["9"]["inputs"]["model"] = ["6", 0]
        workflow["7"]["inputs"]["vae"] = ["6", 2]
    
    return workflow
```

### SDXL - Podstawowy Workflow

```python
def build_sdxl_workflow(
    positive_prompt: str,
    negative_prompt: str,
    model_name: str = "sd_xl_base_1.0.safetensors",
    width: int = 1024,
    height: int = 1024,
    seed: int = 12345,
    steps: int = 30,
    cfg: float = 7.0
) -> Dict[str, Any]:
    """Buduj workflow dla SDXL."""
    return {
        "1": {
            "inputs": {
                "text": positive_prompt,
                "clip": ["4", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "2": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["4", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "ckpt_name": model_name
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "5": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["1", 0],
                "negative": ["2", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "7": {
            "inputs": {
                "samples": ["6", 0],
                "vae": ["4", 1]
            },
            "class_type": "VAEDecode"
        },
        "8": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["7", 0]
            },
            "class_type": "SaveImage"
        }
    }
```

### SDXL z LoRA

```python
def build_sdxl_lora_workflow(
    positive_prompt: str,
    negative_prompt: str,
    model_name: str = "sd_xl_base_1.0.safetensors",
    lora_name: str = "style_lora.safetensors",
    lora_strength_model: float = 0.8,
    lora_strength_clip: float = 0.8,
    width: int = 1024,
    height: int = 1024,
    seed: int = 12345,
    steps: int = 30,
    cfg: float = 7.0
) -> Dict[str, Any]:
    """Buduj workflow dla SDXL z LoRA."""
    return {
        "1": {
            "inputs": {
                "text": positive_prompt,
                "clip": ["2", 1]  # Połącz z output LoRA
            },
            "class_type": "CLIPTextEncode"
        },
        "3": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["2", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "ckpt_name": model_name
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "lora_name": lora_name,
                "strength_model": lora_strength_model,
                "strength_clip": lora_strength_clip,
                "model": ["4", 0],
                "clip": ["4", 1]
            },
            "class_type": "LoraLoader"
        },
        "5": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": ["2", 0],
                "positive": ["1", 0],
                "negative": ["3", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "7": {
            "inputs": {
                "samples": ["6", 0],
                "vae": ["2", 2]
            },
            "class_type": "VAEDecode"
        },
        "8": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["7", 0]
            },
            "class_type": "SaveImage"
        }
    }
```

### Flux Krea - Podstawowy Workflow

```python
def build_flux_krea_workflow(
    positive_prompt: str,
    negative_prompt: str,
    model_name: str = "flux1-krea-fp8.safetensors",
    width: int = 1024,
    height: int = 1024,
    seed: int = 12345,
    steps: int = 20,
    cfg: float = 3.5
) -> Dict[str, Any]:
    """Buduj workflow dla Flux Krea (podobny do Flux Dev)."""
    return build_flux_dev_workflow(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        model_name=model_name,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
        cfg=cfg
    )
```

---

## Przykłady Kompletne

### Przykład 1: Generacja Obrazu z ComfyUI i Zapis do NocoDB

```python
import asyncio
import json
import random
from nocodb_client import NocoDBClient
from comfyui_client import ComfyUIClient
from workflows import build_flux_dev_workflow

async def generate_and_save_image():
    # Inicjalizacja klientów
    nocodb = NocoDBClient(
        api_url="http://192.168.0.4:30183",
        api_token="nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw",
        project_id="pmcr6sel7s7gjwj"
    )
    
    comfyui = ComfyUIClient(api_url="http://192.168.0.14:8188")
    
    # Buduj workflow
    workflow = build_flux_dev_workflow(
        positive_prompt="A beautiful landscape in Rembrandt style",
        negative_prompt="modern, digital, blurry",
        model_name="flux1-dev-fp8.safetensors",
        seed=random.randint(0, 2**53 - 1),
        steps=28,
        cfg=3.5
    )
    
    # Wyślij do ComfyUI
    client_id = f"my_app_{random.randint(1000, 9999)}"
    prompt_id = await comfyui.generate_image(workflow, client_id)
    print(f"Generation started: {prompt_id}")
    
    # Czekaj na zakończenie (polling)
    import time
    max_wait = 300  # 5 minut
    waited = 0
    while waited < max_wait:
        status = await comfyui.check_status(prompt_id)
        
        # Sprawdź czy zakończone
        if prompt_id in status:
            history = status[prompt_id]
            if history and len(history) > 0:
                outputs = history[0].get("outputs", {})
                if outputs:
                    # Znajdź SaveImage node
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            images = node_output["images"]
                            if images and len(images) > 0:
                                filename = images[0].get("filename")
                                subfolder = images[0].get("subfolder", "")
                                
                                # Pobierz URL obrazu
                                image_url = await comfyui.get_image_url(filename)
                                
                                # Zapisz do NocoDB
                                file_info = {
                                    "title": filename,
                                    "url": image_url,
                                    "mimetype": "image/png",
                                    "size": 0  # Możesz pobrać rozmiar z pliku
                                }
                                
                                await nocodb.update_row("scenes", "123", {
                                    "Image": json.dumps([file_info]),
                                    "Status": "Image Generated"
                                })
                                
                                print(f"Image saved: {image_url}")
                                return
        
        await asyncio.sleep(10)  # Czekaj 10 sekund
        waited += 10
    
    print("Generation timeout")

asyncio.run(generate_and_save_image())
```

### Przykład 2: Batch Generacja z LoRA

```python
async def batch_generate_with_lora():
    comfyui = ComfyUIClient(api_url="http://192.168.0.14:8188")
    
    prompts = [
        "A dramatic scene in Caravaggio style",
        "A peaceful landscape in Monet style",
        "An abstract composition in Kandinsky style"
    ]
    
    lora_name = "art_style_lora.safetensors"
    
    for i, prompt in enumerate(prompts):
        workflow = build_flux_dev_lora_workflow(
            positive_prompt=prompt,
            negative_prompt="modern, digital, blurry",
            lora_1_name="flux_turbo.safetensors",
            lora_1_strength=0.8,
            lora_2_name=lora_name,
            lora_2_strength=0.7,
            seed=random.randint(0, 2**53 - 1)
        )
        
        client_id = f"batch_{i}_{random.randint(1000, 9999)}"
        prompt_id = await comfyui.generate_image(workflow, client_id)
        print(f"Image {i+1} started: {prompt_id}")
        
        # Możesz dodać delay między requestami
        await asyncio.sleep(5)

asyncio.run(batch_generate_with_lora())
```

### Przykład 3: Pobranie i Aktualizacja Danych z NocoDB

```python
async def update_scene_with_image():
    nocodb = NocoDBClient(
        api_url="http://192.168.0.4:30183",
        api_token="nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw",
        project_id="pmcr6sel7s7gjwj"
    )
    
    # Pobierz scenę
    scene = await nocodb.get_row("scenes", "123")
    master_prompt = scene.get("Master Prompt")
    
    if not master_prompt:
        print("No prompt found")
        return
    
    # Generuj obraz
    comfyui = ComfyUIClient(api_url="http://192.168.0.14:8188")
    workflow = build_flux_dev_workflow(
        positive_prompt=master_prompt,
        negative_prompt="modern, digital, blurry"
    )
    
    prompt_id = await comfyui.generate_image(workflow, "scene_123")
    
    # Czekaj i zapisz (uproszczone - bez pełnego polling)
    await asyncio.sleep(60)  # Czekaj 60 sekund
    
    # Pobierz wynik (w rzeczywistości użyj polling)
    status = await comfyui.check_status(prompt_id)
    # ... (parsuj status i zapisz)
    
    # Aktualizuj scenę
    await nocodb.update_row("scenes", "123", {
        "Status": "Image Generated",
        "Image Provider": "Flux Dev"
    })

asyncio.run(update_scene_with_image())
```

---

## Konfiguracja Środowiska

### Zmienne Środowiskowe

```env
# NocoDB
NOCODB_API_URL=http://192.168.0.4:30183
NOCODB_API_TOKEN=nQfd0FHaDIa3IoBcg4yRExAkCDzIQ388U9WRO3iw
NOCODB_PROJECT_ID=pmcr6sel7s7gjwj

# ComfyUI
COMFYUI_API_URL=http://192.168.0.14:8188
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

### NocoDB

**Problem: 401 Unauthorized**
- Sprawdź czy token jest poprawny
- Sprawdź czy header `xc-token` jest ustawiony

**Problem: 404 Table not found**
- Sprawdź czy nazwa tabeli jest poprawna (case-sensitive)
- Sprawdź czy `project_id` jest poprawny
- Użyj `get_table_id()` aby znaleźć ID tabeli

**Problem: Field not found**
- Upewnij się że używasz `user_field_names=true` w URL
- Sprawdź czy nazwa pola jest poprawna (case-sensitive)

### ComfyUI

**Problem: Connection refused**
- Sprawdź czy ComfyUI działa: `curl http://192.168.0.14:8188/`
- Sprawdź firewall/network settings

**Problem: Invalid workflow**
- Sprawdź czy model istnieje w ComfyUI
- Sprawdź czy LoRA istnieje (jeśli używane)
- Sprawdź logi ComfyUI dla szczegółów błędu

**Problem: Generation timeout**
- Zwiększ timeout w `httpx.AsyncClient`
- Sprawdź czy model jest załadowany
- Sprawdź logi ComfyUI

---

## Dodatkowe Zasoby

### NocoDB
- API Documentation: https://docs.nocodb.com/
- REST API: https://docs.nocodb.com/developer-resources/rest-apis

### ComfyUI
- GitHub: https://github.com/comfyanonymous/ComfyUI
- API Examples: https://github.com/comfyanonymous/ComfyUI/wiki/API

---

**Ostatnia aktualizacja:** 2025-11-21

