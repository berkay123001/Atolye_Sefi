#!/usr/bin/env python3
"""
⚡ HIZLI EXECUTE TEST
execute_local_python aracının çalışıp çalışmadığını test et
"""

from core_agent_react import execute_local_python

def test_execute():
    print("⚡ EXECUTE_LOCAL_PYTHON TESTİ")
    print("=" * 30)
    
    # Test 1: Basit matematik
    print("Test 1: Basit matematik")
    result1 = execute_local_python.invoke({"code": "print(2 + 2)\nprint('Hello, World!')"})
    print(result1)
    
    print("\n" + "-" * 30)
    
    # Test 2: Liste işleme
    print("Test 2: Liste işleme")
    code2 = """
files = ['app.py', 'config.json', 'main.py', 'test.txt', 'core_agent.py']
py_files = [f for f in files if f.endswith('.py')]
print(f'Python dosyaları ({len(py_files)} adet):')
for f in py_files:
    print(f'  - {f}')
"""
    result2 = execute_local_python.invoke({"code": code2})
    print(result2)

if __name__ == "__main__":
    test_execute()