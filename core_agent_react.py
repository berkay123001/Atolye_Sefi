#!/usr/bin/env python3
"""
🧠 CORE AGENT - ReAct (Reason-Act-Observe) Architecture
Düşünen mühendis seviyesinde, çok adımlı problem çözme yeteneği
"""

import os
import sys
import json
import re
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# 1. ADIM: Kırılmaz LLM Bağlantısı
print("🧠 Core Agent ReAct başlatılıyor...")
print("1️⃣ LLM bağlantısı test ediliyor...")

try:
    from langchain_groq import ChatGroq
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, SystemMessage
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # API key kontrolü
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("❌ GROQ_API_KEY bulunamadı!")
        print("💡 .env dosyasında GROQ_API_KEY=your_key_here ekleyin")
        sys.exit(1)
    
    # LLM'i başlat
    llm = ChatGroq(
        model="llama3-70b-8192",
        temperature=0.1,
        groq_api_key=groq_api_key
    )
    
    # Test et
    test_response = llm.invoke([HumanMessage(content="test")])
    print("✅ LLM bağlantısı başarılı!")
    
except ImportError as e:
    print(f"❌ Kütüphane eksik: {e}")
    print("💡 Kurun: pip install langchain-groq python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"❌ LLM bağlantı hatası: {e}")
    print("💡 API anahtarınızı kontrol edin")
    sys.exit(1)

# 2. ADIM: Profesyonel Araçları Tanımla
print("2️⃣ Araçlar tanımlanıyor...")

# Import code intelligence and secure execution
from tools.code_intelligence import get_file_imports
from tools.code_quality import analyze_code_quality
from tools.secure_executor import run_code_in_sandbox
from tools.git_operations_simple import git_create_branch, git_commit_changes

@tool
def list_files_recursive(directory_path: str = ".") -> str:
    """
    Verilen dizindeki tüm dosyaları recursive olarak listeler.
    """
    try:
        target_path = Path(directory_path)
        if not target_path.exists():
            return f"❌ Dizin bulunamadı: {directory_path}"
        
        files = []
        for file_path in target_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(target_path)
                files.append(str(relative_path))
        
        if not files:
            return f"📁 Dizin boş: {directory_path}"
        
        result = f"📁 {directory_path} dizinindeki dosyalar ({len(files)} adet):\n"
        for file in sorted(files)[:20]:  # İlk 20 dosya
            result += f"  📄 {file}\n"
        
        if len(files) > 20:
            result += f"  ... ve {len(files) - 20} dosya daha\n"
        
        return result
        
    except Exception as e:
        return f"❌ Dosya listeleme hatası: {e}"

@tool  
def get_git_status(directory_path: str = ".") -> str:
    """
    Git repository durumunu kontrol eder ve formatlanmış rapor döndürür.
    """
    try:
        # GitPython'u direkt import et
        import git
        from git.exc import InvalidGitRepositoryError, GitCommandError
        from pathlib import Path
        
        # Dizin kontrolü
        target_path = Path(directory_path).resolve()
        if not target_path.exists():
            return f"❌ Dizin bulunamadı: {directory_path}"
        
        # Git repository'yi aç
        repo = git.Repo(target_path)
        
        # Temel bilgiler
        current_branch = repo.active_branch.name
        is_dirty = repo.is_dirty()
        
        # Değişiklikleri analiz et
        modified_files = []
        staged_files = []
        untracked_files = []
        
        # Modified files (working directory'de değişen)
        for item in repo.index.diff(None):
            modified_files.append(item.a_path)
        
        # Staged files (index'e eklenmiş)
        for item in repo.index.diff("HEAD"):
            staged_files.append(item.a_path)
        
        # Untracked files (takip edilmeyen)
        untracked_files = repo.untracked_files
        
        # Commit count
        try:
            commit_count = len(list(repo.iter_commits()))
            last_commit = repo.head.commit
            last_commit_message = last_commit.message.strip()
            last_commit_author = last_commit.author.name
        except:
            commit_count = 0
            last_commit_message = "Henüz commit yok"
            last_commit_author = "Unknown"
        
        # Formatlanmış rapor oluştur
        report = f"""📊 Git Durumu - {target_path}
🌿 Branch: {current_branch} | 📈 Commits: {commit_count}

💾 Son Commit: {last_commit_message[:50]}{'...' if len(last_commit_message) > 50 else ''}
👤 Yazar: {last_commit_author}

📝 Değişiklikler:"""

        if not is_dirty and not untracked_files:
            report += "\n✅ Working directory temiz - değişiklik yok"
        else:
            if staged_files:
                report += f"\n🟢 Staged ({len(staged_files)}): {', '.join(staged_files[:3])}"
                if len(staged_files) > 3:
                    report += f" ...+{len(staged_files) - 3}"
            
            if modified_files:
                report += f"\n🟡 Modified ({len(modified_files)}): {', '.join(modified_files[:3])}"
                if len(modified_files) > 3:
                    report += f" ...+{len(modified_files) - 3}"
            
            if untracked_files:
                report += f"\n🔴 Untracked ({len(untracked_files)}): {', '.join(untracked_files[:3])}"
                if len(untracked_files) > 3:
                    report += f" ...+{len(untracked_files) - 3}"
        
        return report
        
    except InvalidGitRepositoryError:
        return f"❌ '{directory_path}' bir Git repository değil. (git init ile oluşturabilirsin)"
    except ImportError:
        return "❌ GitPython kütüphanesi yüklü değil. (pip install GitPython)"
    except Exception as e:
        return f"❌ Git kontrol hatası: {e}"

# 3. ADIM: Dosya Yazma Aracı
@tool
def write_file(file_path: str, content: str) -> str:
    """
    Belirtilen dosya yoluna içerik yazar
    """
    try:
        import os
        from pathlib import Path
        
        # Dizin var mı kontrol et, yoksa oluştur
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Dosyayı yaz
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ **Dosya Yazıldı**\n\n📁 Dosya: `{file_path}`\n📊 Boyut: {len(content)} karakter\n\n💡 Dosya başarıyla kaydedildi."
        
    except Exception as e:
        return f"❌ **Dosya Yazma Hatası**\n\n{str(e)}"

# 4. ADIM: Execute Local Python - Veri İşleme Aracı (Helper metodunda implement edildi)
@tool
def execute_local_python(code: str) -> str:
    """
    Basit Python kodlarını lokal olarak çalıştırır - VERİ İŞLEME için kullanılır.
    
    Args:
        code: Çalıştırılacak Python kodu
    
    Returns:
        Kodun çıktısı veya sonucu
    
    Note: Bu araç execute_tool metodunda özel olarak handle ediliyor ve scratchpad erişimi sağlanıyor.
    """
    # Bu method aslında kullanılmıyor, execute_tool'da özel handle ediliyor
    return "Bu araç execute_tool metodunda handle ediliyor"

# 5. ADIM: Final Answer Aracı (ReAct Döngüsünü Sonlandırmak İçin)
@tool
def final_answer(answer: str) -> str:
    """
    Görev tamamlandığında final cevabı döndürür.
    """
    return f"✅ GÖREV TAMAMLANDI: {answer}"

# Araçları listele
tools = [list_files_recursive, get_git_status, get_file_imports, analyze_code_quality, run_code_in_sandbox, git_create_branch, git_commit_changes, write_file, execute_local_python, final_answer]
tool_names = [tool.name for tool in tools]

print("✅ Araçlar hazır:", tool_names)

# 4. ADIM: YENİ SİSTEM PROMPT'U - ReAct Architecture
REACT_SYSTEM_PROMPT = """🏆 ALTIN KURAL #1 (EN ÖNEMLİ): HER ŞEY SİCİLE GEÇMELİ - MUTLAK!
Herhangi bir araçtan (Gözlem) veri aldığında, bu veriyi MUTLAKA hafızaya (scratchpad) kaydet. Tüm sonuçlar, dosya listeleri, git durumları, analizler scratchpad'de saklanmalıdır. Sonraki adımlarda bu verileri kullanarak işlem yap.

🏆 ALTIN KURAL #2: TÜM CEVAPLARIN TÜRKÇE OLMALI - MUTLAK!
'Thought' adımların dahil, tüm düşünce sürecin ve nihai cevapların MUTLAKA Türkçe olmalıdır. Bu kuralı asla ihlal etme. İngilizce düşünme yasak!

**SCRATCHPAD HAFIZA SİSTEMİ:**
- `scratchpad['last_file_list']` - Son dosya listesi (list_files_recursive'den)
- `scratchpad['last_git_status']` - Son git durumu (get_git_status'dan)  
- `scratchpad['last_code_quality']` - Son kod kalitesi analizi
- `scratchpad['last_file_imports']` - Son bağımlılık analizi
- `scratchpad['project_files']` - Proje dosyalarının tam listesi

Sen, 'Atolye Şefi' adında uzman bir AI mühendisisin. Karmaşık görevleri çözmek için ÖNCE adım adım bir plan oluşturursun, sonra bu planı uygularsın.

KULLANABİLECEĞİN ARAÇLAR:
- list_files_recursive(directory_path): Verilen dizindeki tüm dosyaları recursive olarak listeler
- get_git_status(directory_path): Git repository durumunu kontrol eder ve formatlanmış rapor döndürür
- get_file_imports(query): Bir Python dosyasının bağımlılıklarını analiz eder - AKILLI: dağınık sorguları anlayabilir
- analyze_code_quality(query): Python dosyalarının kod kalitesini analiz eder - AKILLI: dağınık sorguları anlayabilir
- run_code_in_sandbox(code, language): Kodu güvenli Docker sandbox'ında çalıştırır - TAM GÜVENLİ: izole ortam
- git_create_branch(branch_name): Yeni git branch oluşturur ve o branch'e geçer
- git_commit_changes(message): Değişiklikleri stage'e ekler ve commit eder
- write_file(file_path, content): Belirtilen dosya yoluna içerik yazar
- execute_local_python(code): Basit Python kodlarını çalıştırır - VERİ İŞLEME için kullanılır
- Final Answer: Görevi başarıyla tamamladığında kullanırsın

🧠 STRATEJİK KURALLAR - PLAN-AND-EXECUTE:

📋 KURAL 1: ÖNCE PLANLA
Karmaşık bir görev aldığında, ilk düşüncen (Thought) MUTLAKA o görevi tamamlamak için gereken adımları listeleyen bir plan olmalıdır. Bu plan, hangi araçları hangi sırayla kullanacağını içermelidir. Hiçbir aracı çalıştırmadan önce planını açıkla.

⚡ KURAL 2: PLANI UYGULA  
Planını oluşturduktan sonra, her adımda o plandaki bir maddeyi uygula. Her eylemden sonra, planın hangi adımında olduğunu ve bir sonraki adımının ne olduğunu belirt.

✅ KURAL 3: GÖREVİ TAMAMLA
Plandaki tüm adımlar tamamlandığında VE elindeki bilgi kullanıcının orijinal görevini tamamen karşıladığında, görevi 'Final Answer' ile sonlandır.

⚠️ KURAL 4: SONSUZ DÖNGÜ ÖNLEMESİ
ASLA aynı aracı aynı argümanlarla tekrar çağırma. Her gözlemden sonra "Bu gözlem planımın hangi adımını tamamlıyor?" ve "Sıradaki adım ne?" sorularını sor.

🎯 KURAL 5: HEDEFLİ ANALİZ KURALI
Eğer kullanıcı 'kod kalitesini kontrol et' gibi genel istekler yaparsa ve belirli dosya belirtmezse, ASLA tüm projeyi tarama. Bunun yerine kullanıcıya 'Hangi dosyanın kod kalitesini analiz etmemi istiyorsun?' diye sor. analyze_code_quality aracı sadece belirli dosyalar için kullanılmalıdır.

📊 KURAL 6 (GÜÇLENDİRİLMİŞ): VERİYİ AKTAR VE İŞLE - KRİTİK!
Bir araçtan (Gözlem) bir sonuç (özellikle bir liste veya metin bloğu) aldığında, bu sonucu bir sonraki Düşünce adımında planını yapmak için kullanmalısın. Eğer bu veriyi filtrelemen veya işlemen gerekiyorsa, bir sonraki Eylem'in execute_local_python olmalıdır. 

**EN ÖNEMLİSİ:** execute_local_python aracını çağırırken, bir önceki Gözlem'deki veriyi doğrudan Python kodunun içine bir değişken olarak yerleştirmelisin.

**HATALI YAKLASIM:** `files = [...]` (belirsiz elipsis)
**DOĞRU YAKLASIM:** `files = ['main.py', 'config.json', 'utils.py']` (tam liste)

🏆 ALTIN KURAL: ÖNCE TEZGÂHA BAK VE SİSTEME GÜVEN - MUTLAK!
Bir görevi planlarken, özellikle dosya listesi, git durumu gibi veri gerektiğinde:

**YAPILMASI GEREKENLER:**
1. Düşüncende: "Bu veri daha önce elde edildi mi?" diye sor
2. Eğer evet ise: execute_local_python ile scratchpad'den kullan
3. Eğer hayır ise: İlgili aracı çağır - sistem OTOMATIK olarak sonucu hafızaya kaydedecek

**SCRATCHPAD HAFIZA:**
- `scratchpad['last_file_list']` - Son dosya listesi (list_files_recursive'den)
- `scratchpad['last_git_status']` - Son git durumu (get_git_status'dan)
- `scratchpad['last_code_quality']` - Son kod kalitesi analizi
- `scratchpad['last_file_imports']` - Son bağımlılık analizi

**ÖRNEK DOĞRU KULLANIM:**
```python
# Dosya listesi gerektiğinde:
execute_local_python("files = scratchpad['last_file_list']\npy_files = [f for f in files if '.py' in f]\nprint(len(py_files))")
```

CEVAP FORMATIN ŞU ŞEKİLDE OLMALIDIR:

Thought: (Burada ne yapmayı planladığını, görevi nasıl anladığını açıklarsın. Gözlem aldıysan: "Bu gözlem görevimi karşılıyor mu?" sorusunu cevapla.)
Action: 
```json
{
    "tool": "kullanacağın_aracın_adı",
    "tool_input": "araca_göndereceğin_parametre_veya_metin"
}
```

STRATEJİK ÖRNEKLER:

🔹 BASİT GÖREV (Tek Adım):
Kullanıcı: merhaba

Thought: Kullanıcı basit bir selamlama yaptı. Bu tek adımlık görev, plan gerektirmiyor. Final Answer ile cevap vereceğim.
Action:
```json
{
    "tool": "Final Answer",
    "tool_input": "Merhaba! Ben Atölye Şefi, size nasıl yardımcı olabilirim?"
}
```

🔹 KARMAŞIK GÖREV (Çok Adım):
Kullanıcı: Projedeki git aracının bağımlılıkları nelerdir?

Thought: Kullanıcı benden bir aracın bağımlılıklarını bulmamı istiyor. Bu çok adımlı bir görev, önce plan yapmalıyım:

📋 PLAN:
1. list_files_recursive aracını kullanarak projedeki tüm dosyaları bul
2. Dönen listede \"git\" ile ilgili Python dosyasını tespit et (muhtemelen 'tools/git_operations.py' gibi)
3. Tespit ettiğim dosya yoluyla get_file_imports aracını çalıştır
4. Aldığım sonucu kullanıcıya 'Final Answer' ile sun

Şimdi planımın 1. adımını uygulayacağım.

Action:
```json
{
    \"tool\": \"list_files_recursive\",
    \"tool_input\": {\"directory_path\": \".\"}
}
```

[Gözlem: 482 dosyalık liste alındı]

Thought: Dosya listesi aldım. KURAL 6'ya göre, bu büyük veriyi hemen başka bir araçla işleyemem. Önce bu veriyi anlamalı ve git ile ilgili dosyayı bulmalıyım. Listede 'tools/git_operations.py' gibi bir dosya arayacağım. Listede bu dosyayı gördüm, şimdi planımın 3. adımını uygulayacağım.

Action:
```json
{
    \"tool\": \"get_file_imports\",
    \"tool_input\": {\"query\": \"tools/git_operations.py\"}
}
```

Bu örnek, agent'a hem akıllı araç kullanımını hem de veri işleme adımını öğretir.

🔹 ÖRNEK SENARYO (OTOMATİK HAFIZA SİSTEMİ) - ALTIN STANDART:

Kullanıcı: Bu projede kaç tane Python dosyası var?

ADIM 1:
Thought: Plan: 1) Önce hafızaya bakacağım, 2) Gerekirse dosya listesi alacağım, 3) Python dosyalarını sayacağım. ALTIN KURAL'a göre önce scratchpad'i kontrol etmeliyim.
Action: { "tool": "execute_local_python", "tool_input": {"code": "if 'last_file_list' in scratchpad:\n    print('✅ Hafızada dosya listesi var')\n    print(f'Toplam dosya: {len(scratchpad[\"last_file_list\"])}')\nelse:\n    print('❌ Hafızada dosya listesi yok, yeni liste gerekli')"} }

ADIM 2:
Observation: ❌ Hafızada dosya listesi yok, yeni liste gerekli
Thought: Hafızada veri yok, dosya listesi almalıyım. Sistem otomatik olarak hafızaya kaydedecek.
Action: { "tool": "list_files_recursive", "tool_input": {"directory_path": "."} }

ADIM 3:  
Observation: 📁 . dizinindeki dosyalar (15 adet): 📄 core_agent_react.py 📄 mezuniyet_testi.py ...

💾 HAFIZA: Dosya listesi scratchpad['last_file_list']'e kaydedildi
Thought: Mükemmel! Sistem otomatik olarak dosya listesini hafızaya kaydetti. Şimdi scratchpad'deki veriyi kullanarak Python dosyalarını sayacağım.
Action: { "tool": "execute_local_python", "tool_input": {"code": "file_list = scratchpad['last_file_list']\npy_files = [f for f in file_list if f.endswith('.py')]\nprint(f'🐍 Python dosyası sayısı: {len(py_files)}')\nfor f in py_files[:5]:\n    print(f'  - {f}')"} }

ADIM 4:
Observation: 🐍 Python dosyası sayısı: 8 - core_agent_react.py - mezuniyet_testi.py ...
Thought: Artık kesin sayıyı biliyorum. Görevi tamamlayabilirim.
Action: { "tool": "final_answer", "tool_input": {"answer": "Bu projede **8 tane** Python dosyası var."} }

**BU ÖRNEK, OTOMATİK HAFIZA SİSTEMİNIN NASIL ÇALIŞTIĞINI ÖĞRETİR.**

🚨 KRİTİK HAFIZA KURALI:
execute_local_python kullanırken MUTLAKA `scratchpad['key']` formatında veri oku:
✅ DOĞRU: `file_list = scratchpad['last_file_list']`
❌ YANLIŞ: `file_list = file_list` (tanımsız değişken)

ÖNEMLİ: Karmaşık görevlerde ÖNCE plan yap, sonra adım adım uygula. Her gözlemden sonra hangi adımda olduğunu belirt."""

# 5. ADIM: ReAct Döngüsü Ana Sınıfı
class ReactAgent:
    def __init__(self):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.conversation_history = []
        
    def _sanitize_json_string(self, text: str) -> str:
        """LLM response'undan JSON için zararlı kontrol karakterlerini temizle"""
        # ASCII kontrol karakterlerini (0-31 arası, 127 hariç) temizle
        # Bu, JSON için geçersiz olan \n, \t gibi karakterleri korur
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1F\x7F]', '', text)
    
    def parse_llm_response(self, response_text: str) -> tuple:
        """LLM response'unu Thought ve Action olarak ayrıştır - Hijyen filtreli ve çok dilli"""
        
        # ADIM 1: Hijyen filtresini uygula
        clean_response_text = self._sanitize_json_string(response_text)
        
        # ADIM 2: Thought'u bul (Türkçe ve İngilizce destek)
        thought_match = re.search(r'(?:Thought|Düşünce):\s*(.*?)(?=Action:|Eylem:|$)', clean_response_text, re.DOTALL | re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else "Düşünce bulunamadı"
        
        # ADIM 3: Action'u bul - çok dilli ve esnek (Türkçe: Eylem, İngilizce: Action)
        action_match = re.search(r'(?:\*\*(?:Action|Eylem)\*\*|(?:Action|Eylem):)\s*```json\s*(.*?)\s*```', clean_response_text, re.DOTALL | re.IGNORECASE)
        
        if action_match:
            json_content = action_match.group(1).strip()
            
            # JSON temizlik - basit emoji ve kontrol karakter temizleme
            # Bilinen problemli karakterleri kaldır
            json_content = json_content.replace('✅', '').replace('❌', '').replace('🔍', '')
            json_content = json_content.replace('📄', '').replace('📁', '').replace('💾', '')
            
            # JSON'da hem eski hem yeni format destekle
            # Format 1: "code": "..."  
            # Format 2: {"code": "...}  (quotes eksik)
            
            if '"code":' in json_content or '{"code":' in json_content:
                # Önce {"code": "...} formatını düzelt
                if '{"code":' in json_content and json_content.count('"') < 6:
                    # Format 2: {"code": "...} -> "code": "..."
                    json_content = json_content.replace('{"code":', '"code":')
                    # Son } den önce " ekle
                    last_brace = json_content.rfind('}')
                    if last_brace != -1:
                        json_content = json_content[:last_brace] + '"' + json_content[last_brace:]
                
                # Şimdi standart format 1'i işle: "code": "..."
                start_idx = json_content.find('"code":')
                if start_idx != -1:
                    # "code": "... bul
                    quote_start = json_content.find('"', start_idx + 7)  # "code": den sonraki "
                    if quote_start != -1:
                        quote_end = json_content.rfind('"', quote_start + 1)  # Son "
                        if quote_end != -1 and quote_end > quote_start:
                            code_content = json_content[quote_start + 1:quote_end]
                            # Escape karakterleri - sıra önemli!
                            code_content = code_content.replace('\\', '\\\\')  # \ karakteri önce
                            code_content = code_content.replace('"', '\\"')   # " karakteri
                            code_content = code_content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                            # Yerine koy
                            json_content = json_content[:quote_start + 1] + code_content + json_content[quote_end:]
            
            # Son temizlik
            json_content = json_content.replace('\r\n', '\n').replace('\r', '\n')
            
            try:
                action_json = json.loads(json_content)
                
                # Final Answer araç ismini normalize et
                if action_json.get("tool") == "Final Answer":
                    action_json["tool"] = "final_answer"
                
                return thought, action_json
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse hatası: {e}")
                print(f"🔍 Ham JSON içeriği (tam): {repr(action_match.group(1))}")
                print(f"🔍 Temizlenmiş JSON içeriği (tam): {repr(json_content)}")
                
                # Tam JSON'u göstermek için dosyaya yaz
                with open('/tmp/debug_json.txt', 'w', encoding='utf-8') as f:
                    f.write(f"HAM:\n{action_match.group(1)}\n\nTEMİZLENMİŞ:\n{json_content}")
                # Basit dize değiştirme deneme
                try:
                    simple_json = json_content.replace('\✅', '').replace('\❌', '').encode('utf-8', 'ignore').decode('utf-8')
                    action_json = json.loads(simple_json)
                    return thought, action_json
                except:
                    # Fallback: metin analizi
                    return self._fallback_parse(response_text, thought)
        
        # Fallback parsing - eski format için
        return self._fallback_parse(response_text, thought)
    
    def _fallback_parse(self, response_text: str, thought: str) -> tuple:
        """Eski format veya hatalı JSON durumunda fallback parsing"""
        
        # Action satırını basit şekilde bul
        action_match = re.search(r'Action:\s*(.+?)(?=\n|$)', response_text, re.DOTALL | re.IGNORECASE)
        
        if action_match:
            action_text = action_match.group(1).strip()
            
            # JSON formatında mı kontrol et (fallback için)
            if action_text.startswith('{') and action_text.endswith('}'):
                try:
                    action_json = json.loads(action_text)
                    return thought, action_json
                except json.JSONDecodeError:
                    pass
            
            # Metin analizi ile araç tespiti
            if "final_answer" in action_text.lower() or "final answer" in action_text.lower():
                answer_match = re.search(r'(?:final_answer|final answer)[:\s]+(.+)', action_text, re.IGNORECASE)
                if answer_match:
                    return thought, {"tool": "final_answer", "tool_input": {"answer": answer_match.group(1).strip()}}
            
            if "list_files" in action_text.lower():
                return thought, {"tool": "list_files_recursive", "tool_input": {"directory_path": "."}}
            
            if "git_status" in action_text.lower() or "git" in action_text.lower():
                return thought, {"tool": "get_git_status", "tool_input": {"directory_path": "."}}
            
            if "get_file_imports" in action_text.lower():
                return thought, {"tool": "get_file_imports", "tool_input": {"file_path": "core_agent_react.py"}}
        
        # Son çare: Sonsuz döngü önleme - final_answer ver
        print("⚠️ Fallback: LLM belirsiz response verdi, görevi sonlandırıyorum")
        return thought, {"tool": "final_answer", "tool_input": {"answer": "Görev tamamlanamadı - LLM response belirsiz"}}
    
    def _invoke_llm_with_retry(self, messages, max_retries: int = 2) -> str:
        """LLM çağrısı dayanıklılık katmanı - API hatalarında retry mekanizması"""
        
        for attempt in range(max_retries):
            try:
                # LLM'i çağır
                response = self.llm.invoke(messages)
                return response.content
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # API hatalarını tespit et
                if any(keyword in error_msg for keyword in ['503', 'service unavailable', 'api', 'timeout', 'connection']):
                    if attempt < max_retries - 1:  # Son deneme değilse
                        print(f"🧠 API hatası algılandı: {e}")
                        print(f"⏳ 3 saniye sonra yeniden deniyorum... (Deneme {attempt + 2}/{max_retries})")
                        time.sleep(3)
                        continue
                    else:
                        # Final fallback - son deneme de başarısız
                        print(f"❌ API'ye ulaşılamıyor. Son deneme de başarısız: {e}")
                        raise Exception("API_CONNECTION_ERROR")
                else:
                    # API hatası değil, doğrudan yeniden fırlat
                    raise e
        
        # Bu satıra asla ulaşmamalı ama güvenlik için
        raise Exception("Beklenmeyen durum: Retry döngüsü tamamlandı ama sonuç yok")

    def _execute_local_python_with_scratchpad(self, code: str, scratchpad: dict) -> str:
        """execute_local_python aracını scratchpad ile çalıştır"""
        try:
            import io
            from contextlib import redirect_stdout
            
            # Çıktıyı yakala
            captured_output = io.StringIO()
            
            # Güvenlik: Sadece güvenli built-in'lere izin ver
            safe_builtins = {
                'print': print, 'len': len, 'str': str, 'int': int, 'float': float,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'sorted': sorted, 'enumerate': enumerate, 'range': range,
                'zip': zip, 'sum': sum, 'max': max, 'min': min,
                'any': any, 'all': all, 'filter': filter, 'map': map,
            }
            
            # Namespace oluştur (scratchpad dahil)
            namespace = {"__builtins__": safe_builtins, "scratchpad": scratchpad}
            
            with redirect_stdout(captured_output):
                exec(code, namespace)
            
            output = captured_output.getvalue()
            
            return f"✅ **Python Kodu Çalıştırıldı**\n\n📤 **ÇIKTI:**\n```\n{output.strip()}\n```"
            
        except Exception as e:
            return f"❌ **Python Çalıştırma Hatası**\n\n{str(e)}"

    def execute_tool(self, action: dict) -> str:
        """Aracı çalıştır ve sonucu döndür - Yeni format için optimize edildi"""
        
        tool_name = action.get("tool")
        tool_input = action.get("tool_input", {})
        
        if tool_name not in self.tools:
            return f"❌ Bilinmeyen araç: {tool_name}"
        
        try:
            tool = self.tools[tool_name]
            
            if tool_name == "final_answer":
                # Final answer için özel handling - string veya dict olabilir
                if isinstance(tool_input, str):
                    # Direkt string olarak verildi
                    answer = tool_input
                else:
                    # Dict olarak verildi
                    answer = tool_input.get("answer", str(tool_input))
                
                return tool.invoke({"answer": answer})
            elif tool_name == "execute_local_python":
                # Scratchpad parametresini handle et
                code = tool_input.get("code", "")
                scratchpad = action.get("scratchpad", {})
                
                # execute_local_python fonksiyonunu scratchpad ile çağır
                return self._execute_local_python_with_scratchpad(code, scratchpad)
            else:
                # Diğer araçlar için invoke
                result = tool.invoke(tool_input)
                return result
                
        except Exception as e:
            return f"❌ Araç çalıştırma hatası ({tool_name}): {e}"
    
    def run_react_loop(self, user_task: str, max_iterations: int = 10) -> str:
        """Ana ReAct döngüsü - Yeniden İnşa Edilmiş Hafıza Sistemi"""
        
        print(f"\n🎯 GÖREV BAŞLADI: {user_task}")
        print("=" * 60)
        
        # 1. ADIM: Gerçek Hafıza Mekanizması Kur
        scratchpad = {}
        print("🧠 Çalışma Tezgâhı (Scratchpad) hazırlandı")
        
        # Başlangıç mesajı
        messages = [
            SystemMessage(content=REACT_SYSTEM_PROMPT),
            HumanMessage(content=f"Görev: {user_task}")
        ]
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 ADIM {iteration}:")
            print("-" * 30)
            
            try:
                # LLM'den cevap al - Dayanıklılık katmanı ile
                response_text = self._invoke_llm_with_retry(messages)
                
                # Response'u parse et
                thought, action = self.parse_llm_response(response_text)
                
                # Düşünceyi göster
                print(f"🧠 Düşünce: {thought}")
                
                if not action:
                    print("❌ Eylem parse edilemedi. Döngü sonlandırılıyor.")
                    break
                
                print(f"⚡ Eylem: {action}")
                
                # Final answer kontrolü
                if action.get("tool") == "final_answer":
                    final_result = self.execute_tool(action)
                    print(f"\n{final_result}")
                    print("\n🏁 GÖREV TAMAMLANDI!")
                    return final_result
                
                # 2. ADIM: Aracı Çalıştır ve Sonucu Hafızaya Kaydet
                tool_name = action.get("tool", "")
                
                # execute_local_python için scratchpad'i geç
                if tool_name == "execute_local_python":
                    action_copy = action.copy()
                    action_copy["scratchpad"] = scratchpad
                    observation = self.execute_tool(action_copy)
                else:
                    observation = self.execute_tool(action)
                
                print(f"🔍 Gözlem: {observation}")
                
                # 3. ADIM: Otomatik Hafıza Kaydetme Refleksi
                memory_note = ""
                if tool_name == "list_files_recursive":
                    # list_files_recursive aracını tekrar çağır ama tam liste için
                    from pathlib import Path
                    directory_path = action.get("tool_input", {}).get("directory_path", ".")
                    target_path = Path(directory_path)
                    
                    # Tam dosya listesi oluştur
                    full_files = []
                    if target_path.exists():
                        for file_path in target_path.rglob("*"):
                            if file_path.is_file():
                                relative_path = file_path.relative_to(target_path)
                                full_files.append(str(relative_path))
                    
                    scratchpad['last_file_list'] = sorted(full_files)
                    memory_note = f"\n\n💾 HAFIZA: Dosya listesi scratchpad['last_file_list']'e kaydedildi ({len(full_files)} dosya)"
                    print(f"💾 Hafıza: dosya listesi kaydedildi ({len(full_files)} dosya)")
                elif tool_name == "get_git_status":
                    scratchpad['last_git_status'] = observation
                    memory_note = f"\n\n💾 HAFIZA: Git durumu scratchpad['last_git_status']'e kaydedildi"
                    print(f"💾 Hafıza: git durumu kaydedildi")
                elif tool_name == "analyze_code_quality":
                    scratchpad['last_code_quality'] = observation
                    memory_note = f"\n\n💾 HAFIZA: Kod kalitesi scratchpad['last_code_quality']'e kaydedildi"
                    print(f"💾 Hafıza: kod kalitesi kaydedildi")
                elif tool_name == "get_file_imports":
                    scratchpad['last_file_imports'] = observation
                    memory_note = f"\n\n💾 HAFIZA: Bağımlılıklar scratchpad['last_file_imports']'e kaydedildi"
                    print(f"💾 Hafıza: bağımlılıklar kaydedildi")
                
                # Conversation history'e ekle - hafıza notu dahil
                full_observation = observation + memory_note
                messages.append(HumanMessage(content=f"Observation: {full_observation}"))
                
            except Exception as e:
                # API bağlantı hatası için özel handling
                if str(e) == "API_CONNECTION_ERROR":
                    final_result = self.execute_tool({
                        "tool": "final_answer", 
                        "tool_input": {"answer": "❌ AI beynime (Groq API) ulaşırken bir sorun yaşıyorum. Lütfen birkaç dakika sonra tekrar deneyin. Sorun devam ederse sistem yöneticisine bildirin."}
                    })
                    print(f"\n{final_result}")
                    print("\n🏁 GÖREV API HATASI NEDENİYLE SONLANDIRILDI!")
                    return final_result
                else:
                    print(f"❌ Döngü hatası: {e}")
                    break
        
        return "⚠️ Maksimum iterasyon sayısına ulaşıldı. Görev tamamlanamadı."

# 6. ADIM: Ana Program ve Hoşgeldin Mesajı
def show_welcome():
    """ReAct Agent tanıtımı"""
    print("\n" + "="*70)
    print("🧠 CORE AGENT - ReAct (Reason-Act-Observe) Architecture")
    print("="*70)
    print("🎯 BEN KİMİM:")
    print("  • Atölye Şefi - Düşünen AI Mühendis")
    print("  • Çok adımlı görevleri çözebilirim")
    print("  • Her adımda düşüncelerimi paylaşırım")
    print("")
    print("🧠 NASIL ÇALIŞIRIM:")
    print("  1. 💭 Düşünürüm (Thought)")
    print("  2. ⚡ Eylem yaparım (Action)")  
    print("  3. 🔍 Sonucu gözlemlerim (Observation)")
    print("  4. 🔄 Bir sonraki adımı planlarım")
    print("")
    print("🛠️ ARAÇLARIM:")
    print("  • Dosya sistemi tarama")
    print("  • Git durumu analizi")
    print("  • Python kodu bağımlılık analizi")
    print("  • Python kod kalitesi analizi (Ruff)")
    print("  • Güvenli kod çalıştırma (Docker Sandbox)")
    print("  • Çok adımlı problem çözme")
    print("")
    print("📋 ÖRNEK GÖREVLER:")
    print("  • 'Projede .md dosyaları var mı ve git durumları nedir?'")
    print("  • 'core_agent.py dosyasının bağımlılıklarını analiz et'")
    print("  • 'tools/code_quality.py dosyasının kod kalitesini kontrol et'")
    print("  • 'Bu Python kodunu güvenli ortamda çalıştır: print(2+2)'")
    print("  • 'tools klasöründeki dosyaları listele'")
    print("  • 'Git durumunu kontrol et'")
    print("")
    print("💡 'exit' yazarak çıkabilirsin")
    print("="*70)

def main():
    """Ana program döngüsü"""
    show_welcome()
    
    # ReAct Agent'ı başlat
    agent = ReactAgent()
    
    print("\n🚀 ReAct Agent hazır!")
    
    while True:
        try:
            # Kullanıcı görevini al
            user_task = input("\n🧠 ReAct> ").strip()
            
            # Çıkış kontrolü
            if user_task.lower() in ['exit', 'quit', 'çıkış']:
                print("👋 ReAct Agent kapatılıyor...")
                break
            
            # Boş girdi kontrolü
            if not user_task:
                print("⚠️ Bir görev verin veya 'exit' ile çıkın")
                continue
            
            # ReAct döngüsünü başlat
            result = agent.run_react_loop(user_task)
            
        except KeyboardInterrupt:
            print("\n\n👋 ReAct Agent interrupted - Çıkılıyor...")
            break
        except Exception as e:
            print(f"\n❌ Beklenmeyen hata: {e}")
            print("🔄 Devam ediyor...")

if __name__ == "__main__":
    main()