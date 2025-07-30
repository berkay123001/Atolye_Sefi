#!/usr/bin/env python3
"""
🧠 SCRATCHPAD TESTİ
Agent'ın yeni çalışma tezgâhı yeteneğini test edelim
"""

from core_agent_react import ReactAgent

def test_scratchpad():
    print("🧠 SCRATCHPAD TESTİ")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # Kritik test: Dosya sayısı sorusu
    task = "Bu projede kaç tane Python dosyası var? Tam sayı söyle."
    
    print(f"🎯 TEST GÖREVİ: {task}")
    print("-" * 40)
    
    try:
        result = agent.run_react_loop(task, max_iterations=5)
        print("\n" + "=" * 40)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_scratchpad()