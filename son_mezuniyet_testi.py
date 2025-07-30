#!/usr/bin/env python3
"""
🎓 SON MEZUNİYET TESTİ - Final Answer JSON Kuralı İle
"""

from core_agent_react import ReactAgent

def son_mezuniyet_testi():
    print("🎓 SON MEZUNİYET TESTİ - FİNAL ANSWER JSON KURALI")
    print("=" * 60)
    
    agent = ReactAgent()
    
    # Kapsamlı son test
    task = """
MEZUNİYET TESTİ - SON SINAV

Bu projenin:
1. Python dosya sayısını bul
2. Git durumunu kontrol et
3. Ana bulguları özetle

Agent'ın Final Answer JSON kuralına uyup uymayacağı test ediliyor.
"""
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 60)
    
    try:
        result = agent.run_react_loop(task, max_iterations=10)
        print("\n" + "=" * 60)
        print("🏆 SON SONUÇ:")
        print(result)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    son_mezuniyet_testi()