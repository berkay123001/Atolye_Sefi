#!/usr/bin/env python3
"""
🧼 HİJYEN FİLTRESİ TESTİ
Yeni hijyen filtresi ve çok dilli destek testi
"""

from core_agent_react import ReactAgent

def hijyen_test():
    print("🧼 HİJYEN FİLTRESİ TESTİ")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Basit Python dosya sayma testi
    task = "Bu projede kaç tane .py dosyası var?"
    
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    hijyen_test()