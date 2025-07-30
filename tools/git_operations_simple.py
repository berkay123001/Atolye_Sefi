#!/usr/bin/env python3
"""
🔧 Git Operations - Simple & Professional
Core Agent için basit ve güvenilir Git araçları
"""

import os
import subprocess
from typing import Dict, List
from pathlib import Path
from langchain_core.tools import tool

try:
    import git
    from git.exc import InvalidGitRepositoryError, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("⚠️ GitPython not installed. Run: pip install GitPython")

def get_git_status(directory_path: str = ".") -> str:
    """
    Git repository durumunu kontrol eder ve formatlanmış rapor döndürür.
    
    Args:
        directory_path: Kontrol edilecek dizin yolu (varsayılan: mevcut dizin)
    
    Returns:
        Formatlanmış Git durumu raporu
    """
    if not GIT_AVAILABLE:
        return "❌ GitPython kütüphanesi yüklü değil. Kurmak için: pip install GitPython"
    
    try:
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
    
    except Exception as e:
        return f"❌ Beklenmeyen Git hatası: {str(e)}\n💡 Dizin izinlerini ve Git durumunu kontrol edin"

@tool
def git_create_branch(branch_name: str) -> str:
    """
    Yeni git branch oluşturur ve o branch'e geçer
    
    Args:
        branch_name: Oluşturulacak branch adı
    
    Returns:
        İşlem sonucu mesajı
    """
    try:
        # Yeni branch oluştur ve geç
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            text=True,
            cwd=".",
            timeout=30
        )
        
        if result.returncode == 0:
            return f"✅ **Branch Oluşturuldu**\n\n🌿 Yeni branch '{branch_name}' başarıyla oluşturuldu ve aktif edildi.\n\n💡 Artık bu branch'te çalışıyorsunuz."
        else:
            return f"❌ **Branch Oluşturma Hatası**\n\n{result.stderr}\n\n💡 Branch adının geçerli olduğundan ve aynı isimde branch olmadığından emin olun."
            
    except Exception as e:
        return f"❌ **Git İşlem Hatası**\n\n{str(e)}\n\n💡 Git kurulu olduğundan ve repository içinde olduğunuzdan emin olun."

@tool 
def git_commit_changes(message: str) -> str:
    """
    Değişiklikleri stage'e ekler ve commit eder
    
    Args:
        message: Commit mesajı
    
    Returns:
        İşlem sonucu mesajı
    """
    try:
        # Tüm değişiklikleri stage'e ekle
        add_result = subprocess.run(
            ["git", "add", "."],
            capture_output=True,
            text=True,
            cwd=".",
            timeout=30
        )
        
        if add_result.returncode != 0:
            return f"❌ **Git Add Hatası**\n\n{add_result.stderr}"
        
        # Commit et
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            cwd=".",
            timeout=30
        )
        
        if commit_result.returncode == 0:
            return f"✅ **Commit Başarılı**\n\n📝 Değişiklikler commit edildi: '{message}'\n\n💡 Değişiklikleriniz Git geçmişine kaydedildi."
        else:
            return f"❌ **Commit Hatası**\n\n{commit_result.stderr}\n\n💡 Commit edilecek değişiklik olduğundan emin olun."
            
    except Exception as e:
        return f"❌ **Git Commit Hatası**\n\n{str(e)}"

# Test fonksiyonu
def test_git_operations():
    """Git operations test fonksiyonu"""
    print("🧪 Testing Git Operations...")
    
    # Mevcut dizini test et
    result = get_git_status(".")
    print("📊 Test Result:")
    print(result)

if __name__ == "__main__":
    test_git_operations()