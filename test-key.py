# anahtar_testi.py
import os
from dotenv import load_dotenv
import paramiko

print("🔑 ANAHTAR KONTROL TESTİ BAŞLATILDI 🔑")

# .env dosyasındaki değişkenleri yüklüyoruz
load_dotenv()
key_path = os.getenv("RUNPOD_SSH_KEY")

if not key_path:
    print("❌ HATA: .env dosyasında RUNPOD_SSH_KEY bulunamadı!")
else:
    print(f"🔬 Test edilecek anahtar yolu: {key_path}")
    
    try:
        # Anahtarı yüklemeyi deniyoruz. Eğer şifreliyse, bu satır hata verecektir.
        paramiko.Ed25519Key.from_private_key_file(key_path)
        
        print("\n" + "="*40)
        print("✅ BAŞARILI: Anahtar şifresiz ve doğru formatta!")
        print("Artık sorun kesinlikle anahtarda DEĞİL.")
        print("="*40)

    except paramiko.ssh_exception.PasswordRequiredException:
        print("\n" + "="*40)
        print("❌ TANI KONULDU: Anahtar dosyası ŞİFRELİ!")
        print("Lütfen 'ssh-keygen' komutunu -N \"\" parametresiyle tekrar çalıştırıp yeni bir anahtar oluşturun.")
        print("="*40)
        
    except Exception as e:
        print(f"\n❌ BEKLENMEDİK HATA: {e}")
        print("Anahtar yolu yanlış olabilir veya dosya bozuk olabilir.")