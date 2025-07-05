# tools/pod_management_tools.py

import requests
import json
from typing import Dict, Any
from langchain.tools import tool
from pydantic import BaseModel, Field

# Proje yapılandırmasını import et
try:
    from config import settings
except ImportError:
    print("Hata: config.py bulunamadı.")
    raise


class ExecuteCommandInput(BaseModel):
    """RunPod'da komut çalıştırma aracı için girdi şeması."""
    pod_id: str = Field(description="Komutun çalıştırılacağı Pod'un ID'si")
    command: str = Field(description="Pod üzerinde çalıştırılacak komut")


def _run_graphql_query(query: str, variables: Dict[str, Any] = None) -> Dict:
    """RunPod GraphQL API'sine bir sorgu gönderir ve sonucu döndürür."""
    api_url = "https://api.runpod.io/graphql"
    headers = {
        "Authorization": f"Bearer {settings.RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            try:
                error_details = response.json()
            except json.JSONDecodeError:
                error_details = response.text
            
            return {
                "errors": [{
                    "message": f"API'den {response.status_code} hatası alındı.",
                    "details": error_details
                }]
            }
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"[GraphQL Hata] İstek gönderilemedi: {e}")
        return {"errors": [{"message": str(e)}]}


@tool(args_schema=ExecuteCommandInput)
def execute_command_on_pod(pod_id: str, command: str) -> Dict:
    """
    RunPod GraphQL API kullanarak belirtilen Pod ID'deki ortamda gerçek bir komut çalıştırır.
    podExec mutation kullanarak Pod içinde komut execution yapar.
    
    Args:
        pod_id (str): Komutun çalıştırılacağı Pod'un ID'si
        command (str): Pod üzerinde çalıştırılacak komut
    
    Returns:
        Dict: İşlem sonucu (başarı/hata durumu, komut çıktısı, vb.)
    """
    print(f"\n[Pod Management] Pod '{pod_id}'da gerçek komut çalıştırılıyor: {command}")
    
    # RunPod'un resmi podExec GraphQL mutation sorgusu
    mutation = """
    mutation podExec($podId: String!, $command: String!) {
      podExec(input: {podId: $podId, command: $command, stdin: ""}) {
        output
        done
      }
    }
    """
    
    variables = {
        "podId": pod_id,
        "command": command
    }
    
    try:
        result = _run_graphql_query(mutation, variables)
        
        # Hata kontrolü
        if "errors" in result:
            error_messages = [error.get("message", "Bilinmeyen hata") for error in result["errors"]]
            return {
                "status": "error",
                "message": f"RunPod API hatası: {'; '.join(error_messages)}",
                "details": result["errors"]
            }
        
        # Başarılı sonuç
        if "data" in result and "podExec" in result["data"]:
            pod_exec_data = result["data"]["podExec"]
            
            command_output = pod_exec_data.get("output", "")
            is_done = pod_exec_data.get("done", False)
            
            print(f"[Pod Management] Komut başarıyla çalıştırıldı. Tamamlandı: {is_done}")
            print(f"[Pod Management] Komut çıktısı:\n{command_output}")
            
            return {
                "status": "success",
                "message": f"Pod '{pod_id}'da komut başarıyla çalıştırıldı: {command}",
                "command_output": command_output,
                "is_completed": is_done,
                "pod_id": pod_id,
                "command": command
            }
        else:
            return {
                "status": "error",
                "message": "API'den beklenmeyen yanıt formatı alındı",
                "details": result
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Komut çalıştırma hatası: {str(e)}",
            "exception_type": type(e).__name__
        }


@tool
def get_pod_status(pod_id: str) -> Dict:
    """
    RunPod GraphQL API kullanarak belirtilen Pod'un gerçek durumunu sorgular.
    
    Args:
        pod_id (str): Durumu sorgulanacak Pod'un ID'si
    
    Returns:
        Dict: Pod'un mevcut durumu ve detayları
    """
    print(f"\n[Pod Management] Pod '{pod_id}' gerçek durumu sorgulanıyor...")
    
    # GraphQL query sorgusu
    query = """
    query pod($podId: String!) {
      pod(input: {podId: $podId}) {
        id
        name
        runtime {
          uptimeInSeconds
        }
        desiredStatus
        lastStatusChange
      }
    }
    """
    
    variables = {
        "podId": pod_id
    }
    
    try:
        result = _run_graphql_query(query, variables)
        
        # Hata kontrolü
        if "errors" in result:
            error_messages = [error.get("message", "Bilinmeyen hata") for error in result["errors"]]
            return {
                "status": "error",
                "message": f"Pod durumu sorgulanamadı: {'; '.join(error_messages)}",
                "details": result["errors"]
            }
        
        # Başarılı sonuç
        if "data" in result and "pod" in result["data"]:
            pod_data = result["data"]["pod"]
            
            if pod_data is None:
                return {
                    "status": "error",
                    "message": f"Pod '{pod_id}' bulunamadı veya erişim izni yok"
                }
            
            runtime_info = pod_data.get("runtime") or {}
            
            # desiredStatus'u state olarak kullan
            pod_state = pod_data.get("desiredStatus", "UNKNOWN")
            
            print(f"[Pod Management] Pod '{pod_id}' durumu: {pod_state}")
            
            uptime_seconds = runtime_info.get("uptimeInSeconds", 0) if runtime_info else 0
            
            return {
                "status": "success",
                "pod_info": {
                    "id": pod_data.get("id"),
                    "name": pod_data.get("name"),
                    "state": pod_state,
                    "desired_status": pod_data.get("desiredStatus"),
                    "last_status_change": pod_data.get("lastStatusChange"),
                    "uptime_seconds": uptime_seconds,
                    "uptime_minutes": round(uptime_seconds / 60, 2) if uptime_seconds else 0
                }
            }
        else:
            return {
                "status": "error",
                "message": "API'den beklenmeyen yanıt formatı alındı",
                "details": result
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Pod '{pod_id}' durumu sorgulanamadı: {str(e)}",
            "exception_type": type(e).__name__
        }


