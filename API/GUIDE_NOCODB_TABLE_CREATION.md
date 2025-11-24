# NocoDB - Tworzenie Tabel z Automatycznym ID i Primary Key

## Przegląd

NocoDB automatycznie dodaje kolumnę `id` jako primary key do każdej nowej tabeli. Jednak przy programowym tworzeniu tabel przez API, musisz upewnić się, że kolumna ID jest poprawnie skonfigurowana.

## Automatyczne Dodawanie ID i Primary Key

### 1. Podstawowa Struktura Request

**Endpoint:**
```
POST /api/v1/db/meta/projects/{project_id}/tables
```

**Headers:**
```json
{
  "xc-token": "YOUR_API_TOKEN",
  "Content-Type": "application/json"
}
```

### 2. Format Request Body

```json
{
  "table_name": "nazwa_tabeli",
  "title": "Nazwa Tabeli",
  "type": "table",
  "description": "Opcjonalny opis",
  "columns": [
    {
      "column_name": "id",
      "title": "Id",
      "dt": "integer",
      "dtxp": null,
      "dtx": "autoNumber",
      "colOptions": {},
      "required": false,
      "unique": false,
      "pk": true
    },
    {
      "column_name": "nazwa_pola",
      "title": "Nazwa Pola",
      "dt": "varchar",
      "dtxp": "255",
      "dtx": "specificType",
      "colOptions": {},
      "required": false,
      "unique": false
    }
  ]
}
```

### 3. Kluczowe Parametry dla Kolumny ID

| Parametr | Wartość | Opis |
|----------|---------|------|
| `column_name` | `"id"` | Nazwa kolumny (musi być "id") |
| `title` | `"Id"` | Wyświetlana nazwa |
| `dt` | `"integer"` | Typ danych (integer) |
| `dtxp` | `null` | Opcje typu (null dla integer) |
| `dtx` | `"autoNumber"` | **KRYTYCZNE** - automatyczne numerowanie |
| `pk` | `true` | **KRYTYCZNE** - primary key |
| `required` | `false` | Nie wymagane (auto-increment) |
| `unique` | `false` | Unikalne (gwarantowane przez primary key) |

### 4. Przykład Python

```python
import httpx
import asyncio

async def create_table_with_auto_id():
    """Tworzy tabelę z automatycznym ID i primary key."""
    
    api_url = "http://192.168.0.4:30183"
    api_token = "YOUR_API_TOKEN"
    project_id = "YOUR_PROJECT_ID"
    
    url = f"{api_url}/api/v1/db/meta/projects/{project_id}/tables"
    headers = {
        "xc-token": api_token,
        "Content-Type": "application/json"
    }
    
    # Zawsze dodaj kolumnę ID jako pierwszą
    data = {
        "table_name": "moja_tabela",
        "title": "Moja Tabela",
        "type": "table",
        "description": "Przykładowa tabela z auto ID",
        "columns": [
            # KROK 1: Dodaj kolumnę ID jako pierwszą
            {
                "column_name": "id",
                "title": "Id",
                "dt": "integer",
                "dtxp": None,
                "dtx": "autoNumber",  # Automatyczne numerowanie
                "colOptions": {},
                "required": False,
                "unique": False,
                "pk": True  # Primary key
            },
            # KROK 2: Dodaj pozostałe kolumny
            {
                "column_name": "nazwa",
                "title": "Nazwa",
                "dt": "varchar",
                "dtxp": "255",
                "dtx": "specificType",
                "colOptions": {},
                "required": True,
                "unique": False
            },
            {
                "column_name": "opis",
                "title": "Opis",
                "dt": "text",
                "dtxp": None,
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        table_id = result.get("id")
        print(f"Tabela utworzona z ID: {table_id}")
        return result

# Uruchomienie
asyncio.run(create_table_with_auto_id())
```

### 5. Funkcja Helper (Automatyczne Dodawanie ID)

