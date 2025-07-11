#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 RunPod Pod Management Test Script

Bu script, RunPod API kullanarak pod oluşturma, yönetme ve SSH erişimi sağlama süreçlerini test eder.
"""

import os
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import json

# Environment setup
load_dotenv()
API_KEY = os.getenv("RUNPOD_API_KEY")
GRAPHQL_URL = "https://api.runpod.io/graphql"

if not API_KEY:
    print("❌ HATA: RUNPOD_API_KEY bulunamadı!")
    print("🔧 Çözüm: .env dosyanızda RUNPOD_API_KEY=your_key_here ekleyin")
    exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def run_graphql_query(query: str, variables: Dict = None) -> Dict:
    """GraphQL sorgusu çalıştırmak için yardımcı fonksiyon."""
    try:
        response = requests.post(
            GRAPHQL_URL, 
            json={"query": query, "variables": variables or {}}, 
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ GraphQL isteği sırasında hata: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"📄 Hata Detayı: {e.response.text}")
        return {"errors": [{"message": str(e)}]}

def test_api_connection():
    """API bağlantısını test eder."""
    print("🧪 API bağlantısı test ediliyor...")
    test_query = """
    query {
        myself {
            id
            email
        }
    }
    """
    
    test_result = run_graphql_query(test_query)
    if "errors" in test_result:
        print(f"❌ API bağlantı hatası: {test_result['errors'][0]['message']}")
        return False
    else:
        user_data = test_result.get("data", {}).get("myself", {})
        print(f"✅ API bağlantısı başarılı!")
        print(f"👤 Kullanıcı ID: {user_data.get('id', 'N/A')}")
        print(f"📧 Email: {user_data.get('email', 'N/A')}")
        return True

def list_all_pods():
    """Tüm pod'ları listeler."""
    query = """
    query {
        myself {
            pods {
                id
                name
                desiredStatus
                runtime {
                    uptimeInSeconds
                }
            }
        }
    }
    """
    
    result = run_graphql_query(query)
    
    if "errors" in result:
        print(f"❌ Pod listesi alınamadı: {result['errors'][0]['message']}")
        return
    
    pods = result.get("data", {}).get("myself", {}).get("pods", [])
    
    if not pods:
        print("📝 Hiç pod bulunamadı.")
        return
    
    print("\n📋 MEVCUT POD'LAR:")
    print("=" * 60)
    
    for i, pod in enumerate(pods, 1):
        pod_id = pod.get("id", "")
        pod_name = pod.get("name", "")
        status = pod.get("desiredStatus", "")
        runtime = pod.get("runtime", {})
        uptime = runtime.get("uptimeInSeconds", 0) if runtime else 0
        
        print(f"{i}. 🆔 {pod_id}")
        print(f"   📛 Name: {pod_name}")
        print(f"   🟢 Status: {status}")
        print(f"   ⏱️ Uptime: {uptime}s")
        
        # Jupyter URL'i oluştur
        if uptime > 0:  # Pod çalışıyorsa
            jupyter_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
            print(f"   🔗 Jupyter: {jupyter_url}")
            print(f"   🔐 Şifre: atolye123")
        
        print()
    
    print("=" * 60)

def create_pod_with_jupyter(gpu_type_id: str) -> Dict:
    """SSH ve Jupyter ile pod oluşturur."""
    print(f"\n🔥 Pod oluşturuluyor...")
    print(f"🎮 GPU Type: {gpu_type_id}")
    
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
            "name": f"script-test-{int(time.time())}",
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
    
    result = run_graphql_query(mutation, variables)
    
    if "errors" in result:
        print(f"❌ Pod oluşturma hatası: {result['errors'][0].get('message')}")
        return {"status": "error", "message": result['errors'][0].get('message')}
    
    pod_data = result.get("data", {}).get("podFindAndDeployOnDemand")
    if not pod_data:
        print("❌ Pod oluşturulamadı - uygun GPU bulunamamış olabilir.")
        return {"status": "error", "message": "Pod oluşturulamadı"}
    
    pod_id = pod_data.get("id")
    image_name = pod_data.get("imageName")
    print(f"✅ Pod başarıyla oluşturuldu!")
    print(f"🆔 Pod ID: {pod_id}")
    print(f"🖼️ Image: {image_name}")
    
    return {
        "status": "success",
        "pod_id": pod_id,
        "image_name": image_name,
        "machine_id": pod_data.get("machineId")
    }

