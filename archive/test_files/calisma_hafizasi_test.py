#!/usr/bin/env python3
"""
🧠 ÇALIŞMA HAFIZASI TESTİ
Agent'ın yeni veri aktarım yeteneğini test edelim
"""

from core_agent_react import ReactAgent

def test_memory():
    print("🧠 ÇALIŞMA HAFIZASI TESTİ")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Kritik test: Büyük veri seti veri işleme
    task = "Bu projede kaç tane Python dosyası var? Tam sayısını söyle."
    
    print(f"🎯 TEST GÖREVİ: {task}")
    print("-" * 40)
    
    try:
        result = agent.run_react_loop(task, max_iterations=6)
        print("\n" + "=" * 40)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_memory()