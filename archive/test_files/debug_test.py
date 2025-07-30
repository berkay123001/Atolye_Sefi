#!/usr/bin/env python3
"""
🔧 DEBUG TEST
"""

from core_agent_react import ReactAgent

def debug_test():
    print("🔧 DEBUG TEST")
    print("=" * 20)
    
    agent = ReactAgent()
    
    # Çok basit test
    task = "Kaç .py dosyası?"
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 20)
    
    try:
        result = agent.run_react_loop(task, max_iterations=4)
        print("\nSONUÇ:", result)
        
    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    debug_test()