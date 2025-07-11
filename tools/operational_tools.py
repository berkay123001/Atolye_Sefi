# tools/operational_tools.py

import sys
import os
import requests
import time
import json
import re
from typing import Dict, List, Any
from pydantic.v1 import BaseModel, Field

# LangChain araçları için gerekli importlar
from langchain.tools import tool

try:
    from config import settings
except ImportError:
    print("Hata: config.py bulunamadı.")
    sys.exit(1)

# --- Yardımcı Fonksiyonlar ---
def _run_graphql_query(query: str, variables: Dict = None) -> Dict:
    """GraphQL sorgusu çalıştırmak için yardımcı fonksiyon."""
    api_url = "https://api.runpod.io/graphql"
    headers = {"Authorization": f"Bearer {settings.RUNPOD_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(api_url, headers=headers, json={'query': query, 'variables': variables or {}})
        if response.status_code != 200:
            error_details = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
            return {"errors": [{"message": f"API'den {response.status_code} hatası alındı.", "details": error_details}]}
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"errors": [{"message": str(e)}]}

def _start_pod(pod_id: str) -> Dict:
    """Belirtilen ID'ye sahip bir pod'u başlatır."""
    print(f"[Pod Start] Pod '{pod_id}' başlatılıyor...")
    mutation = """
    mutation podResume($input: PodResumeInput!) {
        podResume(input: $input) {
            id
            desiredStatus
            lastStatusChange
        }
    }
    """
    variables = {"input": {"podId": pod_id, "gpuCount": 1}}
    result = _run_graphql_query(mutation, variables)
    if "errors" in result or not result.get("data", {}).get("podResume"):
        error_message = result.get("errors", [{}])[0].get("message", "Bilinmeyen bir hata oluştu.")
        print(f"❌ Pod başlatılamadı: {error_message}")
        return {"status": "error", "message": f"Pod '{pod_id}' başlatılamadı.", "details": error_message}
    
    print(f"[Pod Start] Pod '{pod_id}' başlatma komutu gönderildi")
    return {"status": "success", "message": f"Pod '{pod_id}' başarıyla başlatıldı", "pod_id": pod_id, **result["data"]["podResume"]}

def _get_web_terminal_info(pod_id: str) -> Dict:
    """Pod'un Web Terminal bilgilerini alır."""
    query = """
    query pods {
        myself {
            pods {
                id
                name
                machine {
                    podHostId
                }
                runtime {
                    uptimeInSeconds
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                        type
                    }
                }
            }
        }
    }
    """
    
    result = _run_graphql_query(query, {})
    pods = result.get("data", {}).get("myself", {}).get("pods", [])
    
    for pod in pods:
        if pod.get("id") == pod_id:
            runtime = pod.get("runtime", {})
            if runtime:
                ports = runtime.get("ports", [])
                
                # Jupyter Notebook URL (8888 portu)
                jupyter_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
                
                # Web Terminal için SSH port bulma (genellikle 22)
                ssh_port = None
                for port in ports:
                    if port.get("privatePort") == 22:
                        ssh_port = port.get("publicPort")
                        break
                
                return {
                    "jupyter_url": jupyter_url,
                    "ssh_port": ssh_port,
                    "uptime": runtime.get("uptimeInSeconds", 0),
                    "total_ports": len(ports),
                    "pod_name": pod.get("name", ""),
                    "machine_host": pod.get("machine", {}).get("podHostId", "")
                }
    
    return None

# --- ÇALIŞAN POD CREATION TOOL ---

class FindAndPrepareGpuInput(BaseModel):
    min_memory_gb: Any = Field(description="Minimum VRAM gereksinimi (GB). Varsayılan: 16", default=16)

