#!/usr/bin/env python3
"""
🔥 SUBPROCESS TEST - Gelişmiş execute_local_python test et
"""

from core_agent_react import ReactAgent

def subprocess_test():
    print("🔥 SUBPROCESS TEST BAŞLADI")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Karmaşık kod testi
    task = """Aşağıdaki işlemleri yap:
1. Scratchpad'den dosya listesini al
2. Python dosyalarını filtrele 
3. workspace/test_sonuc.md dosyası oluştur
4. İçine ilk 3 Python dosyasını yaz"""
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 40)
    
    try:
        result = agent.run_react_loop(task, max_iterations=4)
        print("\n" + "=" * 40)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    subprocess_test()