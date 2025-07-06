import os
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

# .env dosyasındaki RUNPOD_API_KEY'i yükle
load_dotenv()
API_KEY = os.getenv("RUNPOD_API_KEY")
GRAPHQL_URL = "https://api.runpod.io/graphql"

if not API_KEY:
    raise ValueError("RUNPOD_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin.")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def _run_graphql_query(query: str, variables: Dict = None) -> Dict:
    """GraphQL sorgusu çalıştırmak için yardımcı fonksiyon."""
    try:
        response = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables or {}}, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"GraphQL isteği sırasında hata: {e}")
        if e.response:
            print(f"Hata Detayı: {e.response.text}")
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

class PrepareEnvironmentInput(BaseModel):
    gpu_type_id: str = Field(description="Oluşturulacak Pod için GPU tipi ID'si. Örneğin: 'NVIDIA GeForce RTX 3070'")

@tool(args_schema=PrepareEnvironmentInput)
def prepare_environment_with_ssh(gpu_type_id: str) -> Dict[str, Any]:
    """
    Pod oluşturur, HAZIR OLMASINI BEKLER ve yeni Proxy URL'ini alarak başlatır.
    Önce pod'u oluşturur, ardından Web Terminal için doğru proxy URL aktif olana kadar periyodik olarak kontrol eder.
    """
    print(f"\n[Pod Management] Pod oluşturuluyor...")
    print(f"🔑 GPU Type: {gpu_type_id}")

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
            "name": f"atolye-sefi-final-{int(time.time())}",
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
            return {"status": "error", "message": f"Pod oluşturma hatası: {creation_result['errors'][0].get('message')}"}

        pod_data = creation_result.get("data", {}).get("podFindAndDeployOnDemand")
        if not pod_data:
            return {"status": "error", "message": "Pod oluşturulamadı - uygun GPU bulunamamış olabilir."}

        pod_id = pod_data.get("id")
        image_name = pod_data.get("imageName")
        print(f"✅ Pod temel kaydı oluşturuldu! ID: {pod_id}")
        print(f"🖼️  Image: {image_name}")
        print(f"\n⏳ Pod'un Proxy URL'inin aktif hale gelmesi bekleniyor...")

        web_terminal_url = None
        max_attempts = 15
        for attempt in range(max_attempts):
            print(f"   - Proxy URL kontrol denemesi [{attempt + 1}/{max_attempts}]...")
            
            # Düzeltilmiş GraphQL sorgusu - pods listesi üzerinden ID ile arama
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
            
            # Pods listesinden bizim pod'umuzu bulalım
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
                jupyter_url = None
                for port in ports:
                    if port.get("privatePort") == 8888:
                        # Jupyter için doğru URL formatı
                        jupyter_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
                        print(f"   ✅ Jupyter Notebook hazır: {jupyter_url}")
                        break
                
                # Şimdilik Jupyter URL'ini web_terminal_url olarak kullanıyoruz
                if jupyter_url:
                    web_terminal_url = jupyter_url
            if web_terminal_url:
                print(f"   ✅ Çalışan Proxy URL başarıyla bulundu!")
                break
            else:
                print(f"   - Proxy URL (port 8888) henüz hazır değil, bekleniyor...")
                if attempt < max_attempts - 1:
                     time.sleep(15)

        if not web_terminal_url:
            return {"status": "error", "message": "Zaman aşımı: Web Terminal için Proxy URL hazır hale gelmedi."}
        
        print(f"\n🚀 Pod '{pod_id}' durumu doğrulanıyor...")
        start_result = _start_pod(pod_id)

        print("\n✅✅✅ ORTAM HAZIRLAMA BAŞARILI ✅✅✅")
        
        # Web Terminal bilgilerini al
        terminal_info = _get_web_terminal_info(pod_id)
        
        response = {
            "status": "success",
            "message": "Pod başarıyla oluşturuldu, başlatıldı ve Jupyter Notebook hazır.",
            "pod_id": pod_id,
            "image_name": image_name,
            "start_result": start_result,
            "jupyter_url": web_terminal_url,
            "jupyter_ready": True,
            "terminal_info": terminal_info
        }
        
        print(f"\n🔗 Jupyter Notebook: {web_terminal_url}")
        if terminal_info and terminal_info.get("ssh_port"):
            print(f"🔗 SSH Port: {terminal_info['ssh_port']}")
            print(f"📊 Pod Bilgileri: {terminal_info['total_ports']} port, {terminal_info['uptime']}s çalışma süresi")
        
        return response

    except Exception as e:
        return {"status": "error", "message": f"Pod hazırlama sırasında beklenmedik bir hata oluştu: {str(e)}"}

def main_test():
    """Ana test fonksiyonu."""
    print("================================================================================")
    print("🧪 WEB TERMINAL TABANLI POD MANAGEMENT ARAÇLARI - TAM TEST BAŞLIYOR")
    print("================================================================================")

    print("\n1️⃣ ADIM: Pod oluşturuluyor ve Web Terminal bilgilerinin hazır olması bekleniyor...")
    
    gpu_to_test = "NVIDIA GeForce RTX 3070" 
    
    result = prepare_environment_with_ssh.invoke({"gpu_type_id": gpu_to_test})

    print("\n---------------------- SONUÇ ----------------------")
    print(f"İşlem Durumu: {result.get('status')}")
    print(f"Mesaj: {result.get('message')}")
    print(f"Pod ID: {result.get('pod_id')}")
    
    if result.get('status') == 'success':
        print(f"Jupyter Notebook URL: {result.get('jupyter_url')}")
        
        terminal_info = result.get('terminal_info')
        if terminal_info:
            print(f"SSH Port: {terminal_info.get('ssh_port', 'Henüz hazır değil')}")
            print(f"Pod Çalışma Süresi: {terminal_info.get('uptime', 0)}s")
        
        print("\n✅ POD HAZIRLAMA TESTİ BAŞARILI!")
        print("\n📋 KULLANIM TALİMATLARI:")
        print("1. Jupyter Notebook için yukarıdaki URL'i kullanın")
        print("2. Şifre: atolye123")
        print("3. Web Terminal için RunPod Console'dan manuel olarak başlatın")
    else:
        print("\n❌ POD HAZIRLAMA TESTİ BAŞARISIZ!")
        print(f"Detaylar: {result}")

if __name__ == "__main__":
    main_test()