def wait_for_pod_ready(pod_id: str, max_attempts: int = 15) -> Dict:
    """Pod'un Jupyter port 8888'inin hazır olmasını bekler."""
    print(f"\n📡 Pod '{pod_id}' hazırlık durumu izleniyor...")
    print(f"⏰ Maksimum {max_attempts} deneme, 15 saniye aralıklarla")
    
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
    
    for attempt in range(max_attempts):
        print(f"🔍 Deneme [{attempt + 1}/{max_attempts}] - Pod durumu kontrol ediliyor...")
        
        status_result = run_graphql_query(status_query, {})
        
        if "errors" in status_result:
            print(f"❌ Durum sorgusu hatası: {status_result['errors'][0]['message']}")
            continue
            
        # Pod'umuzu bulalım
        pods = status_result.get("data", {}).get("myself", {}).get("pods", [])
        current_pod = None
        for pod in pods:
            if pod.get("id") == pod_id:
                current_pod = pod
                break
        
        if not current_pod:
            print("⚠️ Pod bulunamadı, devam ediliyor...")
            time.sleep(15)
            continue
            
        runtime = current_pod.get("runtime")
        if not runtime:
            print("⏳ Pod henüz runtime bilgisine sahip değil...")
            time.sleep(15)
            continue
            
        uptime = runtime.get("uptimeInSeconds", 0)
        ports = runtime.get("ports", [])
        
        print(f"📊 Pod durumu: {len(ports)} port, çalışma süresi: {uptime}s")
        
        # Port 8888'i arıyoruz
        for port in ports:
            if port.get("privatePort") == 8888:
                jupyter_url = f"https://{pod_id}-8888.proxy.runpod.net/lab/"
                print(f"✅ Jupyter Notebook hazır!")
                print(f"🔗 URL: {jupyter_url}")
                print(f"🔐 Şifre: atolye123")
                return {
                    "status": "ready",
                    "jupyter_url": jupyter_url,
                    "uptime": uptime,
                    "total_ports": len(ports)
                }
        
        print(f"⏳ Jupyter portu (8888) henüz hazır değil...")
        if attempt < max_attempts - 1:
            print(f"⏰ 15 saniye bekleniyor...")
            time.sleep(15)
    
    return {
        "status": "timeout",
        "message": f"Pod {max_attempts * 15} saniye içinde hazır hale gelmedi"
    }

def test_complete_workflow():
    """Tam iş akışını test eder: Pod oluştur -> Bekle -> Bağlan."""
    print("\n🚀 TAM İŞ AKIŞI TESTİ BAŞLIYOR")
    print("=" * 50)
    
    GPU_TYPE = "NVIDIA GeForce RTX 3070"
    
    # 1. Pod Oluştur
    print("\n1️⃣ Pod oluşturuluyor...")
    create_result = create_pod_with_jupyter(GPU_TYPE)
    
    if create_result["status"] != "success":
        print(f"❌ Pod oluşturma başarısız: {create_result['message']}")
        return create_result
    
    pod_id = create_result["pod_id"]
    print(f"✅ Pod oluşturuldu: {pod_id}")
    
    # 2. Hazır olmasını bekle
    print("\n2️⃣ Pod'un hazır olması bekleniyor...")
    wait_result = wait_for_pod_ready(pod_id)
    
    if wait_result["status"] != "ready":
        print(f"❌ Pod hazır hale gelmedi: {wait_result['message']}")
        return wait_result
    
    print("\n✅ TAM İŞ AKIŞI TESTİ BAŞARILI!")
    print("🎯 Jupyter Notebook'a erişebilirsiniz!")
    print(f"🔗 URL: {wait_result['jupyter_url']}")
    print(f"🔐 Şifre: atolye123")
    
    return {
        "status": "success",
        "pod_id": pod_id,
        "jupyter_url": wait_result["jupyter_url"]
    }

def main():
    """Ana menu fonksiyonu."""
    print("=" * 70)
    print("🚀 RUNPOD POD MANAGEMENT TEST SCRIPT")
    print("=" * 70)
    
    if not test_api_connection():
        return
    
    while True:
        print("\n📋 MENÜ:")
        print("1. Mevcut pod'ları listele")
        print("2. Yeni pod oluştur ve test et (ÜCRETLİ!)")
        print("3. Çıkış")
        
        try:
            choice = input("\nSeçiminiz (1-3): ").strip()
            
            if choice == "1":
                list_all_pods()
            elif choice == "2":
                print("\n⚠️ DİKKAT: Bu işlem yeni bir pod oluşturacak ve ücretlendirilecek!")
                confirm = input("Devam etmek istiyor musunuz? (y/N): ").strip().lower()
                if confirm == 'y':
                    test_complete_workflow()
                else:
                    print("❌ İşlem iptal edildi.")
            elif choice == "3":
                print("👋 Çıkılıyor...")
                break
            else:
                print("❌ Geçersiz seçim! Lütfen 1-3 arası bir sayı girin.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Ctrl+C ile çıkılıyor...")
            break
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")

if __name__ == "__main__":
    main()
