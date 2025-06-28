# tools/operational_tools.py
import uuid
import time
from typing import Dict

# LangChain'in bu fonksiyonu bir "araç" olarak tanımasını sağlayan dekoratör
from langchain.tools import tool

@tool
def prepare_environment(gpu_type: str) -> Dict:
    """
    Belirtilen GPU tipine sahip bir bulut ortamı (örn: RunPod) hazırlar.
    Bu araç, bir MLOps görevi için gerekli olan sanal makineyi ve
    temel yapılandırmayı kurar. Şimdilik bu bir simülasyondur.

    Args:
        gpu_type (str): Kurulması istenen GPU'nun modeli (örn: 'A100', 'RTX 4090').

    Returns:
        Dict: İşlemin durumunu ve oluşturulan oturumun kimliğini içeren bir sözlük.
    """
    # 1. Görevin başladığını belirten bir mesaj yazdır.
    #    Bu, terminalde kodu çalıştırırken bize bilgi verir.
    print(f"\n[Operational Tool] RunPod üzerinde '{gpu_type}' GPU'lu bir ortam hazırlanıyor...")
    
    # 2. Gerçek bir API çağrısının zaman alacağını simüle etmek için kısa bir bekleme.
    time.sleep(3)
    
    # 3. Rastgele ve benzersiz bir oturum kimliği (session_id) oluştur.
    #    Bu, ileride bu özel ortamı takip etmemizi sağlar.
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    print(f"[Operational Tool] Ortam başarıyla kuruldu! Oturum Kimliği: {session_id}")

    # 4. İşlem başarılı olduğunda, standart bir başarı mesajı ve oturum kimliğini döndür.
    #    Ajan, bu çıktıyı "Gözlem" olarak alacak ve planının sonraki adımına geçecektir.
    return {
        "status": "success",
        "message": f"Ortam, {gpu_type} GPU ile başarıyla kuruldu.",
        "session_id": session_id
    }

# --- Test Bloğu ---
# Bu dosya doğrudan çalıştırıldığında, aracın doğru çalışıp çalışmadığını test eder.
if __name__ == '__main__':
    print("--- Operasyonel Araç Testi Başlatıldı ---")
    
    # Test senaryosu: 'A100' GPU'lu bir ortam iste.
    gpu_to_prepare = "NVIDIA A100 80GB"
    result = prepare_environment(gpu_to_prepare)
    
    print("\n--- Test Sonucu ---")
    # Dönen sözlüğü daha okunaklı bir formatta yazdır.
    import json
    print(json.dumps(result, indent=2))
