#!/usr/bin/env python3
"""
🎓 FINAL MEZUNİYET TESTİ - Kendi Kendini Düzeltme Sistemi İle
"""

from core_agent_react import ReactAgent

def final_mezuniyet_testi():
    print("🎓 FINAL MEZUNİYET TESTİ BAŞLADI")
    print("=" * 50)
    
    agent = ReactAgent()
    
    # Karmaşık mezuniyet görevi
    task = """
🎯 ATÖLYE ŞEFİ FINAL MEZUNİYET TESTİ

Bu projenin:
1. Python dosyalarını say ve ilk 3'ünü listele
2. Git durumunu kontrol et
3. workspace/final_rapor.md dosyası oluştur ve bu verileri yaz
4. Raporda toplam dosya sayısını da belirt

Agent'ın kendi kendini düzeltme kabiliyeti test ediliyor.
"""
    
    print(f"🎯 GÖREV: {task}")
    print("-" * 50)
    
    try:
        result = agent.run_react_loop(task, max_iterations=15)
        print("\n" + "=" * 50)
        print("🏆 FINAL SONUÇ:")
        print(result)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    final_mezuniyet_testi()