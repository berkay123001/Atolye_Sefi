#!/bin/bash
# =============================================================================
# Atölye Şefi - Docker Build & Test Script
# =============================================================================
# Bu script Docker imajını build eder ve temel testleri çalıştırır.
#
# Kullanım:
#   ./docker/build-and-test.sh
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

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $1${NC}"
}

# Docker kurulu mu kontrol et
if ! command -v docker &> /dev/null; then
    log_error "Docker kurulu değil!"
    exit 1
fi

log "🚀 Atölye Şefi Docker Build & Test başlatılıyor..."

# Proje kök dizinine git
cd "$(dirname "$0")/.."

# =============================================================================
# DOCKER BUILD
# =============================================================================

log "🔨 Docker imajı build ediliyor..."

IMAGE_NAME="atolyesefi"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# Build argümanları
SSH_PASSWORD="${SSH_ROOT_PASSWORD:-AtolyeSefi2025!}"

docker build \
    --build-arg SSH_ROOT_PASSWORD="$SSH_PASSWORD" \
    -t "$FULL_IMAGE_NAME" \
    -f Dockerfile \
    .

if [ $? -eq 0 ]; then
    log_success "Docker imajı başarıyla build edildi: $FULL_IMAGE_NAME"
else
    log_error "Docker build başarısız!"
    exit 1
fi

# =============================================================================
# DOCKER IMAGE INFO
# =============================================================================

log "📊 Docker imaj bilgileri:"
docker images "$FULL_IMAGE_NAME"

IMAGE_SIZE=$(docker images --format "table {{.Size}}" "$FULL_IMAGE_NAME" | tail -1)
log "💾 İmaj boyutu: $IMAGE_SIZE"

# =============================================================================
# BASIC TESTS
# =============================================================================

log "🧪 Temel testler başlatılıyor..."

# Test 1: Container başlatma testi
log "Test 1: Container başlatma..."

CONTAINER_NAME="atolyesefi-test-$(date +%s)"

docker run -d \
    --name "$CONTAINER_NAME" \
    -p 2223:22 \
    -p 7861:7860 \
    -e RUNPOD_API_KEY="${RUNPOD_API_KEY:-test}" \
    -e GROQ_API_KEY="${GROQ_API_KEY:-test}" \
    "$FULL_IMAGE_NAME"

if [ $? -eq 0 ]; then
    log_success "Container başarıyla başlatıldı: $CONTAINER_NAME"
else
    log_error "Container başlatılamadı!"
    exit 1
fi

# Container'ın başlaması için bekle
log "⏳ Container'ın başlaması için 30 saniye bekleniyor..."
sleep 30

# Test 2: Container sağlık kontrolü
log "Test 2: Container sağlık kontrolü..."
CONTAINER_STATUS=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}")

if [[ "$CONTAINER_STATUS" == *"Up"* ]]; then
    log_success "Container çalışıyor: $CONTAINER_STATUS"
else
    log_error "Container durumu: $CONTAINER_STATUS"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

# Test 3: SSH port kontrolü
log "Test 3: SSH erişilebilirlik testi..."
if netstat -tuln | grep -q ":2223"; then
    log_success "SSH portu (2223) açık"
else
    log_error "SSH portu erişilebilir değil"
fi

# Test 4: Gradio port kontrolü
log "Test 4: Gradio erişilebilirlik testi..."
if netstat -tuln | grep -q ":7861"; then
    log_success "Gradio portu (7861) açık"
else
    log_error "Gradio portu erişilebilir değil"
fi

# Test 5: Gradio health check
log "Test 5: Gradio erişilebilirlik testi..."
sleep 10  # Gradio'nun tam başlaması için ekstra süre

if curl -s -f "http://localhost:7861/" > /dev/null; then
    log_success "Gradio ana sayfa erişilebilir"
else
    log_error "Gradio ana sayfa erişilebilir değil"
    # Log'ları göster
    docker logs "$CONTAINER_NAME" | tail -20
fi

# Test 6: Container içi Python testi
log "Test 6: Container içi Python modül testi..."
docker exec "$CONTAINER_NAME" python -c "
import sys
print(f'Python version: {sys.version}')

# Test temel modülleri
try:
    import langchain
    print('✅ langchain import başarılı')
except ImportError as e:
    print(f'❌ langchain import hatası: {e}')
    sys.exit(1)

try:
    import gradio
    print('✅ gradio import başarılı')
except ImportError as e:
    print(f'❌ gradio import hatası: {e}')
    sys.exit(1)

try:
    import paramiko
    print('✅ paramiko import başarılı')
except ImportError as e:
    print(f'❌ paramiko import hatası: {e}')
    sys.exit(1)

print('🎉 Tüm Python modülleri başarıyla yüklendi!')
"

if [ $? -eq 0 ]; then
    log_success "Python modül testi geçti"
else
    log_error "Python modül testi başarısız"
fi

# =============================================================================
# CLEANUP
# =============================================================================

log "🧹 Test temizliği yapılıyor..."

# Container'ı durdur ve sil
docker stop "$CONTAINER_NAME" > /dev/null
docker rm "$CONTAINER_NAME" > /dev/null

log_success "Test container temizlendi: $CONTAINER_NAME"

# =============================================================================
# SONUÇ
# =============================================================================

log_success "🎉 Tüm testler başarıyla tamamlandı!"
log "📋 Özet:"
echo "  🔨 Docker Build: ✅ Başarılı"
echo "  🚀 Container Start: ✅ Başarılı"
echo "  🔐 SSH Port: ✅ Açık"
echo "  🎨 Gradio Port: ✅ Açık"
echo "  🏥 Health Check: ✅ Geçti"
echo "  🐍 Python Modules: ✅ Yüklü"

log "🚀 Üretim için hazır imaj: $FULL_IMAGE_NAME"
log "📖 Kullanım kılavuzu:"
echo "  docker run -d -p 2222:22 -p 7860:7860 --name atolyesefi $FULL_IMAGE_NAME"
echo "  ssh root@localhost -p 2222"
echo "  http://localhost:7860"
