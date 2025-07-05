# 🏗️ Atölye Şefi - Proje Dosya İskeleti ve Açıklamaları

## 📂 Genel Proje Yapısı

```
Atolye_Sefi/
├── 🤖 agents/                      # AI Agent modülleri
│   ├── chief_agent.py              # Eski chief agent (artık kullanılmıyor)
│   ├── graph_agent.py              # Ana LangGraph tabanlı AI agent
│   └── __init__.py                 # Python package init
│
├── 🎨 app/                         # Web arayüzü ve dashboard
│   ├── dashboard.py                # Gradio web interface
│   └── __init__.py                 # Python package init
│
├── 🔧 tools/                       # AI Agent araçları
│   ├── architectural_tools.py      # Mimari tasarım araçları
│   ├── callback_handlers.py        # Callback yönetimi
│   ├── operational_tools.py        # RunPod API entegrasyonu
│   ├── pod_management_tools.py     # Temel pod yönetimi
│   ├── pod_management_tools_ssh.py # SSH tabanlı pod yönetimi
│   └── __init__.py                 # Python package init
│
├── 🐳 docker/                      # Docker yapılandırması
│   ├── build-and-test.sh           # Otomatik build ve test scripti
│   └── start.sh                    # Container başlangıç scripti
│
├── ⚙️ Yapılandırma Dosyaları
│   ├── config.py                   # Ana yapılandırma modülü
│   ├── .env                        # Çevre değişkenleri (gizli)
│   ├── requirements.txt            # Python bağımlılıkları
│   └── .gitignore                  # Git ignore kuralları
│
├── 🐳 Docker Dosyaları
│   ├── Dockerfile                  # Ana Docker imaj tanımı
│   ├── docker-compose.yml          # Docker Compose yapılandırması
│   ├── docker-compose.prod.yml     # Üretim override'ları
│   └── .dockerignore               # Docker build ignore kuralları
│
└── 📚 Dokümantasyon
    ├── README.md                   # Proje ana dokümantasyonu
    └── DOCKER_GUIDE.md             # Docker kullanım kılavuzu
```

## 📄 Dosya İçerikleri Detayı

### 🤖 AI Agent Katmanı

**`agents/graph_agent.py`** (1,067 satır) - **❤️ PROJENİN BEYNI**
```python
# LangGraph tabanlı çok adımlı AI agent
# - StateGraph ile workflow yönetimi
# - Multi-step memory sistemi
# - Plan-Execute-Response döngüsü
# - Tool parametrelerini otomatik parse etme
# - Conditional edges ile akıllı karar verme

class GraphAgent:
    - build_graph()     # LangGraph workflow'u oluşturur
    - plan_step()       # Kullanıcı talebini analiz eder
    - execute_step()    # Araçları kullanarak aksiyonlar alır
    - generate_response() # Nihai cevabı oluşturur
```

**`agents/chief_agent.py`** (Eski versiyon - artık kullanılmıyor)
```python
# Eski tekil-adım agent implementasyonu
# Backward compatibility için korunuyor
```

### 🎨 Web Interface Katmanı

**`app/dashboard.py`** (145 satır) - **🎭 KULLANICI ARAYÜZÜ**
```python
# Gradio tabanlı web dashboard
# - GraphAgent ile entegrasyon
# - Real-time chat interface
# - Log tracking sistemi
# - Health check endpoint

def run_agent_interaction() # Ana chat fonksiyonu
def health_check()          # Docker health endpoint
```

### 🔧 Tools Katmanı (AI Agent'ın Elleri)

**`tools/operational_tools.py`** (178 satır) - **🚀 RUNPOD ENTEGRASYONu**
```python
# RunPod GraphQL API entegrasyonu
# - GPU arama ve filtreleme
# - Pod oluşturma (volume mount ile)
# - Pod durum izleme

@tool find_and_prepare_gpu()  # GPU arar ve pod oluşturur
@tool check_gpu_status()      # GPU durumunu kontrol eder
```

**`tools/pod_management_tools_ssh.py`** (450 satır) - **🔐 SSH POD YÖNETİMİ**
```python
# SSH tabanlı uzak pod yönetimi
# - SSH erişimli pod oluşturma
# - Paramiko ile uzak komut çalıştırma
# - HTTP/Jupyter fallback sistemi

@tool prepare_environment_with_ssh() # SSH aktif pod oluşturur
@tool execute_command_via_ssh()      # SSH ile komut çalıştırır
def test_ssh_pod_workflow()          # Full entegrasyon testi
```

**`tools/architectural_tools.py`** - **🏗️ MİMARİ TASARIM**
```python
# Yazılım mimarisi ve tasarım araçları
# - Sistem tasarımı önerileri
# - Best practice rehberleri
# - Kod kalitesi kontrolleri
```

**`tools/pod_management_tools.py`** - **📦 TEMEL POD YÖNETİMİ**
```python
# Basit pod yönetimi araçları
# - Pod başlatma/durdurma
# - Durum kontrolü
# - Temel monitoring
```