```python
def ensure_id_column(columns: list) -> list:
    """
    Zapewnia, że kolumna ID jest obecna jako pierwsza kolumna.
    
    Args:
        columns: Lista definicji kolumn
        
    Returns:
        Lista kolumn z ID jako pierwszą kolumną
    """
    # Sprawdź czy kolumna ID już istnieje
    has_id = any(
        col.get("column_name", "").lower() == "id" 
        or col.get("title", "").lower() == "id"
        for col in columns
    )
    
    # Jeśli nie ma, dodaj jako pierwszą kolumnę
    if not has_id:
        id_column = {
            "column_name": "id",
            "title": "Id",
            "dt": "integer",
            "dtxp": None,
            "dtx": "autoNumber",
            "colOptions": {},
            "required": False,
            "unique": False,
            "pk": True
        }
        columns.insert(0, id_column)
    
    return columns

# Użycie
columns = [
    {
        "column_name": "nazwa",
        "title": "Nazwa",
        "dt": "varchar",
        "dtxp": "255",
        "dtx": "specificType",
        "colOptions": {},
        "required": True,
        "unique": False
    }
]

# Automatycznie dodaj ID jeśli nie ma
columns = ensure_id_column(columns)
```

### 6. Mapowanie Typów Danych

| Typ NocoDB | `dt` | `dtxp` | `dtx` | Użycie |
|------------|------|--------|-------|--------|
| AutoNumber (ID) | `"integer"` | `null` | `"autoNumber"` | Primary key |
| SingleLineText | `"varchar"` | `"255"` | `"specificType"` | Tekst krótki |
| LongText | `"text"` | `null` | `"specificType"` | Tekst długi |
| Number | `"int"` | `null` | `"specificType"` | Liczba całkowita |
| Decimal | `"decimal"` | `"10,2"` | `"specificType"` | Liczba dziesiętna |
| Date | `"date"` | `null` | `"specificType"` | Data |
| DateTime | `"datetime"` | `null` | `"specificType"` | Data i czas |
| Boolean | `"boolean"` | `null` | `"specificType"` | Prawda/Fałsz |
| JSON | `"json"` | `null` | `"specificType"` | Dane JSON |
| URL | `"varchar"` | `"255"` | `"specificType"` | Adres URL |

### 7. Pełny Przykład z Wszystkimi Typami

```python
async def create_complete_table():
    """Tworzy tabelę z różnymi typami kolumn."""
    
    api_url = "http://192.168.0.4:30183"
    api_token = "YOUR_API_TOKEN"
    project_id = "YOUR_PROJECT_ID"
    
    url = f"{api_url}/api/v1/db/meta/projects/{project_id}/tables"
    headers = {
        "xc-token": api_token,
        "Content-Type": "application/json"
    }
    
    data = {
        "table_name": "kompletna_tabela",
        "title": "Kompletna Tabela",
        "type": "table",
        "columns": [
            # ID - ZAWSZE PIERWSZA
            {
                "column_name": "id",
                "title": "Id",
                "dt": "integer",
                "dtxp": None,
                "dtx": "autoNumber",
                "colOptions": {},
                "required": False,
                "unique": False,
                "pk": True
            },
            # SingleLineText
            {
                "column_name": "tytul",
                "title": "Tytuł",
                "dt": "varchar",
                "dtxp": "255",
                "dtx": "specificType",
                "colOptions": {},
                "required": True,
                "unique": False
            },
            # LongText
            {
                "column_name": "opis",
                "title": "Opis",
                "dt": "text",
                "dtxp": None,
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            },
            # Number
            {
                "column_name": "liczba",
                "title": "Liczba",
                "dt": "int",
                "dtxp": None,
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            },
            # Decimal
            {
                "column_name": "cena",
                "title": "Cena",
                "dt": "decimal",
                "dtxp": "10,2",
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            },
            # Date
            {
                "column_name": "data_utworzenia",
                "title": "Data Utworzenia",
                "dt": "date",
                "dtxp": None,
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            },
            # DateTime
            {
                "column_name": "data_modyfikacji",
                "title": "Data Modyfikacji",
                "dt": "datetime",
                "dtxp": None,
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            },
            # Boolean
            {
                "column_name": "aktywny",
                "title": "Aktywny",
                "dt": "boolean",
                "dtxp": None,
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            },
            # JSON
            {
                "column_name": "dane_json",
                "title": "Dane JSON",
                "dt": "json",
                "dtxp": None,
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            },
            # URL
            {
                "column_name": "url",
                "title": "URL",
                "dt": "varchar",
                "dtxp": "255",
                "dtx": "specificType",
                "colOptions": {},
                "required": False,
                "unique": False
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
```

