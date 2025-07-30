# 🌱 CORE AGENT - Temiz ve Odaklanmış Proje

## 📁 **TEMİZ DİZİN YAPISI**

```
Atolye_Sefi/
├── core_agent.py              # ⭐ ANA CORE AGENT
├── CORE_README.md             # Bu dosya
├── CLAUDE.md                  # Claude instructions
├── requirements.txt           # Dependencies
├── .env                       # Environment variables
│
├── tools/                     # Professional tools
├── workspace/                 # Çalışma alanı
├── docs/                      # Dokümantasyon
├── utils/                     # Utilities
│
└── archive/                   # ESKİ DOSYALAR (DİKKAT DAĞITMAZ)
    ├── old_agents/           # Eski agent denemeler
    ├── experiments/          # Test dosyaları
    └── infrastructure/       # Modal, Docker vs
```

## 🚀 **CORE AGENT ÇALIŞTIRMA**

```bash
# Basit çalıştırma
python core_agent.py

# Conda ile çalıştırma
conda run --live-stream --name Atolye_Sefi python core_agent.py
```

## 🎯 **CORE AGENT ÖZELLİKLERİ**

### ✅ **ÇALIŞAN ŞEYLER:**
- **LLM Bağlantısı:** Groq + Llama3-70b
- **Tek Araç:** Dosya listeleme (recursive)
- **Şeffaf İşlem:** Her adım görünür
- **Hata Yönetimi:** Çökmez, net mesaj verir

### 🎯 **TEST KOMUTLARI:**
- `mevcut dizindeki dosyaları listele`
- `workspace klasöründeki dosyaları göster`
- `merhaba`
- `exit`

## 📋 **PROJE İLKELERİ**

1. **Sıfır Yalan** - Sadece çalışan şeyleri iddia et
2. **Tek Görev** - Bir şeyi mükemmel yap
3. **Şeffaflık** - Her işlem görünür
4. **Basitlik** - Karmaşıklık düşmanı
5. **Test Edilmiş** - Her özellik kanıtlanmış

---

**🌱 Bu proje Core Agent temeli üzerine büyüyecek. Sağlam temel, sağlam gelecek.**