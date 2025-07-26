# 🖥️ Atölye Şefi - Modal VS Code Integration

Cloud-based VS Code environment with integrated AI agent capabilities running on Modal.com.

## 🎯 Features

### ✨ VS Code Environment
- **Browser-based VS Code** via OpenVSCode Server
- **Persistent workspace** with Modal volumes
- **Pre-configured Python environment** with all dependencies
- **Integrated debugging and task runners**

### 🤖 AI Agent Integration
- **ReactAgent V3** with real file creation capabilities
- **Modal.com serverless execution** for code running
- **Custom terminal commands** for agent interaction
- **Pre-loaded project structure** with all tools

### 🛠️ Development Tools
- Python 3.11 + all project dependencies
- Git, vim, nano, htop, tree
- Black formatter, flake8 linting
- Jupyter notebook support
- Custom VS Code tasks and launch configurations

## 🚀 Quick Start

### 1. Basic Setup
```bash
# Test workspace setup
modal run infrastructure.modal_vscode::setup_workspace

# Test agent functionality  
modal run infrastructure.modal_vscode::test_agent

# Start full VS Code environment
modal serve infrastructure.modal_vscode::vscode_server
```

### 2. Access VS Code
Once the server starts, Modal will provide a URL like:
```
https://username--atolye-sefi-vscode-vscode-server.modal.run
```

### 3. VS Code Environment
After opening VS Code in browser:
- **Workspace**: `/workspace/atolye-sefi`
- **Terminal commands**: 
  - `atolye-test` - Test agent integration
  - `atolye-dashboard` - Start Gradio dashboard  
  - `atolye-agent` - Run agent directly
  - `atolye-help` - Show help

## 🔧 Configuration

### Environment Variables
The system creates `.env` file automatically. Update with your keys:
```bash
GROQ_API_KEY=your_groq_api_key_here
MODAL_TOKEN_ID=your_modal_token_id_here
# ... other keys
```

### VS Code Settings
Pre-configured with:
- Python interpreter: `/usr/local/bin/python`
- Auto-save enabled
- Black formatter on save
- Dark theme
- Integrated terminal optimizations

### Available Tasks (Ctrl+Shift+P → "Tasks: Run Task")
- **Run Atölye Şefi Agent** - Test agent directly
- **Start Dashboard** - Launch Gradio interface
- **Test Agent Integration** - Run integration tests

## 📁 Project Structure in VS Code

```
/workspace/atolye-sefi/
├── agents/
│   ├── react_agent_v3.py      # Main AI agent
│   └── ...
├── tools/
│   ├── modal_executor.py      # Serverless execution
│   ├── advanced_test_categories.py
│   └── ...
├── app/
│   └── dashboard.py           # Gradio dashboard
├── infrastructure/
│   ├── modal_vscode.py        # This VS Code setup
│   └── README.md              # This file
├── .vscode/
│   ├── settings.json          # VS Code configuration
│   ├── tasks.json             # Custom tasks
│   └── launch.json            # Debug configurations
└── .env                       # Environment variables
```

## 🧪 Testing & Development

### Test Agent in VS Code Environment
```bash
# From terminal in VS Code
python agents/react_agent_v3.py

# Or use custom command
atolye-agent
```

### Test File Creation
```bash
# In VS Code terminal
python -c "
from agents.react_agent_v3 import ReactAgentV3
agent = ReactAgentV3()
result = agent.run('hesap makinesi kodu yaz ve calculator_test.py dosyasına kaydet')
print(result['result'])
"

# Check if file was created
ls -la calculator_test.py
```

### Test Dashboard
```bash
# Start dashboard (will be accessible via Modal URL)
atolye-dashboard

# Or run tests
atolye-test
```

## 🔄 Development Workflow

### 1. Start VS Code Environment
```bash
modal serve infrastructure.modal_vscode::vscode_server
```

### 2. Open Browser
Access the provided Modal URL to get full VS Code in browser

### 3. Develop & Test
- Edit agent code directly in VS Code
- Use integrated terminal for testing
- Files persist in Modal volume
- Real-time development with hot reloading

### 4. Test Agent Features
```bash
# Test basic chat
atolye-agent
# Then interact: "merhaba", "hesap makinesi yaz", etc.

# Test file creation
python -c "
from agents.react_agent_v3 import ReactAgentV3
agent = ReactAgentV3()
result = agent.run('Flask web uygulaması yaz ve app.py dosyasına kaydet')
print('Success:', 'Flask' in result['result'])
"
```

## 🛠️ Advanced Configuration

### Custom Extensions
VS Code extensions can be installed from the built-in marketplace.

### GPU Access
For ML workloads, modify the `@app.function` decorator:
```python
@app.function(
    image=vscode_image,
    gpu="A10G",  # Add GPU
    volumes={"/workspace": workspace_volume},
    ports=[3000]
)
```

### Resource Scaling
Adjust CPU/memory in `modal_vscode.py`:
```python
cpu=4,         # 4 CPU cores
memory=8192,   # 8GB RAM
```

## 📊 Monitoring & Logs

### View Logs
```bash
# Modal logs
modal logs atolye-sefi-vscode

# VS Code server logs (in VS Code terminal)
journalctl -f
```

### Performance Monitoring
- Use `htop` in VS Code terminal
- Monitor Modal dashboard for resource usage
- Check workspace volume usage

## 🔒 Security Notes

### Development Mode
Current setup runs without authentication for development:
```python
"--without-connection-token"  # Remove for production
```

### Production Setup
For production deployment:
1. Remove `--without-connection-token`
2. Add authentication configuration
3. Set up HTTPS with proper certificates
4. Restrict access with Modal's security features

## 🚨 Troubleshooting

### Common Issues

**VS Code won't start:**
```bash
# Check setup
modal run infrastructure.modal_vscode::setup_workspace

# View logs
modal logs atolye-sefi-vscode
```

**Agent can't create files:**
```bash
# Test workspace permissions
ls -la /workspace/atolye-sefi/
chmod 755 /workspace/atolye-sefi/
```

**Import errors:**
```bash
# Check Python path in VS Code terminal
python -c "import sys; print('\\n'.join(sys.path))"

# Reinstall dependencies
pip install -r requirements.txt
```

### Reset Workspace
```bash
# Delete and recreate volume
modal volume delete atolye-vscode-workspace
modal run infrastructure.modal_vscode::setup_workspace
```

## 📝 Next Steps

1. **Extensions**: Install Python extension pack
2. **Customization**: Modify VS Code settings in `.vscode/settings.json`
3. **Integration**: Add more custom terminal commands
4. **Deployment**: Configure for production use
5. **Scaling**: Add GPU support for ML workloads

## 🎉 Success Verification

Your setup is working correctly if:
- ✅ VS Code opens in browser
- ✅ `/workspace/atolye-sefi` contains project files
- ✅ `atolye-test` command works
- ✅ Agent can create and save files
- ✅ Python code execution works
- ✅ Terminal commands are available

**Happy coding in the cloud! 🚀**