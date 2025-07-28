# 📚 Test System Tutorial - Pratik Kullanım Rehberi

## 🎯 **Test Sisteminin Anatomisi**

Senin `advanced_test_categories.py` sisteminde 3 ana bileşen var:

```
📦 Test System
├── 🏷️  Test Categories (Kategoriler)
├── 🧪 Test Cases (Senaryolar)  
└── 📊 Results & Logging (Sonuçlar & Loglar)
```

---

## 🏷️ **1. YENİ SENARYO EKLEME - Adım Adım**

### **Senaryo Ekleme Yeri: `advanced_test_categories.py` dosyasının içi**

**Lokasyon:** Line 83'ten başlayarak `self.advanced_categories` dictionary'si

### **Örnek: File Operations Senaryosu Ekleme**

```python
# advanced_test_categories.py içinde line ~273'e ekle:

"enhanced_file_operations": TestCategory(
    name="Enhanced File Operations Tests",
    description="Gelişmiş dosya işlemleri testleri",
    priority="CRITICAL",
    gemini_enhanced=False,  # İlk aşamada basit tutalım
    test_cases=[
        {
            # 🔍 Test Girdisi (Kullanıcının söylediği)
            "input": "klasörü izle ./test_folder",
            
            # ✅ Ne olmasını bekliyoruz
            "expected": "folder_watching_started",
            
            # 📝 Test açıklaması
            "description": "Klasör izleme özelliği testi",
            
            # 🎯 Özel kriterler (isteğe bağlı)
            "should_start_monitoring": True,
            "expected_response_time": 0.1  # 100ms
        },
        {
            "input": "dosya kopyala source.txt destination.txt",
            "expected": "file_copied_successfully", 
            "description": "Basit dosya kopyalama testi",
            "should_copy_file": True,
            "should_preserve_content": True
        },
        {
            "input": "100 dosyayı toplu kopyala",
            "expected": "bulk_copy_completed",
            "description": "Toplu dosya kopyalama performans testi", 
            "should_handle_bulk_operations": True,
            "expected_max_time": 5.0  # 5 saniye max
        }
    ]
)
```

### **Ekleme Adımları:**

1. **Dosyayı aç:** `tools/advanced_test_categories.py`
2. **Bul:** `self.advanced_categories = {` (line ~83)
3. **En sona ekle:** Yeni kategoriyi
4. **Kaydet:** Dosyayı

---

## 🧪 **2. TEST CASE'LERİN YAPISI**

Her test case şu alanları içerir:

### **🔧 Zorunlu Alanlar:**
```python
{
    "input": "kullanıcının yazdığı komut",
    "expected": "beklenen sonuç", 
    "description": "testin açıklaması"
}
```

### **⚡ İsteğe Bağlı Alanlar:**
```python
{
    # Özel kontroller
    "should_create_file": True,
    "should_start_monitoring": True,
    "should_return_list": True,
    
    # Performans hedefleri  
    "expected_response_time": 0.5,
    "expected_max_memory": 100,  # MB
    
    # Karmaşıklık seviyesi
    "complexity_score": 7,  # 1-10 arası
    
    # Hata senaryoları
    "should_handle_errors": True,
    "expected_error_type": "FileNotFoundError"
}
```

---

## 📊 **3. HATA LOGLAMA SİSTEMİ - Nasıl Çalışır**

### **Hata Loglama Mekanizması:**

```python
# Test çalışır → Başarısız olur → Otomatik log oluşturulur

def execute_category_tests(self, category, category_name):
    for test_case in category.test_cases:
        try:
            # Test çalıştırılır
            response = self.agent.process_request(test_case["input"])
            success, details = self.evaluate_test_case(test_case, response)
            
            if not success:
                # 🚨 HATA LOGU OTOMATIK OLUŞTURULUYOR
                self.create_issue_report(test_result, category.priority)
                
        except Exception as e:
            # 💥 EXCEPTION DURUMUNDA DA LOG OLUŞTURULUYOR
            error_result = TestResult(...)
            self.create_issue_report(error_result, "CRITICAL")
```

### **Log Dosyaları Nerede Oluşuyor:**

```bash
# Test çalıştırdığında otomatik oluşturulan dosyalar:

📁 Proje Root/
├── issue_reports_20250127_143022.json    # Detaylı hata raporu
├── issue_summary_20250127_143022.md      # Özet rapor  
├── claude_integration_20250127_143022.json # Claude için veri
└── claude_fixes_20250127_143022.sh       # Otomatik fix script
```

