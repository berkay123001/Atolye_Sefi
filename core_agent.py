#!/usr/bin/env python3
"""
🌱 CORE AGENT - Sıfır Yalan Prensibiyle İnşa Edilmiş
Basit, kırılmaz, şeffaf. Sadece bir işi mükemmel yapar.

PRENSIP: Her adım görünür, her hata açık, hiçbir abartı yok.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

# 1. ADIM: Kırılmaz LLM Bağlantısı
print("🌱 Core Agent başlatılıyor...")
print("1️⃣ LLM bağlantısı test ediliyor...")

try:
    from langchain_groq import ChatGroq
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage
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
    test_response = llm.invoke([HumanMessage(content="merhaba")])
    print("✅ LLM bağlantısı başarılı!")
    
except ImportError as e:
    print(f"❌ Kütüphane eksik: {e}")
    print("💡 Kurun: pip install langchain-groq python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"❌ LLM bağlantı hatası: {e}")
    print("💡 API anahtarınızı kontrol edin")
    sys.exit(1)

# 2. ADIM: İki Profesyonel Araç Tanımla  
print("2️⃣ Araçlar tanımlanıyor...")

@tool
def list_files_recursive(directory_path: str = ".") -> str:
    """
    Kullanıcı AÇIKÇA dosya veya dizinleri listelememi istediğinde, bu aracı kullanarak 
    belirtilen yoldaki tüm dosyaları ve klasörleri listeler. 
    Sadece dosya listeleme talepleri için kullanılmalıdır.
    
    Args:
        directory_path: Listelenecek dizin yolu (varsayılan: mevcut dizin)
    
    Returns:
        Dosya listesi string formatında
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
    Kullanıcı AÇIKÇA Git durumunu, repository bilgilerini veya değişiklikleri 
    sorduğunda bu aracı kullanarak Git repository durumunu kontrol eder.
    Sadece Git ile ilgili talepler için kullanılmalıdır.
    
    Args:
        directory_path: Kontrol edilecek dizin yolu (varsayılan: mevcut dizin)
    
    Returns:
        Formatlanmış Git durumu raporu
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
        report = f"""📊 **Git Durumu Raporu**
        
📁 **Dizin:** {target_path}
🌿 **Branch:** {current_branch}
📈 **Toplam Commit:** {commit_count}

💾 **Son Commit:**
   • Mesaj: {last_commit_message[:50]}{'...' if len(last_commit_message) > 50 else ''}
   • Yazar: {last_commit_author}

📝 **Değişiklikler:**"""

        if not is_dirty and not untracked_files:
            report += "\n   ✅ Working directory temiz - değişiklik yok"
        else:
            if staged_files:
                report += f"\n   🟢 Staged dosyalar ({len(staged_files)} adet):"
                for file in staged_files[:5]:  # İlk 5 tanesi
                    report += f"\n      • {file}"
                if len(staged_files) > 5:
                    report += f"\n      ... ve {len(staged_files) - 5} dosya daha"
            
            if modified_files:
                report += f"\n   🟡 Modified dosyalar ({len(modified_files)} adet):"
                for file in modified_files[:5]:  # İlk 5 tanesi
                    report += f"\n      • {file}"
                if len(modified_files) > 5:
                    report += f"\n      ... ve {len(modified_files) - 5} dosya daha"
            
            if untracked_files:
                report += f"\n   🔴 Untracked dosyalar ({len(untracked_files)} adet):"
                for file in untracked_files[:5]:  # İlk 5 tanesi
                    report += f"\n      • {file}"
                if len(untracked_files) > 5:
                    report += f"\n      ... ve {len(untracked_files) - 5} dosya daha"
        
        report += f"\n\n💡 **Özet:** {'Temiz repository' if not is_dirty and not untracked_files else 'Değişiklikler mevcut'}"
        
        return report
        
    except InvalidGitRepositoryError:
        return f"❌ '{directory_path}' bir Git repository değil.\n💡 Git repository oluşturmak için: git init"
    
    except GitCommandError as e:
        return f"❌ Git komutu hatası: {str(e)}\n💡 Git kurulu olduğundan ve erişilebilir olduğundan emin olun"
    
    except ImportError:
        return "❌ GitPython kütüphanesi yüklü değil.\n💡 Kurmak için: pip install GitPython"
    
    except Exception as e:
        return f"❌ Git kontrol hatası: {e}\n💡 GitPython kurulu olduğundan emin olun: pip install GitPython"