## Ważne Zasady

### ✅ DOBRE PRAKTYKI

1. **Zawsze dodawaj kolumnę ID jako pierwszą** - NocoDB oczekuje, że ID będzie pierwszą kolumną
2. **Używaj `dtx: "autoNumber"`** - To zapewnia automatyczne numerowanie
3. **Ustaw `pk: true`** - To oznacza kolumnę jako primary key
4. **Nie ustawiaj `required: true`** - Auto-increment nie wymaga podania wartości
5. **Nie ustawiaj `unique: true`** - Primary key automatycznie zapewnia unikalność

### ❌ CZEGO UNIKAĆ

1. **Nie pomijaj kolumny ID** - Każda tabela musi mieć ID
2. **Nie używaj innej nazwy niż "id"** - NocoDB oczekuje dokładnie "id"
3. **Nie ustawiaj `dtx` na coś innego niż "autoNumber"** - To wyłączy auto-increment
4. **Nie dodawaj ID w środku listy kolumn** - Zawsze jako pierwsza

## Weryfikacja

Po utworzeniu tabeli, sprawdź czy ID działa:

```python
async def verify_table_id():
    """Weryfikuje czy tabela ma poprawnie skonfigurowane ID."""
    
    api_url = "http://192.168.0.4:30183"
    api_token = "YOUR_API_TOKEN"
    project_id = "YOUR_PROJECT_ID"
    table_id = "YOUR_TABLE_ID"
    
    # Pobierz metadane tabeli
    url = f"{api_url}/api/v1/db/meta/tables/{table_id}/columns"
    headers = {
        "xc-token": api_token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        columns = response.json()
        
        # Znajdź kolumnę ID
        id_column = next(
            (col for col in columns if col.get("column_name", "").lower() == "id"),
            None
        )
        
        if id_column:
            print(f"ID Column found:")
            print(f"  - column_name: {id_column.get('column_name')}")
            print(f"  - dtx: {id_column.get('dtx')}")
            print(f"  - pk: {id_column.get('pk')}")
            
            if id_column.get("dtx") == "autoNumber" and id_column.get("pk"):
                print("✅ ID column is correctly configured as autoNumber primary key")
            else:
                print("❌ ID column is NOT correctly configured")
        else:
            print("❌ ID column not found!")
```

## Podsumowanie

**Minimalny przykład tworzenia tabeli z auto ID:**

```python
data = {
    "table_name": "moja_tabela",
    "title": "Moja Tabela",
    "type": "table",
    "columns": [
        {
            "column_name": "id",
            "title": "Id",
            "dt": "integer",
            "dtxp": None,
            "dtx": "autoNumber",  # ← KLUCZOWE
            "colOptions": {},
            "required": False,
            "unique": False,
            "pk": True  # ← KLUCZOWE
        },
        # ... pozostałe kolumny
    ]
}
```

**Kluczowe parametry:**
- `"dtx": "autoNumber"` - automatyczne numerowanie
- `"pk": true` - primary key
- Kolumna ID musi być **pierwsza** w liście


