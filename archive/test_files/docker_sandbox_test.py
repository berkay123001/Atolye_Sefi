#!/usr/bin/env python3
"""
🐳 DOCKER SANDBOX TESTİ
Mezuniyet testindeki güvenlik bölümünü direkt test edelim
"""

from tools.secure_executor import run_code_in_sandbox

def main():
    print("🐳 DOCKER SANDBOX TESTİ BAŞLADI")
    print("=" * 40)
    
    # Test kodu - mezuniyet testindeki kodun aynısı
    test_code = """
import math
import json

# Test hesaplamaları
result = {
    "fibonacci_10": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
    "pi_calculation": round(math.pi * 4, 2),
    "system_info": "Sandbox test başarılı"
}

print("🎯 Sandbox Test Sonucu:")
print(json.dumps(result, indent=2, ensure_ascii=False))
"""
    
    try:
        print("🚀 Docker sandbox'ında kod çalıştırılıyor...")
        result = run_code_in_sandbox.invoke({"code": test_code, "language": "python"})
        print("\n" + "=" * 40)
        print("✅ SONUÇ:")
        print(result)
        print("=" * 40)
        return 0
        
    except Exception as e:
        print(f"❌ Sandbox test hatası: {e}")
        return 1

if __name__ == "__main__":
    main()