"""
FAZA 1: Test Initialize Project
Cel: Sprawdzić czy inicjalizacja projektu działa poprawnie
"""
from models import Project
from modules.pipeline_manager import PipelineManager
from utils.logger import logger
from config import settings

def test_phase_1_initialize_project():
    print("="*70)
    print("FAZA 1: INITIALIZE PROJECT")
    print("="*70)
    
    # 1. Utwórz projekt
    print("\n[1/4] Tworzenie obiektu Project...")
    project = Project(
        topic="Test Phase 1 - Initialize",
        status="Testing",
        target_duration=3,
        voice_id="am_michael"
    )
    print(f"✓ Utworzono: {project.topic}")
    
    # 2. Zainicjalizuj przez PipelineManager
    print("\n[2/4] Inicjalizacja przez PipelineManager...")
    pipeline = PipelineManager()
    
    try:
        result = pipeline.initialize_project(project)
        
        if result and result.id:
            print(f"✓ Sukces! Project ID: {result.id}")
            project_id = result.id
        else:
            print("❌ FAIL: Nie otrzymano ID projektu")
            return None
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        logger.exception("Błąd inicjalizacji projektu")
        return None
    
    # 3. Weryfikacja przez GET API
    print("\n[3/4] Weryfikacja przez GET API...")
    import requests
    
    api_url = settings.NOCODB_API_URL
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    try:
        resp = requests.get(
            f"{api_url}/api/v2/tables/{table_id}/records/{project_id}",
            headers=headers
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Rekord istnieje w NocoDB")
            print(f"  Topic: {data.get('Topic')}")
            print(f"  Status: {data.get('Status')}")
            print(f"  CreatedAt: {data.get('CreatedAt')}")
        else:
            print(f"❌ FAIL: Nie można pobrać rekordu ({resp.status_code})")
            return None
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return None
    
    # 4. Weryfikacja przez MCP
    print("\n[4/4] Weryfikacja przez MCP...")
    print(f"  Rekord ID: {project_id}")
    print(f"  Tabela: {table_id}")
    print(f"  → Możesz zweryfikować przez mcp0_getRecord")
    
    # Podsumowanie
    print(f"\n{'='*70}")
    print("PODSUMOWANIE FAZY 1")
    print(f"{'='*70}")
    print(f"✅ Utworzono projekt: {project.topic}")
    print(f"✅ Przypisano ID: {project_id}")
    print(f"✅ Zweryfikowano w NocoDB")
    print(f"\n🎯 FAZA 1: SUCCESS")
    
    return {
        "project_id": project_id,
        "project": result
    }

if __name__ == "__main__":
    result = test_phase_1_initialize_project()
    
    if result:
        print(f"\n✅ Test zakończony sukcesem")
        print(f"   Project ID do użycia w następnych fazach: {result['project_id']}")
    else:
        print(f"\n❌ Test zakończony niepowodzeniem")
