# tools/operational_tools.py

import sys
import os
import requests
import time
import json
import re
from typing import Dict, List, Any

# LangChain araçları için gerekli importlar
from langchain.tools import tool

try:
    from config import settings
except ImportError:
    print("Hata: config.py bulunamadı.")
    sys.exit(1)

# --- Yardımcı Fonksiyonlar (Değişmedi) ---
def _run_graphql_query(query: str) -> Dict:
    api_url = "https://api.runpod.io/graphql"
    headers = {"Authorization": f"Bearer {settings.RUNPOD_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(api_url, headers=headers, json={'query': query})
        if response.status_code != 200:
             error_details = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
             return {"errors": [{"message": f"API'den {response.status_code} hatası alındı.", "details": error_details}]}
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"errors": [{"message": str(e)}]}

def _get_available_gpus_internal() -> List[Dict]:
    graphql_query = "query GpuTypes { gpuTypes { id displayName memoryInGb } }"
    data = _run_graphql_query(graphql_query)
    if "errors" in data and data.get("errors"): return []
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
    Belirtilen minimum VRAM'e sahip, o an mevcut olan bir GPU'yu bulur ve kiralar.
    Bu araç, hem ajandan gelen string girdileri hem de API'den gelen string VRAM
    değerlerini tolere edecek kadar sağlamdır.
    """
    # 1. ADIM: AJANDAN GELEN KİRLİ VERİYİ TEMİZLE (SENİN ÇÖZÜMÜN)
    # Bu blok, ajanın 'min_memory_gb = 16' gibi bir metin göndermesi durumunda bile
    # içindeki sayıyı doğru bir şekilde ayrıştırır.
    parsed_min_memory_gb = 16
    if isinstance(min_memory_gb, str):
        match = re.search(r'\d+', min_memory_gb)
        if match:
            parsed_min_memory_gb = int(match.group(0))
    elif isinstance(min_memory_gb, int):
        parsed_min_memory_gb = min_memory_gb

    print(f"\n[Master Tool] Görev başlatıldı (İstenen Min VRAM: {parsed_min_memory_gb}GB)...")
    
    all_gpus = _get_available_gpus_internal()
    if not all_gpus:
        return {"status": "error", "message": "GPU listesi alınamadığı için işlem yapılamadı."}

    # 2. ADIM: API'DEN GELEN KİRLİ VERİYİ TEMİZLE (YENİ EKlenen ZIRH)
    # Bu yardımcı fonksiyon, API'den gelen 'memoryInGb' değerinin '80' gibi bir
    # string olması durumunda bile onu güvenli bir şekilde sayıya çevirir.
    def to_int_safe(value: Any) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    # Artık her iki taraftan gelen veriyi de temizleyerek karşılaştırma yapıyoruz.
    suitable_gpus = [
        gpu for gpu in all_gpus 
        if to_int_safe(gpu.get('memoryInGb')) >= parsed_min_memory_gb
    ]
    
    if not suitable_gpus:
        return {"status": "error", "message": "Belirtilen minimum VRAM'e uygun hiçbir GPU bulunamadı."}

    priority_order = ["A4000", "A5000", "RTX 3090", "RTX 4090", "A100"]
    sorted_gpus = sorted(
        suitable_gpus,
        key=lambda gpu: next((priority_order.index(p) for p in priority_order if p in gpu['id']), len(priority_order))
    )
    
    for gpu in sorted_gpus:
        gpu_id = gpu['id']
        print(f"[Master Tool] '{gpu_id}' deneniyor...")
        result = _prepare_environment_internal(gpu_id)
        
        if "errors" in result and result.get("errors"):
            error_message = result['errors'][0].get('message', '')
            if "instances available" in error_message:
                print(f"[Master Tool] '{gpu_id}' mevcut değil. Sonraki seçenek deneniyor...")
                time.sleep(1)
                continue
            else:
                return {"status": "error", "message": f"'{gpu_id}' için beklenmedik bir API hatası alındı.", "details": error_message}
        
        pod_data = result.get("data", {}).get("podFindAndDeployOnDemand")
        if pod_data:
            print(f"[Master Tool] BAŞARILI! '{gpu_id}' ile Pod oluşturuldu.")
            return {"status": "success", "message": f"'{gpu_id}' ile Pod başarıyla oluşturuldu.", "pod_info": pod_data}

    return {"status": "error", "message": "Uygun tüm GPU'lar denendi ancak hiçbiri şu anda mevcut değil."}

# --- Test Bloğu ---
if __name__ == '__main__':
    print("--- Yeni 'Usta' Araç Testi Başlatıldı ---")
    result = find_and_prepare_gpu.invoke({"min_memory_gb": 16})
    print("\n--- Nihai Test Sonucu ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
