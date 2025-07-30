#!/usr/bin/env python3
"""
👁️ CODE QUALITY - Kod Kalite Analiz Motoru
Ruff tabanlı hızlı kod kalitesi analizi ve hata tespiti
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool

def _check_ruff_availability() -> Dict[str, Any]:
    """
    Ruff'ın yüklü olup olmadığını kontrol eder
    """
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            return {
                "status": "available",
                "version": version,
                "message": f"Ruff available: {version}"
            }
        else:
            return {
                "status": "error",
                "message": f"Ruff command failed: {result.stderr}",
                "suggestion": "Try: pip install ruff"
            }
            
    except FileNotFoundError:
        return {
            "status": "not_installed",
            "message": "Ruff is not installed",
            "suggestion": "Install with: pip install ruff"
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "message": "Ruff version check timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error checking Ruff: {str(e)}"
        }

def _safe_read_python_file(file_path: str) -> Dict[str, Any]:
    """
    Python dosyasını güvenli şekilde okur ve temel kontrolleri yapar
    """
    try:
        target_path = Path(file_path)
        
        # Dosya var mı?
        if not target_path.exists():
            return {
                "status": "error",
                "message": f"Dosya bulunamadı: {file_path}",
                "error_type": "file_not_found"
            }
        
        # Python dosyası mı?
        if target_path.suffix != '.py':
            return {
                "status": "error", 
                "message": f"Sadece Python dosyaları analiz edilebilir (.py), verilen: {target_path.suffix}",
                "error_type": "invalid_file_type"
            }
        
        # Dosya boyutu kontrolü (çok büyük dosyalar için)
        file_size = target_path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB limit
            return {
                "status": "error",
                "message": f"Dosya çok büyük ({file_size} bytes). Maksimum 1MB desteklenir.",
                "error_type": "file_too_large"
            }
        
        # Dosyayı oku
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "status": "success",
            "content": content,
            "file_size": file_size,
            "line_count": len(content.splitlines())
        }
        
    except UnicodeDecodeError:
        return {
            "status": "error",
            "message": f"Dosya UTF-8 formatında okunamadı: {file_path}",
            "error_type": "encoding_error"
        }
    except PermissionError:
        return {
            "status": "error",
            "message": f"Dosyaya erişim izni yok: {file_path}",
            "error_type": "permission_error"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Dosya okuma hatası: {str(e)}",
            "error_type": "unknown_error"
        }

def _run_ruff_analysis(file_path: str) -> Dict[str, Any]:
    """
    Ruff ile kod kalitesi analizi yapar - GÜVENLI ve HEDEFLI
    """
    try:
        # GÜVENLI Ruff check komutu - lazer odaklı analiz - DÜZELTİLDİ
        result = subprocess.run(
            ["ruff", "check", "--output-format=json", "--quiet", "--exit-zero", file_path],
            capture_output=True,
            text=True,
            timeout=15  # Daha kısa timeout - tek dosya için yeterli
        )
        
        # DEBUG logs kaldırıldı - artık çalışıyor
        
        # Ruff çıktısını parse et
        issues = []
        
        if result.stdout.strip():
            try:
                ruff_output = json.loads(result.stdout)
                for issue in ruff_output:
                    # GÜVENLI parsing - None değerleri handle et
                    rule_code = issue.get("code") or "UNKNOWN"
                    message = issue.get("message", "No message")
                    
                    # Syntax error tespiti - code None ise message'a bak
                    if "SyntaxError" in message:
                        severity = "error"
                        rule_code = "E999"  # Ruff syntax error kodu
                    elif isinstance(rule_code, str) and rule_code.startswith("E"):
                        severity = "error"
                    else:
                        severity = "warning"
                    
                    issues.append({
                        "rule_code": rule_code,
                        "rule_name": message,
                        "severity": severity,
                        "line": issue.get("location", {}).get("row", 0) if issue.get("location") else 0,
                        "column": issue.get("location", {}).get("column", 0) if issue.get("location") else 0,
                        "fix_available": issue.get("fix") is not None
                    })
            except json.JSONDecodeError:
                # Fallback: parse text output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and ' ' in line:
                        issues.append({
                            "rule_code": "PARSE_ERROR",
                            "rule_name": line.strip(),
                            "severity": "warning",
                            "line": 0,
                            "column": 0,
                            "fix_available": False
                        })
        
        return {
            "status": "success",
            "issues": issues,
            "total_issues": len(issues),
            "return_code": result.returncode,
            "stderr": result.stderr if result.stderr else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Ruff analizi 30 saniye içinde tamamlanamadı",
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ruff analizi hatası: {str(e)}",
            "error_type": "ruff_error"
        }

def _categorize_issues(issues: List[Dict]) -> Dict[str, Any]:
    """
    Sorunları kategorilere ayırır ve özet çıkarır
    """
    categories = {
        "errors": [],
        "warnings": [],
        "style_issues": [],
        "imports": [],
        "complexity": [],
        "security": []
    }
    
    for issue in issues:
        rule_code = issue.get("rule_code", "")
        severity = issue.get("severity", "warning")
        
        # Severity'e göre ayır
        if severity == "error":
            categories["errors"].append(issue)
        else:
            categories["warnings"].append(issue)
        
        # Rule code'a göre kategorilere ayır
        if rule_code.startswith(("E", "W")):  # PEP8 style
            categories["style_issues"].append(issue)
        elif rule_code.startswith(("F401", "F811", "I")):  # Import issues
            categories["imports"].append(issue)
        elif rule_code.startswith(("C9")):  # Complexity
            categories["complexity"].append(issue)
        elif rule_code.startswith(("S")):  # Security
            categories["security"].append(issue)
    
    return {
        "categories": categories,
        "summary": {
            "total_errors": len(categories["errors"]),
            "total_warnings": len(categories["warnings"]),
            "style_issues": len(categories["style_issues"]),
            "import_issues": len(categories["imports"]),
            "complexity_issues": len(categories["complexity"]),
            "security_issues": len(categories["security"])
        }
    }

def _find_best_file_match(query: str) -> str:
    """
    Kullanıcının dağınık query'sinden en uygun dosya yolunu bulur
    """
    import os
    from pathlib import Path
    
    # Eğer direkt valid bir dosya yolu verilmişse, onu kullan
    if os.path.exists(query) and query.endswith('.py'):
        return query
    
    # Query'den potansiyel dosya isimlerini çıkar
    potential_names = []
    words = query.replace('/', ' ').replace('\\', ' ').split()
    
    for word in words:
        if word.endswith('.py'):
            potential_names.append(word)
        elif '.' not in word and len(word) > 2:  # Uzantısız isim
            potential_names.append(word + '.py')
    
    # Eğer hiç potansiyel isim bulamazsak, query'nin kendisini dene
    if not potential_names:
        if not query.endswith('.py'):
            query += '.py'
        potential_names.append(query)
    
    # Proje içinde bu isimleri ara
    all_python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(root, file))
                all_python_files.append(rel_path)
    
    # En iyi match'i bul
    best_match = None
    best_score = 0
    
    for potential in potential_names:
        for py_file in all_python_files:
            # Exact match
            if py_file.endswith(potential):
                score = len(potential)
                if potential in query:  # Query'de geçiyor mu
                    score += 10
                if score > best_score:
                    best_score = score
                    best_match = py_file
    
    return best_match if best_match else query

@tool
def analyze_code_quality(query: str) -> str:
    """
    AKILLI: Python dosyasının kod kalitesini analiz eder - dosya bulma özellikli.
    
    BU ARAÇ ARTIK AKILLI: 
    - "bozuk.py dosyası" → otomatik dosya bulma
    - "workspace/test/bozuk.py" → direkt dosya yolu
    - "core_agent kodunu analiz et" → core_agent*.py dosyasını bulur
    
    Yapılan analizler:
    - Ruff ile syntax error ve kalite kontrolü
    - PEP8 stil kontrolü  
    - Import sorunlarını bulma
    - Kod karmaşıklığını değerlendirme
    
    Args:
        query: Dosya adı, yolu veya analiz isteği (esnek format)
    
    Returns:
        Özetlenmiş kod kalitesi analiz raporu
    """
    # GÜVENLIK KONTROLÜ: query mutlaka belirtilmeli
    if not query or query.strip() == "":
        return """❌ **GÜVENLİK HATASI: Dosya Sorgusu Eksik**
        
