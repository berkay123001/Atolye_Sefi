#!/usr/bin/env python3
"""
🔧 FİNAL FİX TESTİ
Tüm düzeltmelerin çalışıp çalışmadığını test edelim
"""

from core_agent_react import ReactAgent

def test_final_fixes():
    print("🔧 FİNAL FİX TESTİ")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Basit ama kritik test
    task = "Bu projede Python dosyası var mı? Kaç tane?"
    
    print(f"🎯 TEST GÖREVİ: {task}")
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
    test_final_fixes()