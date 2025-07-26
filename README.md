# 🤖 Atölye Şefi (Workshop Chief)

**AI-powered serverless code execution system** using LangGraph-based agents on Modal.com cloud functions.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Modal.com](https://img.shields.io/badge/serverless-Modal.com-green.svg)](https://modal.com)
[![LangGraph](https://img.shields.io/badge/AI-LangGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 Features

### ⚡ **Ultra-Fast AI Agent**
- **ReactAgent V3** with real file creation capabilities
- **Intent-based routing** for lightning-fast responses (0.1s for chat, 0.5s for simple code)
- **LangGraph workflow orchestration** for complex multi-step tasks

### 🚀 **Serverless Code Execution**
- **Modal.com integration** for scalable cloud execution
- **GPU-accelerated ML workloads** when needed
- **Persistent file storage** with Modal volumes

### 🖥️ **Cloud Development Environment**
- **VS Code in browser** via OpenVSCode Server
- **Pre-configured Python environment** with all dependencies
- **Real-time file creation and editing** through web interface

### 📊 **Professional Infrastructure**
- **Structured logging system** with specialized log types
- **Performance monitoring** and health checks
- **Error tracking** with full context
- **Configuration management** for different environments

## 🚀 Quick Start

### 1. **Installation**
```bash
git clone <repository-url>
cd Atolye_Sefi
pip install -r requirements.txt
```

### 2. **Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Add your API keys
GROQ_API_KEY=your_groq_api_key_here
MODAL_TOKEN_ID=your_modal_token_id_here
MODAL_TOKEN_SECRET=your_modal_token_secret_here
```

### 3. **Modal.com Setup**
```bash
# Install Modal CLI
pip install modal

# Authenticate with Modal
modal token new

# Deploy functions
modal serve tools/modal_executor.py
```

### 4. **Start the System**

#### Option A: Dashboard Interface
```bash
python app/dashboard.py
# Access at: http://localhost:7860
```

#### Option B: Combined Modal + Dashboard
```bash
python modal_cloud_launcher.py
```

#### Option C: VS Code in Browser
```bash
modal serve -m infrastructure.modal_vscode_simple
# Access VS Code at the provided Modal URL
```

## 🏗️ Architecture

```
User Request → Gradio Dashboard → ReactAgent V3 → LangGraph Workflow → Modal.com Serverless Functions
```

### Core Components

- **`agents/react_agent_v3.py`** - Main AI agent with file creation
- **`tools/modal_executor.py`** - Modal.com serverless execution
- **`app/dashboard.py`** - Gradio web interface
- **`infrastructure/`** - VS Code cloud environment
- **`utils/logger.py`** - Professional logging system

## 📁 Project Structure

```
Atolye_Sefi/
├── agents/                 # AI agents
│   ├── react_agent_v3.py  # Main agent with file creation
│   └── ...
├── tools/                  # Execution tools
│   ├── modal_executor.py  # Modal.com integration
│   └── ...
├── app/                    # Web interfaces
│   └── dashboard.py       # Gradio dashboard
├── infrastructure/         # Cloud development environment
│   ├── modal_vscode.py    # VS Code server setup
│   └── README.md          # VS Code setup guide
├── utils/                  # Utilities
│   └── logger.py          # Professional logging
├── docs/                   # Documentation
└── config.py              # Configuration management
```

## 🎮 Usage Examples

### Chat & Information
```
User: "merhaba"
Agent: "🤖 Merhaba! Atölye Şefi burada - kod çalıştırmaya hazırım! ⚡"
```

### Code Execution
```
User: "2+2 hesapla"
Agent: "✅ Kod çalıştırıldı: 4"
```

### File Creation
```
User: "hesap makinesi kodu yaz ve dosyaya kaydet"
Agent: "🎉 Hesap makinesi başarıyla oluşturuldu! 
       📁 Dosya: hesap_makinesi.py"
```

## 🖥️ VS Code Development Environment

Experience cloud-based development with full VS Code in your browser:

```bash
# Start VS Code environment
modal serve -m infrastructure.modal_vscode_simple

# Features:
# ✅ Browser-based VS Code
# ✅ Pre-installed Python environment
# ✅ Integrated terminal
# ✅ File creation/editing
# ✅ Agent testing environment
```

See [VS_CODE_SETUP.md](VS_CODE_SETUP.md) for detailed setup guide.

## 📊 Performance Characteristics

- **Chat/Help queries**: 0.1s response time ⚡
- **Simple code patterns**: 0.5s via pattern matching
- **Complex code tasks**: 2-5s via Modal.com execution
- **Intent classification**: 0.001s (keyword-based)

## 🔧 Configuration

### Environment Variables
```bash
# Core API Keys
GROQ_API_KEY=your_groq_api_key_here
MODAL_TOKEN_ID=your_modal_token_id_here
MODAL_TOKEN_SECRET=your_modal_token_secret_here

# Agent Configuration
AGENT_MODEL_NAME=llama3-70b-8192
AGENT_SYSTEM_PROMPT=You are a helpful MLOps agent.
```

### Professional Features
- **Structured Logging**: All activities logged with context
- **Performance Monitoring**: Response time tracking
- **Error Handling**: Graceful error recovery
- **Health Checks**: System health monitoring

## 📈 Monitoring & Logs

The system provides comprehensive logging:

```bash
logs/
├── system.log              # System events
├── agent.log              # AI agent activities
├── user_interactions.log  # User analytics
├── errors.log             # Error tracking
└── atolye_sefi.log        # General logs
```

## 🧪 Testing

### Test Agent in Local Environment
```bash
python agents/react_agent_v3.py
```

### Test Dashboard Integration
```bash
python test_dashboard_integration.py
```

### Test in VS Code Environment
```bash
# After starting VS Code server
python -c "
from agents.react_agent_v3 import ReactAgentV3
agent = ReactAgentV3()
result = agent.run('hesap makinesi oluştur')
print(result['result'])
"
```

## 🚀 Professional Development

This project follows professional development practices:

- **Structured Architecture**: Modular design with clear separation
- **Professional Logging**: Enterprise-level logging system
- **Configuration Management**: Environment-based configurations
- **Cloud Development**: VS Code in browser for remote development
- **Performance Monitoring**: Real-time performance tracking

See [PROFESSIONAL_ROADMAP.md](PROFESSIONAL_ROADMAP.md) for development roadmap.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` directory
- **VS Code Setup**: See [VS_CODE_SETUP.md](VS_CODE_SETUP.md)
- **Issues**: Report issues on GitHub

## 🎉 Success Stories

✅ **Real File Creation**: Agent successfully creates and saves functional Python files
✅ **Cloud Development**: Full VS Code environment accessible from any browser
✅ **Lightning Fast**: 0.1s response times for chat interactions
✅ **Professional Logging**: All activities tracked with structured logging
✅ **Serverless Scale**: Powered by Modal.com for unlimited scalability

---

**Made with ❤️ using LangGraph, Modal.com, and professional development practices**