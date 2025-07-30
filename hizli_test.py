#!/usr/bin/env python3
"""
🚀 HIZLI TEST - Sadece temel fonksiyonları test et
"""

from core_agent_react import ReactAgent

def hizli_test():
    print("🚀 HIZLI TEST BAŞLADI")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Kısa test
    task = "Projedeki .py dosyalarından ilk 2'sini listele ve dosya sayısını söyle"
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 40)
    
    try:
        result = agent.run_react_loop(task, max_iterations=3)
        print("\n" + "=" * 40)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    hizli_test()