# 3. ADIM: LLM'e Aracı Öğret
print("3️⃣ LLM'e araç bağlanıyor...")

try:
    # İki aracı LLM'e bağla
    tools = [list_files_recursive, get_git_status]
    llm_with_tools = llm.bind_tools(tools)
    print("✅ Araçlar başarıyla bağlandı!")
except Exception as e:
    print(f"❌ Araç bağlama hatası: {e}")
    sys.exit(1)

# 5. ADIM: Dürüst Çekirdek Mantığı
def process_user_input(user_input: str) -> str:
    """
    Kullanıcı girdisini işle - tam şeffaflıkla
    """
    try:
        # SMART PRE-FILTERING: Basit sohbet sorularını tespit et
        chat_keywords = ['merhaba', 'selam', 'orda mısın', 'nasılsın', 'hello', 'hi', 'hey']
        simple_questions = ['naber', 'ne yapıyorsun', 'kimsin', 'adın ne']
        
        user_lower = user_input.lower()
        is_simple_chat = any(keyword in user_lower for keyword in chat_keywords + simple_questions)
        
        if is_simple_chat:
            print("💬 Basit sohbet - doğal konuşuyorum")
            # Araçsız LLM kullan
            response = llm.invoke([HumanMessage(content=f"Atölye Şefi olarak doğal ve profesyonel cevap ver: {user_input}")])
            return response.content
        
        # Dosya/Git keywords varsa tool kullan
        file_keywords = ['dosya', 'klasör', 'dizin', 'listele', 'göster', 'file', 'folder', 'list']
        git_keywords = ['git', 'commit', 'branch', 'repository', 'repo', 'değişiklik', 'status', 'durumu', 'proje durumu']
        
        needs_file_tool = any(keyword in user_lower for keyword in file_keywords)
        needs_git_tool = any(keyword in user_lower for keyword in git_keywords)
        
        if not needs_file_tool and not needs_git_tool:
            print("💬 Normal sohbet - doğal konuşuyorum")
            
            # Normal sohbet için sistem kuralları
            system_message = """Sen 'Atölye Şefi' adında, tecrübeli, kendine güvenen ve pratik çözümler üreten bir başmühendissin. 

İletişim kurarken şu kurallara uy:

1. Doğal ve Akıcı Ol: Cevapların robotik olmasın. Bir insanla konuşur gibi, doğal ve akıcı bir dil kullan.

2. Direkt ve Profesyonel Ol: Basit sohbet sorularına ("nasılsın", "orda mısın" gibi) "Ben bir yapay zekayım..." gibi felsefi cevaplar verme. Bunun yerine, "Buradayım, seni dinliyorum. Görev nedir?" veya "Hazır ve görev bekliyorum." gibi direkt ve profesyonel cevaplar ver.

Sadece sohbet cevabı ver, hiçbir araç kullanma."""
            
            from langchain_core.messages import SystemMessage
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_input)
            ]
            response = llm.invoke(messages)
            return response.content
        
        print("🔧 Araç kullanarak yardım ediyorum")
        
        # ADIM 1: Sistem Prompt'u ile LLM'e net kurallar ver
        system_message = """Sen 'Atölye Şefi' adında, tecrübeli, kendine güvenen ve pratik çözümler üreten bir başmühendissin. Görevin, kullanıcının mühendislik görevlerini araçlarınla yerine getirmektir.

İletişim kurarken şu kurallara uy:

1. Doğal ve Akıcı Ol: Cevapların robotik olmasın. Bir insanla konuşur gibi, doğal ve akıcı bir dil kullan. Felsefi veya aşırı ansiklopedik cevaplardan kaçın.

2. Önce Özet, Sonra Detay: Bir veri listesi veya teknik bir çıktı sunmadan önce, her zaman bir giriş cümlesiyle ne söyleyeceğini özetle.
   ❌ YANLIŞ: (Direkt dosya listesini dökmek)
   ✅ DOĞRU: "Evet, projede birkaç değişiklik tespit ettim. İşte detaylar:" (Sonra listeyi dök)

3. Sahiplenici Konuş: Bir araç kullandığında, "LLM bir araç kullanmaya karar verdi" gibi pasif ifadeler kullanma. Bunun yerine, "Tamam, projenin Git durumunu kontrol ediyorum..." veya "Anlaşıldı, dosya sistemini tarıyorum..." gibi eylemi sahiplenen, aktif bir dil kullan.

ARAÇ KULLANIM KURALLARI:
- Dosya listeleme talebi → list_files_recursive aracını kullan
- Git durumu talebi → get_git_status aracını kullan
- Basit sohbet → Araç kullanma, doğal konuş"""

        from langchain_core.messages import SystemMessage
        
        # LLM'e sor (sistem kuralları + araçlarla beraber)
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_input)
        ]
        response = llm_with_tools.invoke(messages)
        
        # Tool kullanımı var mı kontrol et
        if hasattr(response, 'tool_calls') and response.tool_calls:
            results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Sahiplenici mesajlar
                if tool_name == "get_git_status":
                    print("🔍 Git durumunu kontrol ediyorum...")
                elif tool_name == "list_files_recursive":
                    print("📁 Dosya sistemini tarıyorum...")
                else:
                    print(f"🛠️ {tool_name} aracını kullanıyorum...")
                
                # Aracı çalıştır
                if tool_name == "list_files_recursive":
                    result = list_files_recursive.invoke(tool_args)
                    results.append(result)
                elif tool_name == "get_git_status":
                    result = get_git_status.invoke(tool_args)
                    results.append(result)
                else:
                    results.append(f"❌ Bilinmeyen araç: {tool_name}")
            
            return "\n".join(results)
        
        else:
            # Sadece sohbet cevabı - sistem prompt kuralları uygulansın
            return response.content
            
    except Exception as e:
        return f"❌ İşlem hatası: {e}"

