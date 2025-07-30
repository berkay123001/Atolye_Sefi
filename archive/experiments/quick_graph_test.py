#!/usr/bin/env python3
"""
🔥 QUICK GRAPH AGENT TEST - Sistem Prompt Fix
GraphAgent'a hızlı sistem prompt düzeltmesi yapıp test edelim
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_intent_classification():
    """Intent classification'ı test et"""
    
    print("🔍 INTENT CLASSIFICATION TEST")
    print("=" * 40)
    
    # Manual test patterns
    test_cases = [
        ("merhaba", "CHAT"),
        ("orda mısın", "CHAT"),
        ("nasılsın", "CHAT"),
        ("neler yapabilirsin", "HELP"),
        ("dosyaları listele", "CODE"),
        ("bozuk proje dosyasında hata var mı", "CODE")
    ]
    
    # Simple classification logic (GraphAgent style)
    def classify_intent_fixed(user_input: str) -> str:
        input_lower = user_input.lower().strip()
        
        # CHAT keywords - Greetings and simple questions (NEW!)
        chat_patterns = [
            "merhaba", "selam", "hello", "hi", "hey", "nasılsın", 
            "orda mısın", "burada mısın", "naber", "slm"
        ]
        if any(pattern in input_lower for pattern in chat_patterns):
            return "CHAT"
        
        # HELP keywords
        help_patterns = [
            "neler yapabilir", "ne yapabilir", "hangi özelliklerin var",
            "komutlar", "özellik", "yardım", "nasıl kullan"
        ]
        if any(pattern in input_lower for pattern in help_patterns):
            return "HELP"
        
        # CODE keywords
        code_patterns = [
            "çalıştır", "kod", "script", "python", "dosya", "klasör",
            "listele", "göster", "analiz", "hata", "bozuk"
        ]
        if any(pattern in input_lower for pattern in code_patterns):
            return "CODE"
        
        return "UNCLEAR"
    
    # Test cases
    for test_input, expected in test_cases:
        result = classify_intent_fixed(test_input)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{test_input}' → {result} (expected: {expected})")
    
    print("\n🎯 QUICK FIX: Chat patterns eklendi!")

def main():
    """Ana test"""
    print("🔥 QUICK GRAPH AGENT FIX TEST")
    print("=" * 50)
    
    test_intent_classification()
    
    print("\n💡 SONUÇ:")
    print("GraphAgent'da classify_intent fonksiyonuna CHAT patterns eklenmeli!")
    print("Bu sayede 'merhaba', 'orda mısın' gibi basit sorular CHAT olarak sınıflandırılacak.")

if __name__ == "__main__":
    main()