#!/usr/bin/env python3
"""
🛡️ DAYANIKLILIK TESTİ
Retry mekanizmasını kısa bir görevle test edelim
"""

from core_agent_react import ReactAgent

def main():
    print("🛡️ DAYANIKLILIK TESTİ BAŞLADI")
    print("=" * 40)
    
    # Agent'ı başlat
    agent = ReactAgent()
    
    # Kısa bir test görevi
    test_gorevi = "Merhaba, sadece 'Selam!' diye cevap ver."
    
    try:
        print("🚀 Test görevi başlatılıyor...")
        sonuc = agent.run_react_loop(test_gorevi, max_iterations=3)
        print(f"\n✅ SONUÇ: {sonuc}")
        return 0
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return 1

if __name__ == "__main__":
    main()