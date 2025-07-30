#!/usr/bin/env python3
"""
🔧 KENDİ KENDİNİ DÜZELTME TEST - JSON Hatası Simülasyonu
"""

from core_agent_react import ReactAgent

def kendi_kendini_duzeltme_test():
    print("🔧 KENDİ KENDİNİ DÜZELTME TEST BAŞLADI")
    print("=" * 50)
    
    agent = ReactAgent()
    
    # Agent'ın JSON hatası yapmasını tetikleyecek task
    task = """
Lütfen aşağıdaki işlemi yap:
1. Bu projedeki Python dosya sayısını bul
2. Sonucu çok detaylı bir şekilde, çok uzun bir rapor halinde sun

(Bu test agent'ın karmaşık cevap verirken JSON hatası yapıp kendini düzeltip düzeltemeyeceğini test ediyor)
"""
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 50)
    
    try:
        result = agent.run_react_loop(task, max_iterations=8)
        print("\n" + "=" * 50)
        print("🔧 SONUÇ:")
        print(result)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    kendi_kendini_duzeltme_test()