---

## 🔍 **4. TEST DEĞERLENDİRME SİSTEMİ**

### **Test Başarılı/Başarısız Nasıl Belirleniyor:**

```python
def evaluate_test_case(self, test_case, response, category):
    """Her kategori için özel değerlendirme"""
    
    success_criteria = []
    
    # 1. Genel Kriterler (hepsi için)
    details["response_quality"] = len(response.strip()) > 20
    details["no_errors"] = "error" not in response.lower()
    
    # 2. Özel Kriterler (kategori bazlı)
    if category == "enhanced_file_operations":
        # Dosya işlemleri için özel kontroller
        if test_case.get("should_copy_file"):
            details["file_copied"] = "kopyalandı" in response.lower()
            success_criteria.append(details["file_copied"])
            
        if test_case.get("should_start_monitoring"):  
            details["monitoring_started"] = "izleme" in response.lower()
            success_criteria.append(details["monitoring_started"])
    
    # 3. Final Karar
    overall_success = all(success_criteria)
    return overall_success, details
```

---

## 🎮 **5. PRATIK KULLANIM ÖRNEĞİ**

### **Senaryo: Enhanced File Operations Testi Ekleme**

**1. Test Case Ekle:**
```python
# advanced_test_categories.py'de line ~273'e ekle
"enhanced_file_operations": TestCategory(
    name="Enhanced File Operations",
    description="Yeni file tool testleri",
    priority="HIGH", 
    test_cases=[
        {
            "input": "watch folder ./test",
            "expected": "monitoring_active",
            "description": "Folder monitoring test",
            "should_start_watching": True
        }
    ]
)
```

**2. Değerlendirme Kriteri Ekle:**
```python
# evaluate_test_case fonksiyonuna (line ~398) ekle:
elif category == "enhanced_file_operations":
    if test_case.get("should_start_watching"):
        details["watching_active"] = "watching" in response.lower()
        success_criteria.append(details["watching_active"])
```

**3. Test Çalıştır:**
```bash
cd /home/berkayhsrt/Atolye_Sefi
python tools/advanced_test_categories.py
```

**4. Sonuçları İncele:**
```bash
# Otomatik oluşan dosyalara bak:
cat issue_summary_*.md      # Özet rapor
cat issue_reports_*.json   # Detaylı rapor
```

---

## 🚨 **6. HATA TİPLERİ VE ÇÖZÜMLEME**

### **Test Başarısızlık Sebepleri:**

```python
# 1. Response Quality Failed
# Sebep: Agent çok kısa yanıt verdi (< 20 karakter)
# Çözüm: Agent'ın response generation'ını iyileştir

# 2. Category Specific Failed  
# Sebep: Beklenen anahtar kelime response'ta yok
# Çözüm: Test case criteria'sını gözden geçir

# 3. Exception Occurred
# Sebep: Agent crash oldu
# Çözüm: Agent'ta bug fix gerekli
```

### **Issue Report Anatomisi:**
```json
{
    "issue_id": "ISSUE_20250127_143022_001",
    "category": "enhanced_file_operations", 
    "severity": "HIGH",
    "title": "Test Failure: Folder monitoring test",
    "description": "Test failed for input: 'watch folder ./test'",
    "test_input": "watch folder ./test",
    "expected_behavior": "monitoring_active",
    "actual_behavior": "Dosya işlemleri desteklenmiyor",
    "suggested_fixes": [
        "Implement folder watching functionality",
        "Add watchdog library integration",
        "Create file monitoring wrapper"
    ]
}
```

---

## ⚡ **7. HIZLI TEST EKLEME REHBERİ**

### **3 Dakikada Test Case Ekleme:**

```python
# 1. KOPYALA BU TEMPLATE'İ:
{
    "input": "YENİ_KOMUT_BURAYA",
    "expected": "BEKLENİLEN_SONUÇ",
    "description": "Test açıklaması",
    "should_DO_SOMETHING": True  # Özel kriter
}

# 2. advanced_test_categories.py'de kategori bul
# 3. test_cases listesine ekle  
# 4. evaluate_test_case'e özel kriter ekle (isteğe bağlı)
# 5. Test çalıştır!
```

---

**🎯 Şimdi hangi senaryoyu eklemek istiyorsun? File operations ile mi başlayalım?**

**Pratik Deney:** 5 dakikada basit bir file operations test case ekleyip çalıştıralım mı?