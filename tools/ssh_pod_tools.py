# tools/ssh_pod_tools.py

"""
🔐 SSH Anahtarı ile Gerçek Pod Otomasyonu
=======================================

Bu modül, RunPod GraphQL API'si ve SSH anahtarları kullanarak,
uzak GPU Pod'larında güvenli komut çalıştırma otomasyonu sağlar.

Gereksinimler:
- paramiko kütüphanesi (pip install paramiko)
- RunPod hesabında SSH anahtarı tanımlı olmalı
- ~/.ssh/ klasöründe özel anahtar dosyası bulunmalı

Kullanım:
    python tools/ssh_pod_tools.py
"""

import os
import sys
import time
import requests
import paramiko
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

# Environment setup
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

def find_ssh_key() -> Optional[str]:
    """Kullanıcının SSH özel anahtarını bulur."""
    ssh_dir = os.path.expanduser("~/.ssh")
    
    # Önce yeni RunPod anahtarını kontrol et
    runpod_key = os.path.join(ssh_dir, "runpod_key")
    if os.path.exists(runpod_key):
        print(f"🔑 RunPod SSH anahtarı bulundu: {runpod_key}")
        return runpod_key
    
    # Diğer anahtarları kontrol et
    possible_keys = [
        "id_rsa",
        "id_ed25519", 
        "id_ecdsa",
        "runpod"
    ]
    
    for key_name in possible_keys:
        key_path = os.path.join(ssh_dir, key_name)
        if os.path.exists(key_path):
            print(f"🔑 SSH anahtarı bulundu: {key_path}")
            return key_path
    
    # Tüm dosyaları listele
    if os.path.exists(ssh_dir):
        files = [f for f in os.listdir(ssh_dir) if not f.endswith('.pub')]
        print(f"📁 ~/.ssh klasöründeki dosyalar: {files}")
    
    return None

def get_pod_ssh_info(pod_id: str) -> Optional[Dict[str, Any]]:
    """Pod'un SSH bağlantı bilgilerini alır."""
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
                machine = pod.get("machine", {})
                
                # SSH port bulma (port 22)
                ssh_direct = None
                for port in ports:
                    if port.get("privatePort") == 22:
                        ssh_direct = {
                            "method": "direct_tcp",
                            "host": port.get("ip"),
                            "port": port.get("publicPort"),
                            "username": "root",
                            "command_template": f"ssh root@{port.get('ip')} -p {port.get('publicPort')} -i ~/.ssh/id_ed25519"
                        }
                        break
                
                # RunPod SSH Proxy yöntemi (her zaman mevcut)
                ssh_proxy = {
                    "method": "runpod_proxy", 
                    "host": "ssh.runpod.io",
                    "port": 22,
                    "username": f"{pod_id}-{machine.get('podHostId', '')}",
                    "command_template": f"ssh {pod_id}-{machine.get('podHostId', '')}@ssh.runpod.io -i ~/.ssh/id_ed25519"
                }
                
                return {
                    "pod_id": pod_id,
                    "uptime": runtime.get("uptimeInSeconds", 0),
                    "pod_name": pod.get("name", ""),
                    "pod_host": machine.get("podHostId", ""),
                    "direct_tcp": ssh_direct,
                    "runpod_proxy": ssh_proxy,
                    "preferred_method": ssh_direct if ssh_direct else ssh_proxy
                }
    
    return None

