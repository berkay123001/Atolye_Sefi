# tools/operational_tools.py

import sys
import os
import requests
import time
import json
from typing import Dict, List, Optional

# LangChain'in bu fonksiyonu bir "araç" olarak tanımasını sağlayan dekoratör
from langchain.tools import tool

# Proje yapılandırmasını import et
try:
    from config import settings
except ImportError:
    print("Hata: config.py bulunamadı.")
    sys.exit(1)


# --- GraphQL Sorgu Fonksiyonu ---
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
def get_available_gpus() -> List[Dict]:
    """
    RunPod API'sinden o an mevcut olan ve kiralanabilecek tüm GPU tiplerini listeler.
    """
    # ... (Bu fonksiyon değişmedi)
    graphql_query = "query GpuTypes { gpuTypes { id displayName memoryInGb } }"
    data = _run_graphql_query(graphql_query)
    if "errors" in data and data.get("errors"): return [{"error": "Mevcut GPU listesi alınamadı.", "details": data['errors'][0]['message']}]
    return data.get("data", {}).get("gpuTypes", [])


@tool
def prepare_environment(gpu_type_id: str, docker_image: str = "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04") -> Dict:
    """
    RunPod API'sini kullanarak, web arayüzünü taklit eden spesifik disk boyutları
    ile Community Cloud üzerinde bir ortam başlatmayı dener.
    """
    print(f"\n[Operational Tool] '{gpu_type_id}' için 'Community Cloud' üzerinde SPESİFİK disk isteği ile ortam hazırlanıyor...")
    
    unique_pod_name = f"AtolyeSefi-Pod-{gpu_type_id.replace(' ', '-').lower()}-{int(time.time())}"

    # NİHAİ ÇÖZÜM: Web arayüzünün gönderdiği disk parametrelerini manuel olarak ekliyoruz.
    graphql_mutation = f'''
    mutation podFindAndDeployOnDemand {{
      podFindAndDeployOnDemand(
        input: {{
          cloudType: COMMUNITY,
          gpuTypeId: "{gpu_type_id}",
          name: "{unique_pod_name}",
          imageName: "{docker_image}",
          gpuCount: 1,
          volumeInGb: 35,          # <-- DOĞRU PARAMETRE: Ana depolama alanı (Volume)
          containerDiskInGb: 5     # <-- DOĞRU PARAMETRE: Sistem diski (Container)
        }}
      ) {{
        id
        imageName
        machineId
      }}
    }}
    '''
    data = _run_graphql_query(graphql_mutation)
    
    if "errors" in data and data.get("errors"):
        raw_error_details = data['errors']
        print(f"\n[!!!] HAM API HATASI: {json.dumps(raw_error_details, indent=2)}\n")
        return {"status": "error", "message": f"'{gpu_type_id}' için API'den hata alındı.", "raw_error": raw_error_details}
    
    pod_data = data.get("data", {}).get("podFindAndDeployOnDemand")
    if pod_data:
        print(f"[Operational Tool] Başarılı! '{gpu_type_id}' ile Pod oluşturuldu. ID: {pod_data.get('id')}")
        return {"status": "success", "message": f"'{gpu_type_id}' ile Pod başarıyla oluşturuldu.", "pod_info": pod_data}
    else:
        return {"status": "error", "message": "Pod oluşturulamadı. Spesifik isteğe rağmen anlık yer olmayabilir veya başka bir sorun olabilir.", "raw_response": data}


# --- Nihai Kanıt Testi ---
if __name__ == '__main__':
    print("--- \"Community Cloud\" üzerinde Nihai Test (Spesifik Disk Boyutu ile) ---")
    
    gpu_to_try = "NVIDIA RTX A4000"
    image_to_try = "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"
    
    print(f"\nUYARI: '{gpu_to_try}' için '{image_to_try}' imajı ile TEK bir deneme yapılacak.")
    print("İptal etmek için 5 saniye içinde CTRL+C'ye basın.")
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nİşlem kullanıcı tarafından iptal edildi.")
        sys.exit(0)

    result = prepare_environment.invoke({
        "gpu_type_id": gpu_to_try,
        "docker_image": image_to_try
    })
    
    print("\n--- Nihai Test Sonucu ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-------------------------")
    if result.get("status") == "success":
        print("[SONUÇ] BAŞARILI! Sorun çözüldü. Kod, spesifik disk isteği ile Pod oluşturabildi.")
    else:
        print("[SONUÇ] DİKKAT! Kod hala Pod oluşturamadı.")
        print("Eğer bu deneme de başarısız olursa, sorun KESİNLİKLE kodda değildir. Lütfen RunPod API anahtarınızın 'Serverless' izinlerine sahip olduğundan emin olun veya yeni bir anahtar oluşturmayı deneyin.")