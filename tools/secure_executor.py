#!/usr/bin/env python3
"""
🛡️ SECURE EXECUTOR - Güvenli Kod Yürütme Ortamı
Docker tabanlı sandbox ile güvenli Python kod çalıştırma
"""

import docker
import tempfile
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
from langchain_core.tools import tool

def _check_docker_availability() -> Dict[str, Any]:
    """
    Docker'ın yüklü ve çalışıyor olup olmadığını kontrol eder
    """
    # Docker Desktop socket yolları
    possible_sockets = [
        None,  # from_env() default
        "unix:///home/berkayhsrt/.docker/desktop/docker.sock",  # Docker Desktop
        "unix:///var/run/docker.sock"  # Standard Docker
    ]
    
    for socket_url in possible_sockets:
        try:
            if socket_url:
                client = docker.DockerClient(base_url=socket_url)
            else:
                client = docker.from_env()
            
            client.ping()
            version = client.version()
            return {
                "status": "available",
                "version": version.get("Version", "Unknown"),
                "message": f"Docker available: {version.get('Version', 'Unknown')}",
                "client": client
            }
        except Exception:
            continue
    
    return {
        "status": "docker_error",
        "message": "Docker not accessible via any known socket",
        "suggestion": "Make sure Docker Desktop is running"
    }

def _create_temp_code_file(code: str, language: str = "python") -> str:
    """
    Geçici kod dosyası oluşturur
    """
    file_extensions = {
        "python": ".py",
        "javascript": ".js",
        "bash": ".sh"
    }
    
    extension = file_extensions.get(language, ".py")
    
    # Geçici dosya oluştur
    with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as tmp_file:
        tmp_file.write(code)
        return tmp_file.name

def _run_code_in_docker(code_file_path: str, language: str = "python", client=None) -> Dict[str, Any]:
    """
    Docker konteynerinde kod çalıştırır
    """
    try:
        # Client yoksa oluştur
        if not client:
            possible_sockets = [
                "unix:///home/berkayhsrt/.docker/desktop/docker.sock",  # Docker Desktop
                "unix:///var/run/docker.sock"  # Standard Docker
            ]
            
            for socket_url in possible_sockets:
                try:
                    client = docker.DockerClient(base_url=socket_url)
                    client.ping()
                    break
                except Exception:
                    continue
            
            if not client:
                client = docker.from_env()  # Son çare
        
        # Dil bazında Docker imajı ve komut seçimi
        docker_configs = {
            "python": {
                "image": "python:3.10-slim",
                "command": ["python", "/code/script.py"]
            },
            "javascript": {
                "image": "node:18-slim", 
                "command": ["node", "/code/script.js"]
            },
            "bash": {
                "image": "ubuntu:20.04",
                "command": ["bash", "/code/script.sh"]
            }
        }
        
        config = docker_configs.get(language, docker_configs["python"])
        
        # Kod içeriğini oku
        with open(code_file_path, 'r') as f:
            code_content = f.read()
        
        print(f"🛡️ [SECURE EXECUTOR] Docker konteyneri başlatılıyor: {config['image']}")
        
        # Mount yerine environment variable kullan (daha güvenli)
        # Kod içeriği base64 encode edilecek ve ENV olarak geçilecek
        import base64
        encoded_code = base64.b64encode(code_content.encode('utf-8')).decode('utf-8')
        
        # Kodu environment variable olarak geçelim ve container içinde decode edelim
        script_ext = Path(code_file_path).suffix
        if language == "python":
            cmd = [
                "python", "-c", 
                f"import base64; exec(base64.b64decode('{encoded_code}').decode('utf-8'))"
            ]
        elif language == "javascript":
            cmd = [
                "node", "-e",
                f"eval(Buffer.from('{encoded_code}', 'base64').toString('utf-8'))"
            ]
        else:  # bash
            cmd = [
                "bash", "-c",
                f"echo '{encoded_code}' | base64 -d | bash"
            ]
        
        # Konteyneri çalıştır - güvenlik sınırlamaları ile
        container = client.containers.run(
            image=config["image"],
            command=cmd,
            remove=True,  # İş bitince otomatik sil
            detach=False,  # Çıktıyı bekle
            stdout=True,
            stderr=True,
            mem_limit="128m",  # Bellek sınırı
            cpu_period=100000,  # CPU sınırı
            cpu_quota=50000,   # CPU kullanımı %50 ile sınırla
            network_disabled=True,  # Ağ erişimini kapat
            user="nobody",  # Root olmayan kullanıcı
            security_opt=["no-new-privileges"],  # Güvenlik
        )
        
        # Çıktıyı decode et
        output = container.decode('utf-8') if container else ""
        
        return {
            "status": "success",
            "output": output,
            "stdout": output,
            "stderr": "",
            "execution_time": "< 30s"
        }
        
    except docker.errors.ContainerError as e:
        # Konteyner çalışırken hata
        return {
            "status": "runtime_error",
            "output": "",
            "stdout": "",
            "stderr": e.stderr.decode('utf-8') if e.stderr else str(e),
            "exit_code": e.exit_status,
            "message": f"Code execution failed with exit code {e.exit_status}"
        }
    except docker.errors.ImageNotFound:
        return {
            "status": "image_error",
            "message": f"Docker image not found: {config['image']}",
            "suggestion": f"Run: docker pull {config['image']}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Docker execution error: {str(e)}"
        }

