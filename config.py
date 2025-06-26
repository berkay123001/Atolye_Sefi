import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yüklemek için
load_dotenv()

class Settings(BaseSettings):
    """
    Proje ayarlarını .env dosyasından okuyan ve yöneten yapılandırma sınıfı.
    Pydantic kullanarak tip güvenliği (type safety) sağlar.
    """
    # .env dosyasından okunacak zorunlu alan. Eğer .env içinde yoksa hata verir.
    GROQ_API_KEY: str

    # Varsayılan değeri olan, opsiyonel alanlar.
    AGENT_MODEL_NAME: str = "llama3-70b-8192"
    AGENT_SYSTEM_PROMPT: str = "You are a helpful MLOps agent."

    class Config:
        # Pydantic'in .env dosyasını tanımasını sağlar.
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Ayarları projenin her yerinden kolayca erişilebilir hale getirmek için
# bir örnek (instance) oluşturuyoruz.
settings = Settings()

# Test için ayarların doğru yüklendiğini kontrol edebiliriz:
if __name__ == "__main__":
    print("Yüklenen Ayarlar:")
    print(f"Model Adı: {settings.AGENT_MODEL_NAME}")
    print(f"Groq API Anahtarı: {settings.GROQ_API_KEY[:4]}... (güvenlik için kısaltıldı)")