#!/bin/bash
# =============================================================================
# Atölye Şefi - Docker Container Startup Script
# =============================================================================
# Bu betik Docker konteynerı başladığında çalışır ve gerekli servisleri
# paralel olarak başlatır.
#
# Kullanım:
#   ./start.sh [OPTIONS]
#
# Seçenekler:
#   --mode production    : Üretim modu (varsayılan)
#   --mode development   : Geliştirme modu
#   --no-ssh            : SSH sunucusunu başlatma
#   --no-gradio         : Gradio arayüzünü başlatma
# =============================================================================

set -e  # Hata durumunda betiği durdur

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log fonksiyonu
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Varsayılan değerler
MODE="production"
START_SSH=true
START_GRADIO=true

# Komut satırı argümanlarını işle
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --no-ssh)
            START_SSH=false
            shift
            ;;
        --no-gradio)
            START_GRADIO=false
            shift
            ;;
        -h|--help)
            echo "Atölye Şefi Docker Startup Script"
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode production     Production mode (default)"
            echo "  --mode development    Development mode"
            echo "  --no-ssh             Don't start SSH server"
            echo "  --no-gradio          Don't start Gradio interface"
            echo "  -h, --help           Show this help"
            exit 0
            ;;
        *)
            log_error "Bilinmeyen parametre: $1"
            exit 1
            ;;
    esac
done

log "🚀 Atölye Şefi Docker Container başlatılıyor..."
log "📋 Mod: $MODE"
log "🔧 SSH: $START_SSH, Gradio: $START_GRADIO"

# =============================================================================
# ÖN KONTROLLER VE YAPILANDIRMA
# =============================================================================

log "🔍 Sistem kontrolleri yapılıyor..."

# Python sürümünü kontrol et
PYTHON_VERSION=$(python --version 2>&1)
log "🐍 $PYTHON_VERSION"

# CUDA kontrol
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
    log_success "🎮 GPU: $GPU_INFO"
else
    log_warning "GPU bulunamadı veya CUDA kurulu değil"
fi

# Gerekli dosyaların varlığını kontrol et
if [ ! -f "/app/config.py" ]; then
    log_error "config.py dosyası bulunamadı!"
    exit 1
fi

if [ ! -f "/app/.env" ]; then
    log_warning ".env dosyası bulunamadı, environment variables'ları kontrol edin"
fi

# Log dizinlerini oluştur
mkdir -p /app/logs /var/log/atolyesefi

# =============================================================================
# SSH SUNUCUSU BAŞLATMA
# =============================================================================

if [ "$START_SSH" = true ]; then
    log "🔐 SSH sunucusu başlatılıyor..."
    
    # SSH host keys kontrolü
    if [ ! -f "/etc/ssh/ssh_host_rsa_key" ]; then
        log "🔑 SSH host keys oluşturuluyor..."
        ssh-keygen -A
    fi
    
    # SSH daemon'unu başlat
    /usr/sbin/sshd -D &
    SSH_PID=$!
    
    # SSH servisinin başlamasını bekle
    sleep 2
    
    if kill -0 $SSH_PID 2>/dev/null; then
        log_success "SSH sunucusu başarıyla başlatıldı (PID: $SSH_PID)"
        log "🌐 SSH erişimi: ssh root@<container_ip> (port 22)"
    else
        log_error "SSH sunucusu başlatılamadı!"
        exit 1
    fi
else
    log_warning "SSH sunucusu devre dışı bırakıldı"
fi

# =============================================================================
# PYTHON ORTAMI KONTROLÜ
# =============================================================================

log "🔍 Python paketleri kontrol ediliyor..."

# Temel paketlerin kurulu olduğunu kontrol et
REQUIRED_PACKAGES=("langchain" "gradio" "requests" "paramiko")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        log_success "📦 $package kurulu"
    else
        log_error "📦 $package eksik! requirements.txt'yi kontrol edin."
        exit 1
    fi
done

# =============================================================================
# GRADIO ARAYÜZÜ BAŞLATMA
# =============================================================================

if [ "$START_GRADIO" = true ]; then
    log "🎨 Gradio arayüzü başlatılıyor..."
    
    # Geliştirme modu için ek ayarlar
    if [ "$MODE" = "development" ]; then
        export GRADIO_SERVER_NAME="0.0.0.0"
        export GRADIO_SERVER_PORT="7860"
        export GRADIO_DEBUG="1"
        log "🔧 Geliştirme modu ayarları aktif"
    else
        export GRADIO_SERVER_NAME="0.0.0.0"
        export GRADIO_SERVER_PORT="7860"
        export GRADIO_DEBUG="0"
    fi
    
    # Gradio uygulamasını başlat
    cd /app
    python -m app.dashboard &
    GRADIO_PID=$!
    
    # Gradio'nun başlamasını bekle
    sleep 5
    
    if kill -0 $GRADIO_PID 2>/dev/null; then
        log_success "Gradio arayüzü başarıyla başlatıldı (PID: $GRADIO_PID)"
        log "🌐 Web arayüzü: http://<container_ip>:7860"
    else
        log_error "Gradio arayüzü başlatılamadı!"
        # Log dosyasını kontrol et
        if [ -f "/app/logs/gradio.log" ]; then
            log "📋 Gradio log:"
            tail -10 /app/logs/gradio.log
        fi
        exit 1
    fi
else
    log_warning "Gradio arayüzü devre dışı bırakıldı"
fi

# =============================================================================
# HEALTH CHECK VE İZLEME
# =============================================================================

log_success "🎉 Tüm servisler başarıyla başlatıldı!"
log "📊 Sistem durumu:"

if [ "$START_SSH" = true ]; then
    echo "  🔐 SSH Server: RUNNING (PID: $SSH_PID)"
fi

if [ "$START_GRADIO" = true ]; then
    echo "  🎨 Gradio Interface: RUNNING (PID: $GRADIO_PID)"
fi

echo "  🐍 Python: $(python --version)"
echo "  📂 Working Directory: $(pwd)"
echo "  👤 User: $(whoami)"

log "🔄 Sistem izleme moduna geçiliyor..."

# Cleanup function
cleanup() {
    log "🛑 Kapatma sinyali alındı, servisler durduruluyor..."
    
    if [ "$START_GRADIO" = true ] && kill -0 $GRADIO_PID 2>/dev/null; then
        log "🎨 Gradio durduruluyor..."
        kill $GRADIO_PID
        wait $GRADIO_PID 2>/dev/null
    fi
    
    if [ "$START_SSH" = true ] && kill -0 $SSH_PID 2>/dev/null; then
        log "🔐 SSH durduruluyor..."
        kill $SSH_PID
        wait $SSH_PID 2>/dev/null
    fi
    
    log_success "✅ Tüm servisler temiz bir şekilde durduruldu"
    exit 0
}

# Signal handlers
trap cleanup SIGTERM SIGINT

# Ana izleme döngüsü
while true; do
    # SSH durumunu kontrol et
    if [ "$START_SSH" = true ] && ! kill -0 $SSH_PID 2>/dev/null; then
        log_error "SSH sunucusu beklenmedik şekilde durdu!"
        exit 1
    fi
    
    # Gradio durumunu kontrol et
    if [ "$START_GRADIO" = true ] && ! kill -0 $GRADIO_PID 2>/dev/null; then
        log_error "Gradio arayüzü beklenmedik şekilde durdu!"
        exit 1
    fi
    
    # Her 30 saniyede kontrol et
    sleep 30
done