**`tools/callback_handlers.py`** - **📞 CALLBACK YÖNETİMİ**
```python
# LangChain callback handlers
# - Tool çağrılarını izleme
# - Performance metrics
# - Debug ve logging
```

### ⚙️ Yapılandırma Katmanı

**`config.py`** (62 satır) - **⚙️ AYARLAR MERKEZİ**
```python
# Pydantic Settings tabanlı yapılandırma
# - API key'leri (.env'den)
# - Model isimleri ve parametreleri
# - Timeout ve retry ayarları

class Settings(BaseSettings):
    RUNPOD_API_KEY: str
    GROQ_API_KEY: str
    AGENT_MODEL_NAME: str = "llama-3.3-70b-versatile"
```

**`.env`** - **🔐 GİZLİ AYARLAR**
```bash
# Çevre değişkenleri (gizli, git'e dahil değil)
RUNPOD_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
SSH_ROOT_PASSWORD=AtolyeSefi2025!
```

**`requirements.txt`** (11 satır) - **📦 BAĞIMLILIKLAR**
```text
# Python package bağımlılıkları
langchain          # LLM framework
langchain-groq     # Groq provider
gradio            # Web interface
python-dotenv     # .env dosyası desteği
pydantic          # Data validation
langgraph         # Graph-based workflows
requests          # HTTP istekleri
paramiko          # SSH client
```

### 🐳 Docker Katmanı

**`Dockerfile`** (80 satır) - **🐳 KONTEYNER TARIFI**
```dockerfile
# Multi-stage professional Docker image
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# SSH server kurulumu
# Python bağımlılıkları
# Güvenlik ayarları
# Port açılması (22, 7860, 8888)
# Entrypoint: start.sh
```

**`docker/start.sh`** (200+ satır) - **🚀 BAŞLATMA ORKESTRATÖRü**
```bash
# Akıllı container başlatma scripti
# - SSH sunucusu başlatma
# - Gradio arayüzü başlatma
# - Health monitoring
# - Graceful shutdown
# - Error handling ve logging
```

**`docker/build-and-test.sh`** (150+ satır) - **🧪 OTOMATİK TEST**
```bash
# Docker build ve test otomasyonu
# - Image build
# - Container başlatma testi
# - Port erişilebilirlik testi
# - Health check testi
# - Python modül testi
# - Cleanup
```

**`docker-compose.yml`** (60 satır) - **🏗️ ORKESTRATİON**
```yaml
# Docker Compose yapılandırması
# - Service tanımları
# - Port mapping
# - Volume mounts
# - Environment variables
# - GPU access
# - Health checks
```

**`docker-compose.prod.yml`** (30 satır) - **🏭 ÜRETİM OVERRIDE**
```yaml
# Üretim ortamı ayarları
# - Resource limits
# - Performance tuning
# - Security hardening
# - Log configuration
```

**`.dockerignore`** (100+ satır) - **🚫 BUILD İGNORE**
```text
# Docker build'den hariç tutulacak dosyalar
# - .git, __pycache__, logs
# - Development files
# - Sensitive data
# - Large data files
```

### 📚 Dokümantasyon Katmanı

**`README.md`** - **📖 ANA DOKÜMANTASYON**
```markdown
# Proje tanıtımı
# Kurulum talimatları
# Kullanım örnekleri
# API referansları
# Contribution guidelines
```

**`DOCKER_GUIDE.md`** (300+ satır) - **🐳 DOCKER KILAVUZU**
```markdown
# Docker kullanım kılavuzu
# Build ve run talimatları
# Troubleshooting
# Production deployment
# Performance tuning
```

**`.gitignore`** - **🚫 GIT İGNORE**
```text
# Git'e dahil edilmeyecek dosyalar
# __pycache__, .env, logs
# IDE settings
# OS specific files
```

## 🔄 Dosya İlişkileri ve Akış

```
User Request → dashboard.py → graph_agent.py → tools/* → RunPod API
     ↓              ↓              ↓              ↓         ↓
   Gradio     GraphAgent    LangGraph     Tool Calls   GPU Pods
   Interface   Workflow     StateGraph    (SSH/HTTP)   Creation
```

## 📊 Kod İstatistikleri

- **Toplam Dosya:** 23
- **Toplam Dizin:** 5
- **Python Kodu:** ~2,500 satır
- **Bash Scripts:** ~400 satır
- **Docker Config:** ~200 satır
- **Dokümantasyon:** ~500 satır

## 🎯 Ana Özellikler

- ✅ **Multi-step AI Agent** (LangGraph)
- ✅ **RunPod GPU Entegrasyonu**
- ✅ **SSH Pod Management**
- ✅ **Web Dashboard** (Gradio)
- ✅ **Docker Containerization**
- ✅ **Production Ready**
- ✅ **Comprehensive Testing**
- ✅ **Full Documentation**
