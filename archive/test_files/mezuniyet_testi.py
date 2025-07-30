#!/usr/bin/env python3
"""
🎓 MEZUNIYET PROJESİ: Otonom Mühendislik Testi
Atölye Şefi'nin tüm yeteneklerini test eden kapsamlı senaryo
"""

import sys
sys.path.append('.')

def start_graduation_project():
    """Mezuniyet projesini başlat"""
    print("🎓 ATOLYE ŞEFİ MEZUNİYET PROJESİ")
    print("=" * 70)
    print("📋 GÖREV:")
    print("Yeni özellik: 'feature/auto-documentation' branch'i oluştur")
    print("core_agent_react.py'nin kod kalitesini analiz et")
    print("Kalite iyiyse, Sphinx formatında dokümantasyon betiği yaz")
    print("docs/generate_docs.py olarak kaydet ve commit et")
    print("")
    print("🚀 Agent'ı başlatıyor...")
    print("=" * 70)
    
    try:
        from core_agent_react import ReactAgent
        
        # Agent'ı başlat
        agent = ReactAgent()
        print("✅ Atölye Şefi hazır!")
        
        # Kompleks mezuniyet görevi
        graduation_task = """Yeni bir özellik üzerinde çalışacağız. Adı 'feature/auto-documentation' olan yeni bir branch oluştur. core_agent_react.py dosyasının kod kalitesini analiz et. Eğer kod kalitesi iyiyse, bu dosyanın dokümantasyonunu (docstrings) Sphinx formatında oluşturan yeni bir Python betiği yaz ve bu betiği docs/generate_docs.py olarak kaydet. Oluşturduğun bu yeni dosyayı 'feat: Add auto-documentation script' mesajıyla commit et."""
        
        print(f"📝 MEZUNİYET GÖREVİ:")
        print(f"'{graduation_task}'")
        print("")
        
        # Agent'ın mezuniyet testini başlat
        result = agent.run_react_loop(graduation_task, max_iterations=15)
        
        print(f"\n🎯 MEZUNİYET PROJESİ SONUCU:")
        print("=" * 70)
        print(result)
        
        # Başarı değerlendirmesi
        success_indicators = [
            ("Branch oluşturma", "branch" in result.lower() and "feature/auto-documentation" in result.lower()),
            ("Kod kalitesi analizi", "kod kalite" in result.lower() or "code quality" in result.lower()),
            ("Dosya yazma", "docs/generate_docs.py" in result.lower()),
            ("Git commit", "commit" in result.lower()),
            ("Tamamlama", "tamamland" in result.lower() and "maksimum iterasyon" not in result.lower())
        ]
        
        passed_tests = []
        failed_tests = []
        
        for test_name, condition in success_indicators:
            if condition:
                passed_tests.append(test_name)
                print(f"✅ {test_name}")
            else:
                failed_tests.append(test_name)
                print(f"❌ {test_name}")
        
        success_count = len(passed_tests)
        total_tests = len(success_indicators)
        
        print("\n" + "=" * 70)
        if success_count >= 4:
            print("🎉 MEZUNİYET PROJESİ BAŞARILI!")
            print("🏆 Atölye Şefi artık tam otonom mühendis!")
            print(f"✅ Başarı oranı: {success_count}/{total_tests}")
            print("\n🎓 MEZUN OLDU: Atölye Şefi profesyonel AI mühendisi!")
            return True
        else:
            print("📚 Mezuniyet projesi kısmen başarılı")
            print(f"📊 Başarı oranı: {success_count}/{total_tests}")
            print(f"❌ Geliştirilmesi gereken alanlar: {failed_tests}")
            return False
            
    except Exception as e:
        print(f"❌ Mezuniyet testi hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = start_graduation_project()
    print(f"\n{'🎉 MEZUNIYET BAŞARILI!' if success else '📚 EK ÇALIŞMA GEREKLİ'}")
    sys.exit(0 if success else 1)