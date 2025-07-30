#!/usr/bin/env python3
"""
🧠 OTOMATİK HAFIZA TESTİ
Agent'ın yeni otomatik hafıza sistemini test edelim
"""

from core_agent_react import ReactAgent

def test_otomatik_hafiza():
    print("🧠 OTOMATİK HAFIZA TESTİ")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Veri körlüğü sorunu test et
    task = "Bu projede kaç tane Python dosyası var?"
    
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
    test_otomatik_hafiza()