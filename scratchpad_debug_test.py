#!/usr/bin/env python3
"""
🐛 SCRATCHPAD DEBUG TEST
Agent'ın scratchpad'i nasıl kullandığını debug edelim
"""

from core_agent_react import ReactAgent

def debug_scratchpad():
    print("🐛 SCRATCHPAD DEBUG TEST")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Çok basit task
    task = "Projedeki Python dosyalarından ilk 3'ünün ismini söyle"
    
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
    debug_scratchpad()