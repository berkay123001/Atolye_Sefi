#!/usr/bin/env python3
"""
👓 VERİ GÖZLÜĞÜ TESTİ
Agent'ın yeni veri işleme yeteneğini test edelim
"""

from core_agent_react import ReactAgent

def test_data_processing():
    print("👓 VERİ GÖZLÜĞÜ TESTİ BAŞLADI")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Kritik test: Dosya listesi al ve işle
    task = "Bu projede kaç tane Python dosyası var? Listele ve say."
    
    print(f"🎯 TEST GÖREVİ: {task}")
    print("-" * 40)
    
    try:
        result = agent.run_react_loop(task, max_iterations=8)
        print("\n" + "=" * 40)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_data_processing()