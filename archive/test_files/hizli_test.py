#!/usr/bin/env python3
"""
⚡ HIZLI TEST - Basit Dosya Sayma
"""

from core_agent_react import ReactAgent

def hizli_test():
    print("⚡ HIZLI TEST")
    print("=" * 30)
    
    agent = ReactAgent()
    
    # Çok basit test
    task = "Kaç Python dosyası var?"
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 30)
    
    try:
        result = agent.run_react_loop(task, max_iterations=3)
        print("\n" + "=" * 30)
        print("✅ SONUÇ:")
        print(result)
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    hizli_test()