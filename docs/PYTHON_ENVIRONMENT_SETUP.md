# 🐍 VS Code Python Environment Seçimi Rehberi

## 📋 **Hızlı Environment Seçimi:**

### **1. Command Palette Yöntemi (En Kolay):**
```
Ctrl+Shift+P → "Python: Select Interpreter" → Environment seç
```

### **2. Durum Çubuğu Yöntemi:**
- Sol alt köşede Python versiyonu yazısına tıkla
- Açılan listeden environment seç

### **3. Workspace Settings ile:**
- `.vscode/settings.json` dosyasını aç
- Şu satırı ekle:
```json
{
    "python.defaultInterpreter": "/path/to/your/python"
}
```

## 🔍 **Mevcut Python Yollarını Bulma:**

### System Python:
```bash
which python3        # /usr/bin/python3
python3 --version    # Python 3.x.x
```

### Conda Environment:
```bash
conda env list       # Tüm environment'ları listele
which python         # Aktif environment'ın yolu
```

### Virtual Environment:
```bash
source venv/bin/activate  # Environment'ı aktif et
which python             # Environment'ın Python yolu
```

## ⚡ **Proje İçin Önerilen Seçimler:**

### **Seçenek 1: System Python3 (Basit)**
```
/usr/bin/python3
```
- ✅ Basit ve hızlı
- ✅ Dependencies global olarak yüklü
- ❌ Proje arası dependency karışması riski

### **Seçenek 2: Virtual Environment (Önerilen)**
```bash
# Virtual environment oluştur
python3 -m venv .venv

# Aktif et
source .venv/bin/activate

# Dependencies yükle
pip install -r requirements.txt
```
Sonra VS Code'da `.venv/bin/python` seç.

### **Seçenek 3: Conda Environment**
```bash
# Environment oluştur
conda create -n atolye_sefi python=3.10

# Aktif et
conda activate atolye_sefi

# Dependencies yükle
pip install -r requirements.txt
```
Sonra VS Code'da conda environment'ını seç.

## 🎯 **Şu Anki Proje İçin Önerdiğim:**

1. **Command Palette'ı aç:** `Ctrl+Shift+P`
2. **"Python: Select Interpreter" yaz**
3. **System Python'ı seç:** `/usr/bin/python3`
4. **Dependencies yükle:**
   ```bash
   pip3 install -r requirements.txt
   ```

Bu şekilde hızlıca başlayabilirsin! 🚀

## 🔧 **Sorun Giderme:**

### Dependencies Eksikse:
```bash
cd /home/berkayhsrt/Atolye_Sefi
pip3 install -r requirements.txt
```

### Permission Hatası Alırsan:
```bash
pip3 install --user -r requirements.txt
```

### ImportError Alırsan:
- VS Code'u yeniden başlat
- Environment'ı tekrar seç
- Terminal'de `python3 -c "import langchain"` ile test et