def execute_ssh_command(pod_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
    """SSH ile Pod'da komut çalıştırır."""
    print(f"🔧 Pod '{pod_id}' üzerinde SSH ile komut çalıştırılıyor: {command}")
    
    # SSH anahtarını bul
    ssh_key_path = find_ssh_key()
    if not ssh_key_path:
        return {
            "status": "error",
            "message": "SSH özel anahtarı bulunamadı. ~/.ssh/ klasörünü kontrol edin."
        }
    
    # Pod SSH bilgilerini al
    ssh_info = get_pod_ssh_info(pod_id)
    if not ssh_info:
        return {
            "status": "error",
            "message": f"Pod '{pod_id}' SSH bilgileri alınamadı. Pod çalışır durumda mı?"
        }
    
    # Önce Direct TCP'yi dene, sonra RunPod Proxy
    methods_to_try = []
    if ssh_info.get("direct_tcp"):
        methods_to_try.append(("Direct TCP", ssh_info["direct_tcp"]))
    if ssh_info.get("runpod_proxy"):
        methods_to_try.append(("RunPod Proxy", ssh_info["runpod_proxy"]))
    
    for method_name, method_info in methods_to_try:
        host = method_info["host"]
        port = method_info["port"]
        username = method_info["username"]
        
        print(f"🔗 SSH Bağlantısı ({method_name}): {username}@{host}:{port}")
        
        try:
            # SSH bağlantısı kur
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Özel anahtar yükle
            try:
                # Passphrase olmadan dene
                try:
                    private_key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path)
                except paramiko.PasswordRequiredException:
                    # Passphrase gerekli - şimdilik boş passphrase dene
                    private_key = paramiko.Ed25519Key.from_private_key_file(ssh_key_path, password="")
            except:
                try:
                    try:
                        private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
                    except paramiko.PasswordRequiredException:
                        private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path, password="")
                except:
                    try:
                        private_key = paramiko.ECDSAKey.from_private_key_file(ssh_key_path)
                    except paramiko.PasswordRequiredException:
                        private_key = paramiko.ECDSAKey.from_private_key_file(ssh_key_path, password="")
            
            ssh_client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=private_key,
                timeout=timeout
            )
            
            print(f"✅ SSH bağlantısı başarılı ({method_name})!")
            
            # Komutu çalıştır
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            ssh_client.close()
            
            result = {
                "status": "success",
                "pod_id": pod_id,
                "command": command,
                "output": output,
                "error": error,
                "exit_code": exit_code,
                "method_used": method_name,
                "ssh_info": method_info
            }
            
            if exit_code == 0:
                print(f"✅ Komut başarıyla çalıştırıldı!")
                if output:
                    print(f"📤 Çıktı:\n{output}")
            else:
                print(f"⚠️ Komut hata ile sonlandı (exit code: {exit_code})")
                if error:
                    print(f"❌ Hata:\n{error}")
            
            return result
            
        except paramiko.AuthenticationException as e:
            print(f"❌ SSH kimlik doğrulama hatası ({method_name}): {str(e)}")
            continue  # Diğer yöntemi dene
        except paramiko.SSHException as e:
            print(f"❌ SSH bağlantı hatası ({method_name}): {str(e)}")
            continue  # Diğer yöntemi dene
        except Exception as e:
            print(f"❌ Beklenmedik hata ({method_name}): {str(e)}")
            continue  # Diğer yöntemi dene
    
    return {
        "status": "error",
        "message": "Tüm SSH bağlantı yöntemleri başarısız oldu.",
        "ssh_info": ssh_info,
        "suggestion": "SSH anahtarının RunPod hesabında doğru tanımlı olduğundan emin olun."
    }

def create_ssh_pod(gpu_type_id: str) -> Dict[str, Any]:
    """SSH etkin bir Pod oluşturur ve hazır olmasını bekler."""
    print(f"\n[SSH Pod Creation] SSH etkin Pod oluşturuluyor...")
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
            "name": f"ssh-pod-{int(time.time())}",
            "imageName": "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
            "gpuCount": 1,
            "volumeInGb": 40,
            "volumeMountPath": "/workspace",
            "containerDiskInGb": 10,
            "startSsh": True,
            "startJupyter": True,
            "ports": "8888/http,22/tcp",
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
        print(f"✅ SSH Pod oluşturuldu! ID: {pod_id}")
        
        print(f"\n⏳ SSH bağlantısının hazır hale gelmesi bekleniyor...")
        
        ssh_ready = False
        max_attempts = 20
        
        for attempt in range(max_attempts):
            print(f"   - SSH hazırlık kontrolü [{attempt + 1}/{max_attempts}]...")
            
            ssh_info = get_pod_ssh_info(pod_id)
            if ssh_info and (ssh_info.get("direct_tcp") or ssh_info.get("runpod_proxy")):
                # SSH port bilgilerini göster
                if ssh_info.get("direct_tcp"):
                    direct = ssh_info["direct_tcp"]
                    print(f"   ✅ SSH Direct TCP hazır: {direct['host']}:{direct['port']}")
                if ssh_info.get("runpod_proxy"):
                    proxy = ssh_info["runpod_proxy"]
                    print(f"   ✅ SSH RunPod Proxy hazır: {proxy['username']}@{proxy['host']}")
                
                # SSH bağlantısını test et
                test_result = execute_ssh_command(pod_id, "echo 'SSH Test OK'")
                if test_result.get("status") == "success":
                    print(f"   ✅ SSH bağlantı testi başarılı!")
                    ssh_ready = True
                    break
                else:
                    print(f"   - SSH henüz hazır değil: {test_result.get('message', 'Bağlantı hatası')}")
            else:
                print(f"   - SSH port henüz hazır değil...")
            
            if attempt < max_attempts - 1:
                time.sleep(15)
        
        if not ssh_ready:
            return {
                "status": "partial_success",
                "message": "Pod oluşturuldu ancak SSH bağlantısı zaman aşımına uğradı.",
                "pod_id": pod_id,
                "suggestion": "Manuel olarak birkaç dakika sonra tekrar deneyin."
            }
        
        return {
            "status": "success",
            "message": "SSH etkin Pod başarıyla oluşturuldu ve hazır!",
            "pod_id": pod_id,
            "ssh_info": ssh_info,
            "jupyter_url": f"https://{pod_id}-8888.proxy.runpod.net/lab/"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"SSH Pod oluşturma sırasında beklenmedik bir hata oluştu: {str(e)}"}

