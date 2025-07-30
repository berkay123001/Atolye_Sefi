#!/usr/bin/env python3
"""
🏁 SON TEST - Hijyen Filtresi Başarı Testi
"""

from core_agent_react import ReactAgent

def son_test():
    print("🏁 SON TEST - HİJYEN FİLTRESİ BAŞARI TESTİ")
    print("=" * 50)
    
    agent = ReactAgent()
    
    # Basit görev - Git durumunu öğren
    task = "Git repository durumunu kontrol et"
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 30)
    
    try:
        result = agent.run_react_loop(task, max_iterations=2)
        print("\n" + "=" * 30)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 30)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    son_test()