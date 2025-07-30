# 🧪 TEST WORKSPACE - Agent Testing Lab

## 📁 **Bu Dizin Nedir?**
Bu workspace içindeki test alanıdır. Burada agent'ları güvenle test edebilirsin.

---

## 🤖 **AGENT ÇALIŞTIRMA**

### **1️⃣ Terminal Agent (Basit)**
```bash
python terminal_agent_runner.py
```
**Özellikler:**
- ✅ Basit komut işleme
- ✅ Dosya oluşturma
- ✅ Türkçe destek
- ✅ Hızlı yanıt

### **2️⃣ Graph Agent (Gelişmiş)**
```bash
python graph_agent_runner.py
```
**Özellikler:**
- ✅ Tüm professional tools
- ✅ Jedi Intelligence
- ✅ Git Operations
- ✅ Complex task handling

---

## 🧪 **TEST KOMUTLARI**

### **🔹 Basit Testler:**
```
merhaba
hello
help
```

### **🔹 Dosya İşlemleri:**
```
create python file test.py
Python dosyası oluştur hello.py
list files
```

### **🔹 Kod Analizi (Graph Agent):**
```
Jedi analiz yap: import math; result = math.sqrt(16)
kod hata analizi yap
workspace dosyalarını analiz et
```

### **🔹 Git İşlemleri (Graph Agent):**
```
git durumu nedir
git commit yap
git branch durumu
```

---

## 📁 **DİZİN YAPISI**

```
test_workspace/
├── terminal_agent_runner.py    # Terminal Agent runner
├── graph_agent_runner.py       # Graph Agent runner  
├── README.md                   # Bu dosya
├── test_files/                 # Oluşturulan test dosyaları
└── temp/                       # Geçici dosyalar
```

---

## 🔧 **SORUN GİDERME**

### **❌ Import Error:**
```bash
# Ana dizine git ve tekrar dene
cd /home/berkayhsrt/Atolye_Sefi
python workspace/test_workspace/terminal_agent_runner.py
```

### **❌ Path Error:**
```bash
# Python path kontrol et
python -c "import sys; print(sys.path)"
```

### **❌ Agent Error:**
- GROQ_API_KEY set edildi mi kontrol et
- .env dosyası var mı kontrol et

---

## 💡 **KULLANIM İPUÇLARI**

### **🎯 Terminal Agent İçin:**
- Basit komutları test et
- Dosya oluşturma test et
- Türkçe komutları dene

### **🎯 Graph Agent İçin:**
- Complex task'ları test et
- Tool integration'ı test et
- Professional features'ları dene

### **🎯 Genel:**
- Her test sonrası `test_files/` dizinini kontrol et
- Session history'yi gözlemle
- Error handling'i test et

---

## 🚀 **HIZLI BAŞLATMA**

### **🎯 Method 1: Direct Python**
```bash
# Test workspace'e git
cd /home/berkayhsrt/Atolye_Sefi/workspace/test_workspace

# Terminal Agent çalıştır (basit)
python terminal_agent_runner.py

# VEYA Graph Agent çalıştır (profesyonel)
python graph_agent_runner.py
```

### **🎯 Method 2: Conda Environment (Önerilen)**
```bash
# Ana dizinden çalıştır (çok güvenli)
cd /home/berkayhsrt/Atolye_Sefi

# Terminal Agent
conda run --live-stream --name Atolye_Sefi python workspace/test_workspace/terminal_agent_runner.py

# Graph Agent
conda run --live-stream --name Atolye_Sefi python workspace/test_workspace/graph_agent_runner.py
```

## ✅ **DÜZELTME TAMAMLANDI**

**🔧 Method çağrıları düzeltildi:**
- ✅ Terminal Agent: `process_request()` 
- ✅ Graph Agent: `run()` method ve doğru response yapısı

**🎯 Bu test workspace ile agent'ları güvenle test edebilirsin!**