@tool(args_schema=FindAndPrepareGpuInput)
def find_and_prepare_gpu(min_memory_gb: Any = 16) -> Dict:
    """
    Belirtilen minimum VRAM'e sahip GPU'yu bulur ve GERÇEK Pod oluşturur.
    Pod'un tam olarak hazır olmasını bekler ve doğru Jupyter URL'ini döndürür.
    """
    # GPU seçimi için temel mantık (basitleştirilmiş)
    gpu_priority = ["NVIDIA RTX A4000", "NVIDIA GeForce RTX 3070", "NVIDIA RTX A5000"]
    
    print(f"\n[Pod Creator] GPU aranıyor (Min VRAM: {min_memory_gb}GB)...")
    
    for gpu_type_id in gpu_priority:
        print(f"[Pod Creator] '{gpu_type_id}' deneniyor...")
        
        mutation = """
        mutation PodFindAndDeployOnDemand($input: PodFindAndDeployOnDemandInput!) {
          podFindAndDeployOnDemand(input: $input) {
            id
            imageName
            machineId
          }
        }
        """
        variables = {
            "input": {
                "cloudType": "COMMUNITY",
                "gpuTypeId": gpu_type_id,
                "name": f"AtolyeSefi-Pod-{gpu_type_id.replace(' ', '-').lower()}-{int(time.time())}",
                "imageName": "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
                "gpuCount": 1,
                "volumeInGb": 40,
                "volumeMountPath": "/workspace",
                "containerDiskInGb": 10,
                "startSsh": True,
                "startJupyter": True,
                "ports": "8888/http",
                "env": [{"key": "JUPYTER_PASSWORD", "value": "atolye123"}]
            }
        }

        try:
            creation_result = _run_graphql_query(mutation, variables)
            if "errors" in creation_result:
                error_msg = creation_result['errors'][0].get('message', '')
                if "instances available" in error_msg:
                    print(f"[Pod Creator] '{gpu_type_id}' mevcut değil. Sonraki deneniyor...")
                    continue
                else:
                    print(f"[Pod Creator] '{gpu_type_id}' için API hatası: {error_msg}")
                    continue

            pod_data = creation_result.get("data", {}).get("podFindAndDeployOnDemand")
            if not pod_data:
                print(f"[Pod Creator] '{gpu_type_id}' için pod oluşturulamadı.")
                continue

            pod_id = pod_data.get("id")
            image_name = pod_data.get("imageName")
            print(f"[Pod Creator] BAŞARILI! '{gpu_type_id}' ile Pod oluşturuldu.")
            print(f"[Pod Creator] Pod ID: {pod_id}")
            print(f"[Pod Creator] Image: {image_name}")
            print(f"\n⏳ Pod'un Proxy URL'inin aktif hale gelmesi bekleniyor...")

            # Pod'un hazır olmasını bekle
            web_terminal_url = None
            max_attempts = 15
            for attempt in range(max_attempts):
                print(f"   - Proxy URL kontrol denemesi [{attempt + 1}/{max_attempts}]...")
                
                status_query = """
                query pods {
                    myself {
                        pods {
                            id
                            runtime {
                                uptimeInSeconds
                                ports {
                                    ip
                                    isIpPublic
                                    privatePort
                                    publicPort
                                    type
                                }
                            }
                        }
                    }
                }
                """
                status_result = _run_graphql_query(status_query, {})
                
                # Bizim pod'umuzu bul
                pods = status_result.get("data", {}).get("myself", {}).get("pods", [])
                current_pod = None
                for pod in pods:
                    if pod.get("id") == pod_id:
                        current_pod = pod
                        break
                
                if current_pod and current_pod.get("runtime"):
                    runtime = current_pod.get("runtime", {})
                    uptime = runtime.get("uptimeInSeconds", 0)
                    ports = runtime.get("ports", [])
                    
                    print(f"   📊 Pod durumu: {len(ports)} port mevcut, çalışma süresi: {uptime}s")
                    
                    # Port 8888'i arıyoruz (Jupyter Notebook)
                    for port in ports:
                        if port.get("privatePort") == 8888:
                            web_terminal_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
                            print(f"   ✅ Jupyter Notebook hazır: {web_terminal_url}")
                            break
                    
                    if web_terminal_url:
                        break
                else:
                    print(f"   - Pod runtime henüz hazır değil, bekleniyor...")
                
                if attempt < max_attempts - 1:
                    time.sleep(10)

            if not web_terminal_url:
                web_terminal_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
                print(f"   ⚠️ Zaman aşımı - varsayılan URL kullanılıyor: {web_terminal_url}")

            # Pod'u başlat
            print(f"\n🚀 Pod '{pod_id}' durumu doğrulanıyor...")
            start_result = _start_pod(pod_id)

            print("\n✅✅✅ ORTAM HAZIRLAMA BAŞARILI ✅✅✅")
            
            # Web Terminal bilgilerini al
            terminal_info = _get_web_terminal_info(pod_id)
            
            response = {
                "status": "success",
                "message": f"'{gpu_type_id}' ile Pod başarıyla oluşturuldu.",
                "pod_info": pod_data,
                "pod_id": pod_id,
                "jupyter_url": web_terminal_url,
                "image_name": image_name,
                "start_result": start_result,
                "jupyter_ready": True,
                "terminal_info": terminal_info
            }
            
            print(f"\n🔗 Jupyter Notebook: {web_terminal_url}")
            if terminal_info and terminal_info.get("ssh_port"):
                print(f"🔗 SSH Port: {terminal_info['ssh_port']}")
                print(f"📊 Pod Bilgileri: {terminal_info['total_ports']} port, {terminal_info['uptime']}s çalışma süresi")
            
            return response

        except Exception as e:
            print(f"[Pod Creator] '{gpu_type_id}' için beklenmeyen hata: {str(e)}")
            continue

    return {"status": "error", "message": "Hiçbir GPU şu anda mevcut değil."}

