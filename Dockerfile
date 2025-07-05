# =============================================================================
# Atölye Şefi - Production Docker Image
# =============================================================================
# Bu Dockerfile, Atölye Şefi projesi için anahtar teslim bir Docker imajı
# oluşturur. İçinde SSH sunucusu, Python bağımlılıkları ve Gradio arayüzü
# bulunur.
#
# Kullanım:
#   docker build -t atolyesefi:latest .
#   docker run -p 22:22 -p 7860:7860 atolyesefi:latest
# =============================================================================

# Temel imaj: RunPod'un PyTorch tabanlı CUDA imajı
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Metadata etiketleri
LABEL maintainer="Atölye Şefi Team"
LABEL description="Production-ready Docker image for Atölye Şefi AI Agent with SSH access"
LABEL version="1.0"

# Çevre değişkenleri
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# =============================================================================
# SSH SUNUCUSU KURULUMU
# =============================================================================

# Sistem paketlerini güncelle ve SSH sunucusunu kur
RUN apt-get update && \
    apt-get install -y \
        openssh-server \
        sudo \
        vim \
        nano \
        htop \
        curl \
        wget \
        git \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# SSH dizinini oluştur ve yapılandır
RUN mkdir /var/run/sshd

# SSH yapılandırması
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Root kullanıcısı için güvenli şifre belirle
# Üretim ortamında bu şifre bir secret olarak değiştirilmelidir
ARG SSH_ROOT_PASSWORD=AtolyeSefi2025!
RUN echo "root:${SSH_ROOT_PASSWORD}" | chpasswd

# SSH host anahtarlarını oluştur
RUN ssh-keygen -A

# =============================================================================
# UYGULAMA KURULUMU
# =============================================================================

# Çalışma dizinini ayarla
WORKDIR /app

# Önce requirements.txt'yi kopyala (Docker cache optimizasyonu için)
COPY requirements.txt /app/

# Python bağımlılıklarını yükle
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# RunPod API client için ek paketler
RUN pip install --no-cache-dir requests paramiko

# Proje dosyalarını kopyala
COPY . /app/

# Dosya izinlerini ayarla
RUN chmod +x /app/docker/start.sh

# Log dizinlerini oluştur
RUN mkdir -p /app/logs /var/log/atolyesefi

# =============================================================================
# PORT VE SERVİS YAPILANDIRMASI
# =============================================================================

# SSH portu
EXPOSE 22

# Gradio arayüz portu
EXPOSE 7860

# Jupyter Lab portu (opsiyonel)
EXPOSE 8888

# =============================================================================
# BAŞLANGIÇ KOMUTU
# =============================================================================

# Başlangıç betiğini entrypoint olarak ayarla
ENTRYPOINT ["/app/docker/start.sh"]

# Varsayılan komut
CMD ["--mode", "production"]
