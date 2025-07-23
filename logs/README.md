# 📋 Logs Klasörü

Bu klasör Claude Code geliştirme sürecindeki önemli değişiklikleri, hataları ve çözümleri takip eder.

## 📁 **DOSYA YAPISI:**

- `development_log.md` - Ana geliştirme logu
- `errors_and_fixes.md` - Hata ve çözüm kayıtları  
- `performance_notes.md` - Performans iyileştirmeleri
- `integration_notes.md` - Entegrasyon notları

## 🎯 **AMAÇ:**

Claude Code'un bir sonraki çalışmada:
- Önceki değişiklikleri hatırlayabilmesi
- Yapılan hataları tekrarlamaması
- Geliştirme sürecini takip edebilmesi
- Proje durumunu anlayabilmesi

## 🔒 **GİZLİLİK:**

Bu klasör `.gitignore` ile git'ten hariç tutulmuştur.
- ✅ Yerel geliştirme notları
- ✅ Hata analizi kayıtları
- ✅ Claude'un hafıza desteği
- ❌ Git repository'de saklanmaz

## 📝 **KULLANIM:**

Claude Code her önemli değişiklikten sonra bu dosyaları güncelleyecek:

```bash
# Yeni hata kaydı
echo "$(date): SSH connection error fixed" >> logs/errors_and_fixes.md

# Geliştirme notu
echo "## $(date): Feature X completed" >> logs/development_log.md
```

## 🔍 **CLAUDE İÇİN TALİMATLAR:**

Yeni bir session başladığında:

1. `logs/development_log.md` oku - son durumu anla
2. `logs/errors_and_fixes.md` oku - tekrar hatalardan kaçın
3. Yeni değişiklikler sonrası logları güncelle
4. Önemli milestone'ları kaydet