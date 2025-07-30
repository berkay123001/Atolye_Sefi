#!/usr/bin/env python3
"""
⚡ ULTRA SON TEST - JSON Kuralı Validation
"""

from core_agent_react import ReactAgent

def ultrason_test():
    print("⚡ ULTRA SON TEST BAŞLADI")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # En basit test
    task = "Bu projede kaç Python dosyası var? Kısa cevap ver."
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 40)
    
    try:
        result = agent.run_react_loop(task, max_iterations=4)
        print("\n" + "=" * 40)
        print("🏆 SONUÇ:")
        print(result)
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    ultrason_test()