class SSHCommandInput(BaseModel):
    pod_id: str = Field(description="Komutun çalıştırılacağı Pod ID'si")
    command: str = Field(description="Çalıştırılacak shell komutu")

@tool(args_schema=SSHCommandInput)
def execute_command_via_ssh(pod_id: str, command: str) -> Dict[str, Any]:
    """
    SSH kullanarak Pod'da gerçek komut çalıştırır.
    Bu fonksiyon gerçek otomasyonu sağlar - Jupyter Notebook gerekmez.
    """
    return execute_ssh_command(pod_id, command)

class CreateSSHPodInput(BaseModel):
    gpu_type_id: str = Field(description="Oluşturulacak Pod için GPU tipi ID'si")

@tool(args_schema=CreateSSHPodInput)
def prepare_environment_with_ssh(gpu_type_id: str) -> Dict[str, Any]:
    """
    SSH etkin Pod oluşturur ve gerçek komut çalıştırma için hazırlar.
    Bu fonksiyon tam otomasyonu sağlar.
    """
    return create_ssh_pod(gpu_type_id)

def main_test():
    """SSH araçlarının tam testi."""
    print("================================================================================")
    print("🔐 SSH ANAHTARLI POD MANAGEMENT ARAÇLARI - TAM TEST BAŞLIYOR")
    print("================================================================================")

    print("\n1️⃣ ADIM: SSH anahtarı kontrolü...")
    ssh_key = find_ssh_key()
    if not ssh_key:
        print("❌ SSH anahtarı bulunamadı!")
        print("📋 SSH anahtarı kurulum talimatları:")
        print("1. ssh-keygen -t rsa -b 4096 -f ~/.ssh/runpod_key")
        print("2. RunPod hesabınızda ~/.ssh/runpod_key.pub içeriğini ekleyin")
        return
    
    print("\n2️⃣ ADIM: SSH etkin Pod oluşturuluyor...")
    
    gpu_to_test = "NVIDIA GeForce RTX 3070"
    result = create_ssh_pod(gpu_to_test)
    
    print("\n---------------------- SONUÇ ----------------------")
    print(f"İşlem Durumu: {result.get('status')}")
    print(f"Mesaj: {result.get('message')}")
    
    if result.get('status') == 'success':
        pod_id = result.get('pod_id')
        ssh_info = result.get('ssh_info')
        
        print(f"Pod ID: {pod_id}")
        print(f"SSH: root@{ssh_info['host']}:{ssh_info['port']}")
        print(f"Jupyter: {result.get('jupyter_url')}")
        
        print("\n3️⃣ ADIM: SSH ile komut testi...")
        test_commands = [
            "whoami",
            "pwd", 
            "python --version",
            "nvidia-smi --query-gpu=name --format=csv,noheader"
        ]
        
        for cmd in test_commands:
            print(f"\n🔧 Test komutu: {cmd}")
            cmd_result = execute_ssh_command(pod_id, cmd)
            if cmd_result.get("status") == "success":
                print(f"✅ Başarılı: {cmd_result.get('output', '').strip()}")
            else:
                print(f"❌ Hata: {cmd_result.get('message')}")
        
        print("\n✅ SSH POD MANAGEMENT TESTİ BAŞARILI!")
        print("\n📋 KULLANIM TALİMATLARI:")
        print("1. execute_command_via_ssh() ile gerçek komutlar çalıştırabilirsiniz")
        print("2. GraphAgent artık tam otomasyonla çalışır")
        print("3. Jupyter Notebook manual kullanım için hala mevcut")
    else:
        print("\n❌ SSH POD MANAGEMENT TESTİ BAŞARISIZ!")
        print(f"Detaylar: {result}")

if __name__ == "__main__":
    main_test()
