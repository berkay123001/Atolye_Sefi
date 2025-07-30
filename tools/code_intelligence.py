#!/usr/bin/env python3
"""
🧠 CODE INTELLIGENCE - Kod Analiz Motoru
Sağlam, profesyonellik odaklı kod analizi araçları
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool

def _safe_read_file(file_path: str) -> Dict[str, Any]:
    """
    Dosyayı güvenli şekilde okur ve syntax kontrolü yapar
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
        
        # Dosyayı oku
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Syntax kontrolü
        try:
            ast.parse(content)
        except SyntaxError as e:
            return {
                "status": "error",
                "message": f"Dosyada syntax hatası bulundu: {e.msg} (satır {e.lineno})",
                "error_type": "syntax_error",
                "line_number": e.lineno
            }
        
        return {
            "status": "success",
            "content": content,
            "file_size": len(content)
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

def _extract_imports_from_ast(content: str) -> Dict[str, Any]:
    """
    AST kullanarak import'ları çıkarır - Jedi'ye alternatif, daha stabil
    """
    try:
        tree = ast.parse(content)
        imports = {
            "standard_imports": [],      # import os, sys
            "from_imports": [],          # from pathlib import Path
            "relative_imports": [],      # from .utils import helper
            "all_modules": set()         # Tüm import edilen modüller
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # import os, sys şeklinde
                for alias in node.names:
                    module_name = alias.name
                    alias_name = alias.asname if alias.asname else alias.name
                    imports["standard_imports"].append({
                        "module": module_name,
                        "alias": alias_name,
                        "line": node.lineno
                    })
                    imports["all_modules"].add(module_name.split('.')[0])  # İlk seviye modül
                    
            elif isinstance(node, ast.ImportFrom):
                # from module import item şeklinde
                module_name = node.module if node.module else "." * node.level
                
                for alias in node.names:
                    item_name = alias.name
                    alias_name = alias.asname if alias.asname else alias.name
                    
                    import_info = {
                        "module": module_name,
                        "item": item_name,
                        "alias": alias_name,
                        "line": node.lineno,
                        "level": node.level  # Relative import level (0=absolute, >0=relative)
                    }
                    
                    if node.level > 0:  # Relative import (from .utils import)
                        imports["relative_imports"].append(import_info)
                    else:  # Absolute import (from os import path)
                        imports["from_imports"].append(import_info)
                        if module_name:
                            imports["all_modules"].add(module_name.split('.')[0])
        
        # Set'i list'e çevir (JSON serializable)
        imports["all_modules"] = sorted(list(imports["all_modules"]))
        
        return {
            "status": "success",
            "imports": imports,
            "total_imports": len(imports["standard_imports"]) + len(imports["from_imports"]) + len(imports["relative_imports"])
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Import analizi hatası: {str(e)}",
            "error_type": "ast_analysis_error"
        }

def _find_best_file_match_for_imports(query: str) -> str:
    """
    get_file_imports için akıllı dosya bulma - code_quality ile aynı mantık
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
def get_file_imports(query: str) -> str:
    """
    AKILLI: Python dosyasının bağımlılıklarını analiz eder - dosya bulma özellikli.
    
    BU ARAÇ ARTIK AKILLI: 
    - "core_agent.py bağımlılıkları" → otomatik dosya bulma
    - "tools/kod_intelligence.py" → direkt dosya yolu
    - "bozuk dosyanın import'ları" → bozuk.py dosyasını bulur
    
    Yapılan analizler:
    - Dosya varlık kontrolü
    - Python syntax hata tespiti
    - Tüm import türlerini listeler (import, from...import, relative)
    - Bağımlılık modüllerini kategorize eder
    
    Args:
        query: Dosya adı, yolu veya analiz isteği (esnek format)
    
    Returns:
        Detaylı import analizi raporu
    """
    # AKILLI DOSYA BULMA
    file_path = _find_best_file_match_for_imports(query.strip())
    
    print(f"🧠 [CODE INTELLIGENCE] Akıllı arama: '{query}' → '{file_path}'")
    
    # 1. Dosyayı güvenli oku
    file_result = _safe_read_file(file_path)
    
    if file_result["status"] == "error":
        return f"""❌ **Dosya Okuma Hatası:**
        
**Dosya:** `{file_path}`
**Hata:** {file_result['message']}
**Tip:** {file_result['error_type']}

💡 **Çözüm Önerileri:**
- Dosya yolunun doğru olduğundan emin olun
- Dosyanın Python (.py) formatında olduğunu kontrol edin
- Dosya izinlerini kontrol edin"""

    # 2. Import'ları analiz et
    content = file_result["content"]
    import_result = _extract_imports_from_ast(content)
    
    if import_result["status"] == "error":
        return f"""❌ **Import Analizi Hatası:**
        
**Dosya:** `{file_path}`
**Hata:** {import_result['message']}

Dosya okunabildi ama import analizi başarısız oldu."""

    # 3. Güzel formatlanmış rapor oluştur
    imports = import_result["imports"]
    total_imports = import_result["total_imports"]
    
    report = f"""🧠 **Kod Zekası - Import Analizi**

📂 **Dosya:** `{file_path}`
📊 **Dosya Boyutu:** {file_result['file_size']} karakter  
📦 **Toplam Import:** {total_imports} adet
🔗 **Benzersiz Modül:** {len(imports['all_modules'])} adet

"""

    # Standard imports (import os, sys)
    if imports["standard_imports"]:
        report += f"""### 📋 **Standard Imports** ({len(imports["standard_imports"])} adet):
```python"""
        for imp in imports["standard_imports"]:
            alias_part = f" as {imp['alias']}" if imp['alias'] != imp['module'] else ""
            report += f"\nimport {imp['module']}{alias_part}  # satır {imp['line']}"
        report += "\n```\n\n"

    # From imports (from module import item)
    if imports["from_imports"]:
        report += f"""### 📥 **From Imports** ({len(imports["from_imports"])} adet):
```python"""
        for imp in imports["from_imports"]:
            alias_part = f" as {imp['alias']}" if imp['alias'] != imp['item'] else ""
            report += f"\nfrom {imp['module']} import {imp['item']}{alias_part}  # satır {imp['line']}"
        report += "\n```\n\n"

    # Relative imports (from .utils import helper)
    if imports["relative_imports"]:
        report += f"""### 🔗 **Relative Imports** ({len(imports["relative_imports"])} adet):
```python"""
        for imp in imports["relative_imports"]:
            alias_part = f" as {imp['alias']}" if imp['alias'] != imp['item'] else ""
            dots = "." * imp['level']
            module_part = imp['module'].replace("." * imp['level'], "", 1) if imp['module'] != "." * imp['level'] else ""
            if module_part:
                report += f"\nfrom {dots}{module_part} import {imp['item']}{alias_part}  # satır {imp['line']}"
            else:
                report += f"\nfrom {dots} import {imp['item']}{alias_part}  # satır {imp['line']}"
        report += "\n```\n\n"

    # Tüm modüller
    if imports["all_modules"]:
        report += f"""### 🎯 **Bağımlı Modüller** ({len(imports["all_modules"])} adet):
{', '.join(f'`{mod}`' for mod in imports["all_modules"])}

"""

    # Eğer hiç import yoksa
    if total_imports == 0:
        report += """### 📭 **Import Yok**
Bu dosyada herhangi bir import statement'ı bulunamadı.

"""

    report += """✅ **Analiz Tamamlandı!** Dosya başarıyla incelendi ve tüm bağımlılıklar tespit edildi."""
    
    print(f"✅ [CODE INTELLIGENCE] Analiz tamamlandı: {total_imports} import bulundu")
    return report

# Test fonksiyonu (geliştirme aşamasında kullanım için)
def _test_code_intelligence():
    """Code intelligence aracını test eder"""
    print("🧪 Code Intelligence Test Başlıyor...")
    
    # Test dosyası oluştur
    test_content = '''import os
import sys
from pathlib import Path
from typing import Dict, List
from .utils import helper_function
import requests as req

def test_function():
    pass
'''
    
    test_file = "test_code_intelligence.py"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    try:
        # Test et
        result = get_file_imports.invoke({"file_path": test_file})  
        print("✅ Test başarılı!")
        print(result)
    except Exception as e:
        print(f"❌ Test başarısız: {e}")
    finally:
        # Test dosyasını temizle
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    _test_code_intelligence()