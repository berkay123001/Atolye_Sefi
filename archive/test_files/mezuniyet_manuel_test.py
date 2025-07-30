#!/usr/bin/env python3
"""
🎓 MEZUNIYET MANUEL TESTİ
Agent'ın her adımını ayrı ayrı test edelim
"""

from core_agent_react import ReactAgent

def test_step_by_step():
    print("🎓 MEZUNIYET MANUEL TESTİ")
    print("=" * 40)
    
    agent = ReactAgent()
    
    # 1. Basit görev
    print("\n1️⃣ BASIT GÖREV TESTİ:")
    result1 = agent.run_react_loop("Merhaba de", max_iterations=2)
    print(f"Sonuç: {result1}")
    
    # 2. Git status
    print("\n2️⃣ GIT STATUS TESTİ:")
    result2 = agent.run_react_loop("Git durumunu kontrol et", max_iterations=3)
    print(f"Sonuç: {result2}")
    
    # 3. Docker sandbox
    print("\n3️⃣ DOCKER SANDBOX TESTİ:")
    sandbox_task = """Python kodunu güvenli sandbox'ta çalıştır:
print("Merhaba Docker!")
print(2 + 2)
"""
    result3 = agent.run_react_loop(sandbox_task, max_iterations=5)
    print(f"Sonuç: {result3}")

if __name__ == "__main__":
    test_step_by_step()