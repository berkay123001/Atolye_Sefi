#!/usr/bin/env python3
"""
🔧 SİSTEM TESTİ - YENİ HAFIZA SİSTEMİ
"""

from core_agent_react import ReactAgent

def sistem_test():
    print("🔧 SİSTEM TESTİ - YENİ HAFIZA SİSTEMİ")
    print("=" * 50)
    
    agent = ReactAgent()
    
    # Basit Python dosya sayma testi
    task = "Python dosyası say"
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 30)
    
    try:
        result = agent.run_react_loop(task, max_iterations=4)
        print("\n" + "=" * 30)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 30)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sistem_test()