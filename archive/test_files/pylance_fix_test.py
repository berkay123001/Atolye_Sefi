#!/usr/bin/env python3
"""
🔧 PYLANCE FIX TEST
Scratchpad erişim sorunu çözüldü mü kontrol edelim
"""

from core_agent_react import ReactAgent

def pylance_fix_test():
    print("🔧 PYLANCE FIX TEST")
    print("=" * 35)
    
    agent = ReactAgent()
    
    # Scratchpad kullanan basit test
    task = "Scratchpad'i test et ve çalışıyor mu kontrol et"
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 35)
    
    try:
        result = agent.run_react_loop(task, max_iterations=2)
        print("\n" + "=" * 35)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 35)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    pylance_fix_test()