def test_pod_management_workflow():
    """
    Pod management araçlarının tam entegrasyon testi.
    1. Pod oluşturma (operational_tools.find_and_prepare_gpu)
    2. Pod durumu kontrolü (get_pod_status)
    3. Pod'da komut çalıştırma (execute_command_on_pod)
    """
    print("\n" + "="*60)
    print("🧪 POD MANAGEMENT ARAÇLARI TAM TEST BAŞLIYOR")
    print("="*60)
    
    try:
        # 1. ADIM: Pod oluşturma
        print("\n1️⃣ ADIM: Pod oluşturuluyor...")
        from tools.operational_tools import find_and_prepare_gpu
        
        pod_creation_result = find_and_prepare_gpu.invoke({})
        print(f"Pod oluşturma sonucu: {pod_creation_result}")
        
        if pod_creation_result.get("status") != "success":
            print("❌ Pod oluşturulamadı, test durduruluyor.")
            return pod_creation_result
        
        # Pod ID'yi al
        pod_id = pod_creation_result.get("pod_info", {}).get("id")
        if not pod_id:
            print("❌ Pod ID bulunamadı, test durduruluyor.")
            print(f"Pod creation result: {pod_creation_result}")
            return {"status": "error", "message": "Pod ID alınamadı"}
        
        print(f"✅ Pod başarıyla oluşturuldu. Pod ID: {pod_id}")
        
        # 2. ADIM: Pod durumu kontrolü
        print(f"\n2️⃣ ADIM: Pod '{pod_id}' durumu kontrol ediliyor...")
        
        # Pod'un hazır olması için kısa bir bekleme
        import time
        print("Pod'un başlatılması için 10 saniye bekleniyor...")
        time.sleep(10)
        
        status_result = get_pod_status.invoke({"pod_id": pod_id})
        print(f"Pod durum sorgusu sonucu: {status_result}")
        
        if status_result.get("status") != "success":
            print("❌ Pod durumu sorgulanamadı.")
            return status_result
        
        pod_state = status_result.get("pod_info", {}).get("state")
        print(f"✅ Pod durumu alındı: {pod_state}")
        
        if pod_state == "RUNNING":
            print("🟢 Pod RUNNING durumunda, komut çalıştırmaya hazır!")
        else:
            print(f"🟡 Pod henüz {pod_state} durumunda, yine de komut deneyeceğiz.")
        
        # 3. ADIM: Pod'da komut çalıştırma
        print(f"\n3️⃣ ADIM: Pod '{pod_id}'da test komutu çalıştırılıyor...")
        
        test_command = "ls -l /workspace"
        command_result = execute_command_on_pod.invoke({"pod_id": pod_id, "command": test_command})
        print(f"Komut çalıştırma sonucu: {command_result}")
        
        if command_result.get("status") == "success":
            print("✅ Komut başarıyla çalıştırıldı!")
            output = command_result.get("command_output", "")
            is_completed = command_result.get("is_completed", False)
            print(f"📋 Komut tamamlandı: {is_completed}")
            print(f"📄 Komut çıktısı:\n{output}")
        else:
            print("❌ Komut çalıştırılamadı.")
            
        # 4. ADIM: Test özeti
        print(f"\n4️⃣ TEST ÖZETİ:")
        print(f"Pod ID: {pod_id}")
        print(f"Pod Durumu: {pod_state}")
        print(f"Komut Durumu: {command_result.get('status')}")
        print(f"Komut Tamamlandı: {command_result.get('is_completed', 'N/A')}")
        print(f"Workspace İçeriği Görüntülendi: {'Evet' if command_result.get('status') == 'success' else 'Hayır'}")
        
        final_result = {
            "status": "success",
            "message": "Pod management workflow testi tamamlandı",
            "test_results": {
                "pod_creation": pod_creation_result.get("status"),
                "pod_status_check": status_result.get("status"),
                "command_execution": command_result.get("status"),
                "pod_id": pod_id,
                "pod_state": pod_state,
                "command_completed": command_result.get("is_completed"),
                "workspace_accessible": command_result.get("status") == "success"
            }
        }
        
        print("\n🎉 TAM ENTEGRASYON TESTİ TAMAMLANDI!")
        print("="*60)
        
        return final_result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Test sırasında hata oluştu: {str(e)}",
            "exception_type": type(e).__name__
        }
        print(f"\n❌ TEST HATASI: {error_result}")
        print("="*60)
        return error_result


if __name__ == "__main__":
    """
    Bu dosya doğrudan çalıştırıldığında tam entegrasyon testini başlat.
    Kullanım: python tools/pod_management_tools.py
    """
    print("🚀 Pod Management Araçları - Doğrudan Test Modu")
    result = test_pod_management_workflow()
    
    if result.get("status") == "success":
        print("\n✅ TÜM TESTLERİN BAŞARILI!")
    else:
        print(f"\n❌ TEST BAŞARISIZ: {result.get('message')}")
        exit(1)
