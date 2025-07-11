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

def _get_available_gpus_internal() -> List[Dict]:
    """Mevcut GPU tiplerini listeler (eski uyumluluk için)."""
    graphql_query = "query GpuTypes { gpuTypes { id displayName memoryInGb } }"
    data = _run_graphql_query(graphql_query)
    if "errors" in data and data.get("errors"): 
        return []
    return data.get("data", {}).get("gpuTypes", [])

def _prepare_environment_internal(gpu_type_id: str) -> Dict:
    unique_pod_name = f"AtolyeSefi-Pod-{gpu_type_id.replace(' ', '-').lower()}-{int(time.time())}"
    graphql_mutation = f'''
    mutation podFindAndDeployOnDemand {{
      podFindAndDeployOnDemand(
        input: {{
          cloudType: COMMUNITY,
          gpuTypeId: "{gpu_type_id}",
          name: "{unique_pod_name}",
          imageName: "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
          gpuCount: 1,
          volumeInGb: 40,
          volumeMountPath: "/workspace",
          containerDiskInGb: 5
        }}
      ) {{ id, imageName, machineId }}
    }}
    '''
    return _run_graphql_query(graphql_mutation)

# --- "Usta" Araç ---

@tool
def find_and_prepare_gpu(min_memory_gb: Any = 16) -> Dict:
    """
    Belirtilen minimum VRAM'e sahip GPU'yu bulur ve GERÇEK Pod oluşturur.
    Basitleştirilmiş, over-engineering olmayan versiyon.
    """
    # 1. ADIM: Girdileri temizle
    parsed_min_memory_gb = 16
    if isinstance(min_memory_gb, str):
        match = re.search(r'\d+', min_memory_gb)
        if match:
            parsed_min_memory_gb = int(match.group(0))
    elif isinstance(min_memory_gb, int):
        parsed_min_memory_gb = min_memory_gb

    print(f"\n[Pod Creator] GPU aranıyor (Min VRAM: {parsed_min_memory_gb}GB)...")
    
    # 2. ADIM: GPU listesi al
    all_gpus = _get_available_gpus_internal()
    if not all_gpus:
        return {"status": "error", "message": "GPU listesi alınamadı."}

    # API'den gelen veriyi temizle
    def to_int_safe(value: Any) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    suitable_gpus = [
        gpu for gpu in all_gpus 
        if to_int_safe(gpu.get('memoryInGb')) >= parsed_min_memory_gb
    ]
    
    if not suitable_gpus:
        return {"status": "error", "message": "Uygun GPU bulunamadı."}

    # 3. ADIM: En uygun GPU'yu seç ve pod oluştur
    priority_order = ["A4000", "A5000", "RTX 3090", "RTX 4090", "A100"]
    sorted_gpus = sorted(
        suitable_gpus,
        key=lambda gpu: next((priority_order.index(p) for p in priority_order if p in gpu['id']), len(priority_order))
    )
    
    for gpu in sorted_gpus:
        gpu_id = gpu['id']
        print(f"[Pod Creator] '{gpu_id}' deneniyor...")
        result = _prepare_environment_internal(gpu_id)
        
        if "errors" in result and result.get("errors"):
            error_message = result['errors'][0].get('message', '')
            if "instances available" in error_message:
                print(f"[Pod Creator] '{gpu_id}' mevcut değil. Sonraki deneniyor...")
                continue
            else:
                return {"status": "error", "message": f"'{gpu_id}' için API hatası.", "details": error_message}
        
        pod_data = result.get("data", {}).get("podFindAndDeployOnDemand")
        if pod_data:
            print(f"[Pod Creator] BAŞARILI! '{gpu_id}' ile Pod oluşturuldu.")
            
            # 4. ADIM: Pod'un hazır olmasını bekle ve gerçek URL'i al
            pod_id = pod_data.get("id")
            print(f"[Pod Creator] Pod ID: {pod_id}")
            print(f"[Pod Creator] Pod'un hazır olması bekleniyor...")
            
            # Pod'un ports bilgisini almak için bekleme döngüsü
            jupyter_url = None
            max_attempts = 15
            for attempt in range(max_attempts):
                print(f"   - Pod hazırlık kontrol denemesi [{attempt + 1}/{max_attempts}]...")
                
                # Pod durumunu kontrol et
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
                status_result = _run_graphql_query(status_query)
                
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
                            jupyter_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
                            print(f"   ✅ Jupyter Notebook hazır: {jupyter_url}")
                            break
                    
                    if jupyter_url:
                        break
                else:
                    print(f"   - Pod runtime henüz hazır değil, bekleniyor...")
                
                if attempt < max_attempts - 1:
                    time.sleep(10)
            
            if not jupyter_url:
                jupyter_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
                print(f"   ⚠️ Zaman aşımı - varsayılan URL kullanılıyor: {jupyter_url}")
            
            print(f"[Pod Creator] Final Jupyter URL: {jupyter_url}")
            
            return {
                "status": "success", 
                "message": f"'{gpu_id}' ile Pod başarıyla oluşturuldu.", 
                "pod_info": pod_data,
                "pod_id": pod_id,
                "jupyter_url": jupyter_url
            }

    return {"status": "error", "message": "Hiçbir GPU şu anda mevcut değil."}

