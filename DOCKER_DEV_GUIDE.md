# 🐳 Atölye Şefi - Docker Development Rehberi

## 🚀 Günlük Geliştirme Workflow'u

### 📋 Durum Kontrolleri

```bash
# Container'ların durumunu kontrol et
docker ps -a

# Çalışan container'ları göster
docker ps

# Atölye Şefi container'ını bul
docker ps -a --filter "name=atolyesefi"

# Container log'larını göster
docker logs atolyesefi -f
```

### 🔄 Kod Güncelleme Adımları

#### Senaryo 1: Küçük değişiklikler
```bash
# 1. VS Code'da kodunu düzenle
# 2. Hızlı test için yeniden build
docker build -t atolyesefi:latest .

# 3. Container'ı yeniden başlat
docker stop atolyesefi && docker rm atolyesefi
docker run -d -p 2222:22 -p 7860:7860 --name atolyesefi atolyesefi:latest
```

#### Senaryo 2: Kapsamlı değişiklikler
```bash
# Tam test ile birlikte
./docker/build-and-test.sh
```

### 💡 Development Hileleri

#### Hızlı Restart (aynı kod ile)
```bash
# Sadece container'ı yeniden başlat (kod aynı)
docker restart atolyesefi
```

#### Volume Mount ile Development
```bash
# Kodu değiştirince otomatik yansısin
docker run -d \
  -p 2222:22 -p 7860:7860 \
  -v $(pwd):/app \
  --name atolyesefi-dev \
  atolyesefi:latest
```

#### Container içinde test
```bash
# Container'a bağlan
docker exec -it atolyesefi bash

# İçinde kod çalıştır
cd /app
python -m app.dashboard
```

### 🔍 Problem Çözme

#### Container başlamıyor
```bash
# Log'ları kontrol et
docker logs atolyesefi

# İnteraktif modda başlat
docker run -it --rm atolyesefi:latest bash
```

#### Port çakışması
```bash
# Farklı portlar kullan
docker run -d -p 2224:22 -p 7862:7860 --name atolyesefi2 atolyesefi:latest
```

#### Disk alanı
```bash
# Eski imajları temizle
docker image prune

# Kullanılmayan her şeyi temizle
docker system prune -a
```

## 🎯 En İyi Pratikler

### ✅ Development Workflow
1. **Kod yaz** (VS Code'da)
2. **Test et** (lokal Python ile)
3. **Build et** (`docker build`)
4. **Test et** (`./docker/build-and-test.sh`)
5. **Deploy et** (container başlat)

### ✅ Production Workflow
```bash
# Üretim için optimize build
docker build -t atolyesefi:prod .

# Docker Compose ile
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### ✅ Backup & Restore
```bash
# İmajı kaydet
docker save atolyesefi:latest > atolyesefi-backup.tar

# İmajı yükle
docker load < atolyesefi-backup.tar
```

## 🛠️ Automation Scripts

### Hızlı Geliştirme Scripti
```bash
#!/bin/bash
# dev-restart.sh
echo "🔄 Development restart..."
docker stop atolyesefi 2>/dev/null
docker rm atolyesefi 2>/dev/null
docker build -t atolyesefi:latest .
docker run -d -p 2222:22 -p 7860:7860 --name atolyesefi atolyesefi:latest
echo "✅ Container yeniden başlatıldı!"
echo "🌐 Web: http://localhost:7860"
echo "🔐 SSH: ssh root@localhost -p 2222"
```

### Monitoring Script
```bash
#!/bin/bash
# monitor.sh
watch -n 5 'docker ps --filter "name=atolyesefi" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```

## 📱 VS Code Integration

### Dev Containers Extension
```json
// .devcontainer/devcontainer.json
{
  "name": "Atölye Şefi Dev",
  "build": {
    "dockerfile": "../Dockerfile"
  },
  "forwardPorts": [7860, 22],
  "mounts": [
    "source=${localWorkspaceFolder},target=/app,type=bind"
  ]
}
```

### Tasks.json
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Docker Build",
      "type": "shell",
      "command": "docker build -t atolyesefi:latest .",
      "group": "build"
    },
    {
      "label": "Docker Run",
      "type": "shell",
      "command": "docker run -d -p 2222:22 -p 7860:7860 --name atolyesefi atolyesefi:latest",
      "group": "build"
    }
  ]
}
```

## 🚨 Yaygın Hatalar ve Çözümleri

### Hata 1: "Port already in use"
```bash
# Çözüm: Başka port kullan
docker run -d -p 2224:22 -p 7862:7860 --name atolyesefi atolyesefi:latest
```

### Hata 2: "Container name already exists"
```bash
# Çözüm: Eski container'ı sil
docker rm atolyesefi
# veya farklı isim kullan
docker run --name atolyesefi-v2 ...
```

### Hata 3: "No space left on device"
```bash
# Çözüm: Temizlik yap
docker system prune -a
docker volume prune
```

### Hata 4: "Permission denied"
```bash
# Çözüm: Docker grup izni
sudo usermod -aG docker $USER
# Logout/login gerekli
```

## 🎮 Hızlı Komutlar Cheat Sheet

```bash
# 🔍 KONTROL
docker ps                              # Çalışan container'lar
docker ps -a                           # Tüm container'lar
docker images                          # İmajlar
docker logs atolyesefi                 # Log'lar

# 🔄 YÖNETİM  
docker stop atolyesefi                 # Durdur
docker start atolyesefi                # Başlat
docker restart atolyesefi              # Yeniden başlat
docker rm atolyesefi                   # Sil

# 🔨 BUILD
docker build -t atolyesefi:latest .    # Build
docker run -d --name atolyesefi ...    # Çalıştır

# 🧹 TEMİZLİK
docker container prune                 # Durmuş container'ları sil
docker image prune                     # Kullanılmayan imajları sil
docker system prune -a                 # Her şeyi temizle

# 📊 İSTATİSTİK
docker stats atolyesefi                # Resource kullanımı
docker exec -it atolyesefi bash        # Container'a bağlan
```