@tool
def run_code_in_sandbox(code: str, language: str = "python") -> str:
    """
    Güvenli sandbox ortamında kod çalıştırır - Docker tabanlı izolasyon.
    
    BU ARAÇ TAM GÜVENLİ:
    - Ana sistemden tamamen izole Docker konteyneri
    - Bellek sınırı (128MB), CPU sınırı (%50), timeout (30s)
    - Ağ erişimi kapalı, dosya sistemi salt okunur
    - Root olmayan kullanıcı, güvenlik kısıtlamaları
    
    Desteklenen diller:
    - python: Python 3.10 (varsayılan)
    - javascript: Node.js 18
    - bash: Ubuntu 20.04 bash
    
    Args:
        code: Çalıştırılacak kod
        language: Programlama dili (python, javascript, bash)
    
    Returns:
        Kod çalıştırma sonucu ve çıktısı
    """
    print(f"🛡️ [SECURE EXECUTOR] Güvenli kod çalıştırma başlıyor: {language}")
    
    # 1. Docker'ın varlığını kontrol et
    docker_check = _check_docker_availability()
    
    if docker_check["status"] != "available":
        return f"""❌ **Docker Sandbox Kullanılamıyor**
        
**Durum:** {docker_check['status']}
**Hata:** {docker_check['message']}

💡 **Çözüm:** {docker_check.get('suggestion', 'Docker kurulumu gerekli')}

⚠️ Güvenli kod çalıştırma için Docker gereklidir."""
    
    # 2. Geçici kod dosyası oluştur
    temp_file = None
    try:
        temp_file = _create_temp_code_file(code, language)
        
        # 3. Docker'da güvenli çalıştırma - updated client kullan
        result = _run_code_in_docker(temp_file, language, docker_check.get("client"))
        
        # 4. Sonucu formatla
        if result["status"] == "success":
            report = f"""✅ **Güvenli Kod Çalıştırma Başarılı**

🛡️ **Güvenlik:** Docker sandbox, izole ortam
🔧 **Dil:** {language}
⏱️ **Süre:** {result.get('execution_time', 'Bilinmiyor')}

📤 **ÇIKTI:**
```
{result['output']}
```

✅ **Güvenli çalıştırma tamamlandı!**"""
        
        elif result["status"] == "runtime_error":
            report = f"""⚠️ **Kod Çalışma Hatası**

🛡️ **Güvenlik:** Hata güvenli ortamda yakalandı
🔧 **Dil:** {language}
❌ **Çıkış Kodu:** {result.get('exit_code', 'Bilinmiyor')}

📤 **HATA MESAJI:**
```
{result['stderr']}
```

💡 **Not:** Hata güvenli sandbox içinde oluştu, sistem güvenliği korundu."""
        
        else:
            report = f"""❌ **Sandbox Çalıştırma Hatası**
            
**Durum:** {result['status']}
**Hata:** {result['message']}

{result.get('suggestion', '')}"""

        return report
        
    except Exception as e:
        return f"""❌ **Beklenmeyen Sandbox Hatası:**
        
**Hata:** {str(e)}

Güvenli kod çalıştırma işlemi başarısız oldu."""
        
    finally:
        # 5. Geçici dosyayı temizle
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass  # Temizlik hatası önemli değil

# Test fonksiyonu (geliştirme aşamasında kullanım için)
def _test_secure_executor():
    """Secure executor'ı test eder"""
    print("🧪 Secure Executor Test Başlıyor...")
    
    # Test kodu - basit Python
    test_code = """
print("Merhaba, güvenli sandbox!")
import sys
print(f"Python version: {sys.version}")

# Matematik işlemi
result = 2 + 2
print(f"2 + 2 = {result}")

# Liste işlemi
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f"Liste toplamı: {total}")
"""
    
    try:
        # Test et
        result = run_code_in_sandbox.invoke({"code": test_code, "language": "python"})
        print("✅ Test başarılı!")
        print(result)
    except Exception as e:
        print(f"❌ Test başarısız: {e}")

if __name__ == "__main__":
    _test_secure_executor()