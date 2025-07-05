# Atölye Şefi - Docker Kullanım Kılavuzu

## 🚀 Hızlı Başlangıç

### Önkoşullar
- Docker (20.10+)
- Docker Compose (v2.0+)
- NVIDIA Container Toolkit (GPU kullanımı için)
- En az 8GB RAM
- En az 20GB disk alanı

### Çevre Değişkenleri
`.env` dosyanızda aşağıdaki değişkenlerin tanımlı olduğundan emin olun:

```bash
RUNPOD_API_KEY=your_runpod_api_key_here
GROQ_API_KEY=your_groq_api_key_here
SSH_ROOT_PASSWORD=AtolyeSefi2025!  # Opsiyonel, varsayılan kullanılabilir
```

## 📦 Docker Build

### Manuel Build
```bash
# Temel build
docker build -t atolyesefi:latest .

# Custom SSH şifresi ile build
docker build --build-arg SSH_ROOT_PASSWORD="MySecurePassword123" -t atolyesefi:latest .
```

### Otomatik Build & Test
```bash
./docker/build-and-test.sh
```

## 🏃‍♂️ Container Çalıştırma

### Docker Run ile
```bash
# Basit çalıştırma
docker run -d \
  --name atolyesefi \
  -p 2222:22 \
  -p 7860:7860 \
  --env-file .env \
  atolyesefi:latest

# GPU desteği ile
docker run -d \
  --name atolyesefi \
  --gpus all \
  -p 2222:22 \
  -p 7860:7860 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  atolyesefi:latest
```

### Docker Compose ile (Önerilen)
```bash
# Geliştirme ortamı
docker-compose up --build

# Üretim ortamı
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Sadece build (çalıştırmadan)
docker-compose build
```

## 🔗 Erişim Noktaları

### Web Arayüzü (Gradio)
- **URL:** http://localhost:7860
- **Açıklama:** Ana AI agent arayüzü
- **Health Check:** http://localhost:7860/health

### SSH Erişimi
```bash
# SSH bağlantısı
ssh root@localhost -p 2222

# Şifre: .env dosyasındaki SSH_ROOT_PASSWORD değeri
# Varsayılan: AtolyeSefi2025!
```

### Jupyter Lab (Opsiyonel)
- **URL:** http://localhost:8888
- **Açıklama:** Geliştirme ve debugging için

## 🛠️ Container Yönetimi

### Durum Kontrolü
```bash
# Container durumu
docker ps -a --filter "name=atolyesefi"

# Log görüntüleme
docker logs atolyesefi -f

# Container istatistikleri
docker stats atolyesefi
```

### Container İçi Komutlar
```bash
# Container'a bash ile bağlan
docker exec -it atolyesefi bash

# Python ortamı kontrol
docker exec atolyesefi python --version

# GPU kontrolü
docker exec atolyesefi nvidia-smi

# Servis durumları
docker exec atolyesefi ps aux
```

### Veri ve Log Yönetimi
```bash
# Log dosyalarını görüntüle
docker exec atolyesefi ls -la /app/logs/

# Workspace içeriği
docker exec atolyesefi ls -la /workspace/

# Container'dan dosya kopyala
docker cp atolyesefi:/app/logs/app.log ./local-app.log
```

## 🔧 Yapılandırma Seçenekleri

### Container Başlatma Modları
```bash
# Üretim modu (varsayılan)
docker run ... atolyesefi:latest

# Geliştirme modu
docker run ... atolyesefi:latest --mode development

# Sadece SSH (Gradio olmadan)
docker run ... atolyesefi:latest --no-gradio

# Sadece Gradio (SSH olmadan)
docker run ... atolyesefi:latest --no-ssh
```

### Çevre Değişkenleri Override
```bash
docker run \
  -e GRADIO_SERVER_PORT=8080 \
  -e GRADIO_DEBUG=true \
  -e PYTHONPATH=/app \
  -p 8080:8080 \
  ... atolyesefi:latest
```

## 🏥 Troubleshooting

### Yaygın Sorunlar

#### Container başlamıyor
```bash
# Container log'larını kontrol et
docker logs atolyesefi

# Disk alanını kontrol et
df -h

# Port çakışması kontrolü
netstat -tuln | grep -E "(2222|7860)"
```

#### SSH bağlantısı kurulamıyor
```bash
# SSH servisinin çalıştığını kontrol et
docker exec atolyesefi systemctl status ssh

# SSH yapılandırmasını kontrol et
docker exec atolyesefi cat /etc/ssh/sshd_config | grep -E "(PermitRootLogin|PasswordAuthentication)"

# SSH restart
docker exec atolyesefi service ssh restart
```

#### Gradio erişilemiyor
```bash
# Gradio process kontrolü
docker exec atolyesefi ps aux | grep python

# Port kontrolü
docker exec atolyesefi netstat -tuln | grep 7860

# Health check
curl http://localhost:7860/health
```

