#!/usr/bin/env python3
"""
🎓 MEZUNİYET TEST PİLOTU
Otomatik test sistemi - Manuel stdin hatalarını önlemek için
"""

import sys
import os
from pathlib import Path

# Core agent'ı import et
try:
    from core_agent_react import ReactAgent
    print("✅ CoreAgentReAct import edildi")
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    sys.exit(1)

# Mezuniyet görevi tanımı
MEZUNIYET_GOREVI = """
Atölye Şefi Mezuniyet Testi - Kapsamlı Mühendislik Görevi

Sen bir AI mühendisi olarak aşağıdaki kapsamlı görevi tamamlamalısın:

1. PROJE ANALİZİ:
   - Bu projenin dosya yapısını analiz et
   - Git durumunu kontrol et 
   - Ana Python dosyalarını tespit et

2. KOD KALİTESİ KONTROLÜ:
   - core_agent_react.py dosyasının kod kalitesini analiz et
   - tools/code_intelligence.py dosyasının bağımlılıklarını kontrol et
   - Varsa kod kalitesi sorunlarını raporla

3. GÜVENLIK TESTİ:
   - Aşağıdaki Python kodunu güvenli sandbox ortamında çalıştır:
   ```python
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
   ```

4. RAPOR OLUŞTURMA:
   - workspace/test_raporu.md dosyası oluştur
   - Bu dosyaya tüm analiz sonuçlarını yaz
   - Proje durumu özetini dahil et

BEKLENTİ: Tüm adımları başarıyla tamamla ve detaylı bir rapor sun. Bu test, ReAct Architecture'ın çok adımlı görev yönetimi kabiliyetini değerlendirir.
"""

def main():
    """Ana test pilotu fonksiyonu"""
    print("🎓 MEZUNİYET TEST PİLOTU BAŞLADI")
    print("=" * 50)
    
    # Agent'ı başlat
    try:
        agent = ReactAgent()
        print("✅ ReactAgent başarıyla oluşturuldu")
    except Exception as e:
        print(f"❌ Agent oluşturma hatası: {e}")
        return 1
    
    # Görevi otomatik olarak çalıştır
    try:
        print("🚀 Mezuniyet görevi başlatılıyor...")
        print("⚠️  Bu test tamamen otomatik olarak çalışacak")
        print("-" * 50)
        
        # run_react_loop metodunu kullanarak görevi çalıştır
        sonuc = agent.run_react_loop(MEZUNIYET_GOREVI, max_iterations=15)
        
        print("\n" + "=" * 50)
        print("🎯 FINAL SONUÇ:")
        print(sonuc)
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"❌ Test çalıştırma hatası: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)