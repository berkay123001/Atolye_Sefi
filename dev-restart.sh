#!/bin/bash
# =============================================================================
# Atölye Şefi - Development Restart Script
# =============================================================================
# Bu script kod değişikliklerinden sonra Docker container'ını hızlıca
# yeniden başlatmak için kullanılır.
#
# Kullanım: ./dev-restart.sh
# =============================================================================

set -e

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $1${NC}"
}

echo ""
echo "🔄 ATOLYE ŞEFİ - DEVELOPMENT RESTART"
echo "======================================"

# Container adı
CONTAINER_NAME="atolyesefi"

# Mevcut container'ı kontrol et
if docker ps -q --filter "name=$CONTAINER_NAME" | grep -q .; then
    log "Mevcut container durduruluyor..."
    docker stop $CONTAINER_NAME > /dev/null 2>&1
    log_success "Container durduruldu"
else
    log_warning "Çalışan container bulunamadı"
fi

# Container'ı sil (varsa)
if docker ps -aq --filter "name=$CONTAINER_NAME" | grep -q .; then
    log "Eski container siliniyor..."
    docker rm $CONTAINER_NAME > /dev/null 2>&1
    log_success "Container silindi"
fi

# Docker imajını yeniden build et
log "🔨 Docker imajı build ediliyor..."
if docker build -t atolyesefi:latest . > /dev/null 2>&1; then
    log_success "Docker build tamamlandı"
else
    log_error "Docker build başarısız!"
    exit 1
fi

# Yeni container'ı başlat
log "🚀 Yeni container başlatılıyor..."
docker run -d \
    --name $CONTAINER_NAME \
    -p 2222:22 \
    -p 7860:7860 \
    --env-file .env \
    atolyesefi:latest > /dev/null

if [ $? -eq 0 ]; then
    log_success "Container başarıyla başlatıldı!"
else
    log_error "Container başlatılamadı!"
    exit 1
fi

# Servisin başlaması için kısa bir bekleme
log "⏳ Servisin başlaması için 10 saniye bekleniyor..."
sleep 10

# Container durumunu kontrol et
CONTAINER_STATUS=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}")
if [[ "$CONTAINER_STATUS" == *"Up"* ]]; then
    log_success "Container çalışıyor: $CONTAINER_STATUS"
else
    log_error "Container durumu: $CONTAINER_STATUS"
    log "Container log'ları:"
    docker logs $CONTAINER_NAME | tail -10
    exit 1
fi

echo ""
echo "🎉 DEVELOPMENT RESTART TAMAMLANDI!"
echo "=================================="
echo ""
echo "📍 Erişim Bilgileri:"
echo "  🌐 Web Arayüzü: http://localhost:7860"
echo "  🔐 SSH Erişimi: ssh root@localhost -p 2222"
echo "  📋 Container Durumu: docker logs $CONTAINER_NAME -f"
echo ""
echo "💡 Faydalı Komutlar:"
echo "  docker logs $CONTAINER_NAME -f    # Log'ları takip et"
echo "  docker exec -it $CONTAINER_NAME bash    # Container'a bağlan"
echo "  docker stop $CONTAINER_NAME       # Container'ı durdur"
echo ""

# Son durum kontrolü
log "📊 Son durum kontrolleri..."

# Port kontrolü
if netstat -tuln 2>/dev/null | grep -q ":7860"; then
    log_success "Gradio portu (7860) açık"
else
    log_warning "Gradio portu henüz açık değil"
fi

if netstat -tuln 2>/dev/null | grep -q ":2222"; then
    log_success "SSH portu (2222) açık"
else
    log_warning "SSH portu henüz açık değil"
fi

log_success "Development environment hazır! 🚀"