# 6. ADIM: Beklenti Yönetimi
def show_welcome():
    """
    Dürüst hoşgeldin mesajı
    """
    print("\n" + "="*60)
    print("🌱 CORE AGENT - Sıfır Yalan Prensibi")
    print("="*60)
    print("🎯 BEN NE YAPABİLİRİM:")
    print("  • Dosya listesi çıkartabilirim (recursive)")
    print("  • Git durumunu kontrol edebilirim")
    print("  • Basit sohbet edebilirim")
    print("  • Bu kadar! Başka hiçbir şey yapmam")
    print("")
    print("🔍 ÖRNEK KOMUTLAR:")
    print("  • 'mevcut dizindeki dosyaları listele'")
    print("  • 'workspace klasöründeki dosyaları göster'")
    print("  • 'git durumunu kontrol et'")
    print("  • 'projede değişiklik var mı'")
    print("  • 'merhaba'")
    print("")
    print("⚠️  YAPAMADIKUM ŞEYLER:")
    print("  • Dosya oluşturma/düzenleme")
    print("  • Kod çalıştırma")
    print("  • Git commit/push işlemleri")
    print("  • Başka hiçbir 'akıllı' özellik")
    print("")
    print("💡 'exit' yazarak çıkabilirsin")
    print("="*60)

# 4. ADIM: Agent Yaşam Döngüsü
def main():
    """
    Ana program döngüsü - basit ve net
    """
    show_welcome()
    
    print("\n🚀 Core Agent hazır!")
    
    while True:
        try:
            # Kullanıcı girdisi al
            user_input = input("\n🌱 Core> ").strip()
            
            # Çıkış kontrolü
            if user_input.lower() in ['exit', 'quit', 'çıkış']:
                print("👋 Core Agent kapatılıyor...")
                break
            
            # Boş girdi kontrolü
            if not user_input:
                print("⚠️ Bir şeyler yazın veya 'exit' ile çıkın")
                continue
            
            # İşle ve cevapla
            print(f"\n🔄 İşleniyor: {user_input}")
            response = process_user_input(user_input)
            print(f"\n📝 Cevap:\n{response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Core Agent interrupted - Çıkılıyor...")
            break
        except Exception as e:
            print(f"\n❌ Beklenmeyen hata: {e}")
            print("🔄 Devam ediyor...")

if __name__ == "__main__":
    main()