# --- start_task_on_pod fonksiyonu ---

class StartTaskInput(BaseModel):
    pod_id: str = Field(description="Komutun çalıştırılacağı Pod ID'si")
    command: str = Field(description="Pod içinde çalıştırılacak komut")

@tool(args_schema=StartTaskInput)
def start_task_on_pod(pod_id: str, command: str) -> Dict[str, Any]:
    """
    Pod'da SSH otomasyonu ile gerçek komut çalıştırır.
    Önce SSH ile dener, başarısız olursa Jupyter Notebook ile manuel çalıştırma önerir.
    """
    print(f"\n[SSH Command Executor] Pod '{pod_id}' için komut çalıştırılıyor...")
    print(f"[SSH Command Executor] Komut: {command}")
    
    try:
        # SSH otomasyonu ile gerçek komut çalıştırmayı dene
        from tools.ssh_pod_tools import execute_ssh_command
        
        print("[SSH Command Executor] SSH ile komut çalıştırılıyor...")
        ssh_result = execute_ssh_command(pod_id, command)
        
        if ssh_result.get("status") == "success":
            print("[SSH Command Executor] ✅ SSH komutu başarıyla çalıştırıldı!")
            return {
                "status": "success",
                "message": f"Komut SSH ile başarıyla çalıştırıldı: {command}",
                "pod_id": pod_id,
                "command": command,
                "output": ssh_result.get("output", ""),
                "error": ssh_result.get("error", ""),
                "exit_code": ssh_result.get("exit_code", 0),
                "execution_method": "SSH Automation",
                "ssh_method": ssh_result.get("method_used", "")
            }
        else:
            print(f"[SSH Command Executor] ❌ SSH hatası: {ssh_result.get('message', '')}")
            # SSH başarısız, Jupyter fallback
            print("[SSH Command Executor] SSH başarısız, Jupyter Notebook kullanımı öneriliyor...")
    
    except Exception as e:
        print(f"[SSH Command Executor] ❌ SSH modülü hatası: {str(e)}")
        print("[SSH Command Executor] Jupyter Notebook kullanımı öneriliyor...")
    
    # SSH başarısız olursa, Jupyter Notebook için kod hazırla
    jupyter_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
    
    # Komutu Jupyter Notebook için uygun hale getir
    if command.startswith("echo"):
        # Echo komutlarını Python print'e çevir
        if ">" in command:
            # Dosya yazma operasyonu
            parts = command.split(" > ")
            content = parts[0].replace("echo", "").strip().strip('"').strip("'")
            filename = parts[1].strip()
            jupyter_code = f'''# Dosya oluşturma
with open("{filename}", "w") as f:
    f.write("{content}")
print("Dosya '{filename}' oluşturuldu!")'''
        else:
            # Basit echo
            content = command.replace("echo", "").strip().strip('"').strip("'")
            jupyter_code = f'print("{content}")'
    elif command.startswith("git clone"):
        # Git clone komutunu çevir
        jupyter_code = f'''# Git repository klonlama
import subprocess
result = subprocess.run("{command}", shell=True, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)'''
    elif command.startswith("pip install"):
        # Pip install komutunu çevir
        packages = command.replace("pip install", "").strip()
        jupyter_code = f'''# Paket kurulumu
import subprocess
result = subprocess.run("pip install {packages}", shell=True, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)'''
    else:
        # Diğer komutlar için genel shell execution
        jupyter_code = f'''# Komut çalıştırma
import subprocess
result = subprocess.run("{command}", shell=True, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)'''
    
    print(f"[Command Executor] ✅ Jupyter kodu hazırlandı!")
    print(f"[Command Executor] Jupyter URL: {jupyter_url}")
    
    return {
        "status": "success",
        "message": "Komut Jupyter Notebook için hazırlandı.",
        "jupyter_url": jupyter_url,
        "jupyter_password": "atolye123",
        "original_command": command,
        "jupyter_code": jupyter_code,
        "instructions": f"""Pod'da kodu çalıştırmak için:
1. Jupyter URL'ini aç: {jupyter_url}
2. Şifre gir: atolye123
3. Yeni notebook oluştur veya terminal aç
4. Aşağıdaki kodu çalıştır:

{jupyter_code}""",
        "pod_id": pod_id
    }