Lütfen analiz edilecek Python dosyasını belirtin.

💡 **Örnekler:** 
- "bozuk.py dosyasını analiz et"
- "tools/code_quality.py" 
- "core_agent kodunu kontrol et"
- "workspace içindeki test dosyası"""
    
    # AKILLI DOSYA BULMA
    file_path = _find_best_file_match(query.strip())
    
    print(f"👁️ [CODE QUALITY] Akıllı arama: '{query}' → '{file_path}'")
    
    # 1. Ruff'ın varlığını kontrol et
    ruff_check = _check_ruff_availability()
    
    if ruff_check["status"] != "available":
        return f"""❌ **Ruff Analiz Aracı Kullanılamıyor**
        
**Durum:** {ruff_check['status']}
**Hata:** {ruff_check['message']}

💡 **Çözüm:** {ruff_check.get('suggestion', 'Ruff kurulumu gerekli')}

⚠️ Kod kalitesi analizi için Ruff kurulumu gereklidir."""

    # 2. Dosyayı güvenli oku
    file_result = _safe_read_python_file(file_path)
    
    if file_result["status"] == "error":
        return f"""❌ **Dosya Okuma Hatası:**
        
**Dosya:** `{file_path}`
**Hata:** {file_result['message']}
**Tip:** {file_result['error_type']}

💡 **Çözüm Önerileri:**
- Dosya yolunun doğru olduğundan emin olun
- Dosyanın Python (.py) formatında olduğunu kontrol edin
- Dosya izinlerini kontrol edin"""

    # 3. Ruff analizi yap
    ruff_result = _run_ruff_analysis(file_path)
    
    if ruff_result["status"] == "error":
        return f"""❌ **Kod Kalitesi Analizi Hatası:**
        
**Dosya:** `{file_path}`
**Hata:** {ruff_result['message']}

Dosya okunabildi ama Ruff analizi başarısız oldu."""

    # 4. Sonuçları kategorilere ayır
    categorized = _categorize_issues(ruff_result["issues"])
    issues = ruff_result["issues"]
    total_issues = ruff_result["total_issues"]
    summary = categorized["summary"]
    
    # 5. AKILLI ÖZETLEME: Anlaşılır rapor oluştur
    report = f"""👁️ **Kod Kalitesi Analizi Özeti**

📂 **Hedef Dosya:** `{file_path}`
📊 **Boyut:** {file_result['file_size']} karakter ({file_result['line_count']} satır)
🔍 **Analiz Motoru:** {ruff_check['version']}

📈 **SONUÇ:** {total_issues} sorun tespit edildi"""

    # AKILLI ÖZETLEME: Sadece kritik bilgileri göster
    if total_issues == 0:
        report += """

✅ **MÜKEMMEL!** Bu dosyada kod kalitesi sorunu yok.
🏆 Tüm standartlara uygun, temiz kod."""

    else:
        # Sorun özetini akıllı şekilde göster
        report += f"""

📊 **SORUN DAĞILIMI:**
🚨 Hatalar: {summary['total_errors']} | ⚠️ Uyarılar: {summary['total_warnings']}"""
        
        # TÜM SORUNLARI GÖSTER - gizleme yok!
        if issues:
            report += f"\n\n🔍 **TÜM SORUNLAR ({total_issues} adet):**"
            for i, issue in enumerate(issues, 1):
                fix_indicator = "🔧" if issue["fix_available"] else "⚠️"
                severity_icon = "🚨" if issue["severity"] == "error" else "⚠️"
                report += f"\n{i}. {severity_icon} Satır {issue['line']}: {issue['rule_name']}"
                
        # Genel değerlendirme
        if total_issues <= 3:
            report += f"\n\n🟢 **DEĞERLENDİRME:** Temiz kod - küçük iyileştirmeler"
        elif total_issues <= 10:
            report += f"\n\n🟡 **DEĞERLENDİRME:** Orta kalite - gözden geçirme önerilir"
        else:
            report += f"\n\n🔴 **DEĞERLENDİRME:** Ciddi sorunlar - refactoring gerekli"

    report += f"""

✅ **Analiz Tamamlandı!** Kod kalitesi değerlendirmesi başarıyla yapıldı."""
    
    print(f"✅ [CODE QUALITY] Analiz tamamlandı: {total_issues} sorun tespit edildi")
    return report

# Test fonksiyonu (geliştirme aşamasında kullanım için)
def _test_code_quality():
    """Code quality aracını test eder"""
    print("🧪 Code Quality Test Başlıyor...")
    
    # Test dosyası oluştur - kasıtlı hatalarla
    test_content = '''import os
import sys
import unused_module

def bad_function( x,y ):
    if x==1:
        print("Hello")
    if y==2:
        print( "World" )
    unused_var = 42
    return x+y

def another_function():
    pass
'''
    
    test_file = "test_code_quality.py"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    try:
        # Test et
        result = analyze_code_quality.invoke({"file_path": test_file})  
        print("✅ Test başarılı!")
        print(result)
    except Exception as e:
        print(f"❌ Test başarısız: {e}")
    finally:
        # Test dosyasını temizle
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    _test_code_quality()