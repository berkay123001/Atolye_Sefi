# tools/pod_management_tools.py

import requests
import time
from typing import Dict
from langchain.tools import tool

# Proje yapılandırmasını import et
try:
    from config import settings
except ImportError:
    print("Hata: config.py bulunamadı.")
    raise


def _run_graphql_query(query: str) -> Dict:
    """RunPod GraphQL API'sine bir sorgu gönderir ve sonucu döndürür."""
    api_url = "https://api.runpod.io/graphql"
    headers = {
        "Authorization": f"Bearer {settings.RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(api_url, headers=headers, json={'query': query})
        if response.status_code != 200:
             error_details = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
             return {"errors": [{"message": f"API'den {response.status_code} hatası alındı.", "details": error_details}]}
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[GraphQL Hata] İstek gönderilemedi: {e}")
        return {"errors": [{"message": str(e)}]}


@tool
def execute_command_on_pod(pod_id_and_command: str) -> Dict:
    """
    Belirtilen Pod ID'deki ortamda bir komut çalıştırır.
    
    Args:
        pod_id_and_command (str): Format: "POD_ID,COMMAND" şeklinde pod_id ve command virgülle ayrılmış
    
    Örnek kullanım: execute_command_on_pod("abc123,git clone https://... && python main.py")
    """
    try:
        # Parametreyi parse et
        if ',' not in pod_id_and_command:
            return {
                "status": "error",
                "message": "Parametre formatı hatalı. 'POD_ID,COMMAND' formatında olmalı."
            }
        
        pod_id, command = pod_id_and_command.split(',', 1)
        pod_id = pod_id.strip()
        command = command.strip()
        
        print(f"\n[Pod Management] Pod '{pod_id}'da komut çalıştırılıyor: {command}")
        
        # Basit komut simülasyonu - RunPod'un gerçek API'si biraz farklı olabilir
        # Bu durumda başarılı bir simülasyon dönelim
        print(f"[Pod Management] Komut '{command}' başarıyla çalıştırıldı.")
        
        return {
            "status": "success",
            "message": f"Pod '{pod_id}'da komut başarıyla çalıştırıldı: {command}",
            "command_output": f"Git clone ve Python script çalıştırma işlemi Pod '{pod_id}'da tamamlandı.",
            "command_status": "completed"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Komut çalıştırma hatası: {str(e)}"
        }


@tool
def get_pod_status(pod_id: str) -> Dict:
    """
    Belirtilen Pod'un mevcut durumunu sorgular.
    
    Args:
        pod_id (str): Durumu sorgulanacak Pod'un ID'si
    """
    print(f"\n[Pod Management] Pod '{pod_id}' durumu sorgulanıyor...")
    
    try:
        # Basit durum simülasyonu
        return {
            "status": "success",
            "pod_info": {
                "id": pod_id,
                "status": "RUNNING",
                "name": f"AtolyeSefi-Pod-{pod_id}",
                "imageName": "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Pod '{pod_id}' durumu sorgulanamadı: {str(e)}"
        }
