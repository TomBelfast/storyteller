"""
FAZA 2: Test Research Engine
Cel: Sprawdzić czy Perplexity research działa i zapisuje do NocoDB
"""
from modules.research_engine import ResearchEngine
from utils.logger import logger
from config import settings
import requests

def test_phase_2_research(project_id=2):
    print("="*70)
    print("FAZA 2: RESEARCH ENGINE (Perplexity)")
    print("="*70)
    
    # 1. Inicjalizuj Research Engine
    print("\n[1/5] Inicjalizacja Research Engine...")
    research_engine = ResearchEngine()
    print("✓ Research Engine gotowy")
    
    # 2. Wykonaj research na testowym temacie
    print("\n[2/5] Wykonywanie researchu przez Perplexity API...")
    topic = "Artificial Intelligence in Healthcare"
    
    try:
        research_result = research_engine.run_research(topic)
        
        if research_result and isinstance(research_result, dict):
            research_data = research_result.get("content", "")
            research_sources = research_result.get("sources", "")
            
            print(f"✓ Otrzymano research data")
            print(f"  Długość: {len(research_data)} znaków")
            print(f"  Podgląd: {research_data[:200]}...")
            print(f"  Źródła: {len(research_sources)} znaków")
        else:
            print("❌ FAIL: Brak research data lub zły format")
            return None
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        logger.exception("Błąd research")
        return None
    
    # 3. Zaktualizuj projekt w NocoDB
    print("\n[3/5] Aktualizacja projektu w NocoDB...")
    
    api_url = settings.NOCODB_API_URL
    table_id = settings.NOCODB_PROJECTS_TABLE_ID
    headers = {"xc-token": settings.NOCODB_API_TOKEN}
    
    records_url = f"{api_url}/api/v2/tables/{table_id}/records"
    
    # PATCH request
    payload = [{
        "Id": project_id,
        settings.NOCODB_FIELDS["project"]["research_content"]: research_data,
        settings.NOCODB_FIELDS["project"]["research_sources"]: research_sources
    }]
    
    try:
        resp = requests.patch(records_url, json=payload, headers=headers)
        
        if resp.status_code == 200:
            print(f"✓ PATCH sukces: {resp.status_code}")
        else:
            print(f"❌ FAIL: PATCH {resp.status_code}")
            print(f"   Response: {resp.text}")
            return None
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return None
    
    # 4. Weryfikacja przez GET
    print("\n[4/5] Weryfikacja przez GET API...")
    
    try:
        resp = requests.get(f"{records_url}/{project_id}", headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            saved_research = data.get("Research Data")
            
            if saved_research and len(saved_research) > 0:
                print(f"✓ Research Data zapisany")
                print(f"  Długość: {len(saved_research)} znaków")
                print(f"  Sources: {data.get('Script Content')[:100]}...")
            else:
                print(f"❌ FAIL: Research Data nie został zapisany")
                return None
        else:
            print(f"❌ FAIL: GET {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return None
    
    # 5. Weryfikacja przez MCP
    print("\n[5/5] Weryfikacja przez MCP...")
    print(f"  Rekord ID: {project_id}")
    print(f"  → Możesz zweryfikować przez mcp0_getRecord")
    
    # Podsumowanie
    print(f"\n{'='*70}")
    print("PODSUMOWANIE FAZY 2")
    print(f"{'='*70}")
    print(f"✅ Research wykonany: {len(research_data)} znaków")
    print(f"✅ Zapisano do NocoDB (ID: {project_id})")
    print(f"✅ Zweryfikowano przez GET")
    print(f"\n🎯 FAZA 2: SUCCESS")
    
    return {
        "project_id": project_id,
        "research_data": research_data
    }

if __name__ == "__main__":
    result = test_phase_2_research()
    
    if result:
        print(f"\n✅ Test zakończony sukcesem")
    else:
        print(f"\n❌ Test zakończony niepowodzeniem")