#### Gradio chat formatı hatası
```bash
# Hata: "Data incompatible with messages format"
# Çözüm: Container'ı restart et (Python cache temizliği için)
docker restart atolyesefi

# Tool schema hataları için de restart gerekebilir
docker logs atolyesefi --tail 20  # Hata loglarını kontrol et
```

#### GPU algılanmıyor
```bash
# NVIDIA Container Toolkit kontrolü
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# Container içi GPU kontrolü
docker exec atolyesefi nvidia-smi

# CUDA kütüphaneleri
docker exec atolyesefi python -c "import torch; print(torch.cuda.is_available())"
```

### Debug Modu
```bash
# Verbose logging ile çalıştır
docker run \
  -e GRADIO_DEBUG=true \
  -e PYTHONPATH=/app \
  -v $(pwd)/logs:/app/logs \
  ... atolyesefi:latest --mode development
```

### Performance Tuning
```bash
# Kaynak sınırları ile çalıştır
docker run \
  --memory=8g \
  --cpus="4.0" \
  --shm-size=2g \
  ... atolyesefi:latest
```

## 🔄 Geliştirme Workflow'u

### ⚡ Hızlı Günlük Komutlar
```bash
# Container'ı başlat
docker start atolyesefi

# Container'ı durdur
docker stop atolyesefi

# Kod değişikliği sonrası restart (En çok kullanılan!)
docker restart atolyesefi

# Log kontrol (sorun giderme için)
docker logs atolyesefi --tail 10

# Durum kontrol
docker ps -a --filter "name=atolyesefi"
```

### Canlı Ayna Sistemi
Kod değişiklikleri anında container'a yansır:
```bash
# Container'ı canlı ayna ile başlat
docker run -d \
  --name atolyesefi \
  -p 2222:22 \
  -p 7860:7860 \
  --env-file .env \
  -v $(pwd):/workspace \
  atolyesefi:latest
```

### Kod Güncellemelerini Uygulama

#### Yöntem 1: Container Restart (Önerilen)
```bash
# Python cache'ini temizlemek için container'ı restart et
docker restart atolyesefi
```

#### Yöntem 2: Sadece Gradio Process'ini Restart
```bash
# Daha hızlı - sadece Gradio process'ini yeniden başlat
docker exec atolyesefi pkill -f "python -m app.dashboard"
sleep 3
docker exec -d atolyesefi bash -c "cd /workspace && python -m app.dashboard"
```

### Ne Zaman Build Gerekir vs Restart Gerekir

#### 🏗️ Docker Build Gerekir:
- `Dockerfile` değişiklikleri
- `requirements.txt` değişiklikleri
- Sistem seviyesi değişiklikler

#### 🔄 Sadece Restart Gerekir:
- `.py` dosya değişiklikleri
- Konfigürasyon değişiklikleri
- Template değişiklikleri

## 🔄 Güncelleme ve Bakım

### Image Güncelleme
```bash
# Yeni build
docker build -t atolyesefi:latest .

# Eski container'ı durdur
docker stop atolyesefi
docker rm atolyesefi

# Yeni container başlat
docker run ... atolyesefi:latest
```

### Temizlik
```bash
# Kullanılmayan image'ları temizle
docker image prune

# Kullanılmayan volume'ları temizle
docker volume prune

# Tüm Atölye Şefi container'larını durdur ve sil
docker ps -a --filter "name=atolyesefi" --format "{{.Names}}" | xargs -r docker stop
docker ps -a --filter "name=atolyesefi" --format "{{.Names}}" | xargs -r docker rm
```

## 🚀 Production Deployment

### Resource Requirements
- **CPU:** Minimum 4 cores, önerilen 8 cores
- **RAM:** Minimum 8GB, önerilen 16GB
- **GPU:** NVIDIA GPU (RTX serisi önerilir)
- **Disk:** SSD, minimum 50GB

### Security Considerations
```bash
# Güvenli şifre kullan
export SSH_ROOT_PASSWORD="$(openssl rand -base64 32)"

# Firewall kuralları
ufw allow 2222/tcp  # SSH
ufw allow 7860/tcp  # Gradio

# Log monitoring
tail -f logs/app.log | grep -E "(ERROR|WARN)"
```

### Monitoring
```bash
# Health check endpoint
curl -f http://localhost:7860/health

# Resource monitoring
docker stats atolyesefi --no-stream

# Log aggregation
docker logs atolyesefi | grep -E "(ERROR|CRITICAL)"
```

## 📚 Ek Kaynaklar

- **GitHub Repository:** [Atölye Şefi](https://github.com/berkay123001/Atolye_Sefi)
- **Docker Hub:** (Henüz yayınlanmadı)
- **Documentation:** README.md
- **Issues:** GitHub Issues sayfası