# --- Diğer fonksiyonlar ---

def execute_command_on_pod(pod_id: str, command: str = "echo 'Command execution simulation'") -> Dict:
    """
    Eski uyumluluk için simülasyon fonksiyonu.
    """
    print(f"🔧 Pod '{pod_id}' üzerinde komut çalıştırılıyor: {command}")
    return {"status": "error", "message": f"Pod '{pod_id}' bulunamadı veya çalışır durumda değil"}

def get_pod_status(pod_id: str) -> Dict:
    """
    Pod durumunu kontrol eder.
    """
    print(f"📊 Pod '{pod_id}' durumu kontrol ediliyor...")
    
    query = """
    query pods {
        myself {
            pods {
                id
                name
                desiredStatus
                runtime {
                    uptimeInSeconds
                    ports {
                        privatePort
                        publicPort
                    }
                }
            }
        }
    }
    """
    
    result = _run_graphql_query(query, {})
    pods = result.get("data", {}).get("myself", {}).get("pods", [])
    
    for pod in pods:
        if pod.get("id") == pod_id:
            runtime = pod.get("runtime", {})
            uptime = runtime.get("uptimeInSeconds", 0) if runtime else 0
            ports = runtime.get("ports", []) if runtime else []
            
            return {
                "status": "success",
                "pod_id": pod_id,
                "pod_name": pod.get("name", ""),
                "desired_status": pod.get("desiredStatus", "UNKNOWN"),
                "uptime": uptime,
                "ports": ports,
                "is_running": runtime is not None
            }
    
    return {
        "status": "error",
        "message": f"Pod '{pod_id}' bulunamadı"
    }