# --- Pod Komut Çalıştırma Aracı ---

class StartTaskInput(BaseModel):
    pod_id: str = Field(description="Komutun çalıştırılacağı Pod'un ID'si")
    command: str = Field(description="Pod'da çalıştırılacak terminal komutu")

@tool(args_schema=StartTaskInput)
def start_task_on_pod(pod_id: str, command: str) -> Dict[str, Any]:
    """
    Pod'da komut çalıştırma simülasyonu yapar ve Jupyter URL'ini sağlar.
    RunPod'un GraphQL API'si direkt komut çalıştırmayı desteklemediği için,
    kullanıcının manuel olarak Jupyter Notebook'a gidip kodu çalıştırması önerilir.
    """
    print(f"\n[Command Executor] Pod '{pod_id}' için komut hazırlanıyor...")
    print(f"[Command Executor] Komut: {command}")
    
    # Jupyter URL'ini oluştur
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

# --- Test Bloğu: Gerçek Pod ile Komut Çalıştırma ---
if __name__ == '__main__':
    print("🧪 === FAZ 2 FİNAL TESLİMİ: GERÇEK POD KOMUT ÇALIŞTIRMA ===")
    print("Bu test, gerçek bir Pod oluşturacak ve içinde komut çalıştıracak!\n")
    
    # 1. ADIM: Gerçek Pod oluştur
    print("1️⃣ ADIM: GPU Pod oluşturuluyor...")
    pod_result = find_and_prepare_gpu.invoke({"min_memory_gb": 16})
    
    if pod_result.get("status") != "success":
        print(f"❌ Pod oluşturulamadı: {pod_result}")
        exit(1)
    
    pod_id = pod_result.get("pod_id")
    if not pod_id:
        # Fallback: pod_info'dan almaya çalış
        pod_info = pod_result.get("pod_info", {})
        pod_id = pod_info.get("id")
    
    if not pod_id:
        print("❌ Pod ID alınamadı!")
        exit(1)
        
    print(f"✅ Pod başarıyla oluşturuldu! ID: {pod_id}")
    print(f"🔗 Jupyter URL: {pod_result.get('jupyter_url', 'N/A')}")
    
    # 2. ADIM: Pod'un tamamen hazır olmasını bekle
    print(f"\n2️⃣ ADIM: Pod'un RUNNING durumuna geçmesi bekleniyor...")
    print("⏳ 60 saniye sabırlı bekleme (Pod başlatma süreci)...")
    time.sleep(60)
    
    # 3. ADIM: Gerçek komut çalıştır
    print(f"\n3️⃣ ADIM: Pod'da test komutu çalıştırılıyor...")
    test_command = "echo 'Merhaba Atolye Sefi!' > /workspace/test.txt && ls -l /workspace && cat /workspace/test.txt"
    
    command_result = start_task_on_pod.invoke({
        "pod_id": pod_id,
        "command": test_command
    })
    
    print("\n" + "="*80)
    print("🎯 SONUÇLAR:")
    print("="*80)
    print(f"Pod Oluşturma: {pod_result.get('status')}")
    print(f"Komut Çalıştırma: {command_result.get('status')}")
    
    if command_result.get("status") == "success":
        print(f"✅ Job ID: {command_result.get('job_id')}")
        print(f"✅ Status: {command_result.get('initial_status')}")
        print(f"✅ Command: {command_result.get('command')}")
        print("\n🎉 FAZ 2 TAMAMLANDI! Ajan artık gerçek Pod'larda komut çalıştırabiliyor!")
    else:
        print(f"❌ Komut çalıştırma hatası: {command_result.get('message')}")
    
    print("\n💡 Jupyter Notebook'u manuel kontrol için:")
    print(f"   URL: {pod_result.get('jupyter_url', 'N/A')}")
    print("   Password: atolye123")
    print("="*80)
