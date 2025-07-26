#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - MODAL + OPENVSCODE SERVER INTEGRATION
Cloud-based VS Code environment with integrated AI agent capabilities
"""

import modal
import os
import subprocess
import time
from pathlib import Path

# Initialize Modal app
app = modal.App("atolye-sefi-vscode")

# 🏗️ WORKSPACE VOLUME - Persistent file storage
workspace_volume = modal.Volume.from_name("atolye-vscode-workspace", create_if_missing=True)

# 🐳 CUSTOM IMAGE - VS Code Server + Python Development Environment
vscode_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install([
        # Essential packages
        "curl", "wget", "git", "build-essential", "software-properties-common",
        # VS Code Server dependencies  
        "libnss3", "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0", "libgbm1",
        "libasound2", "libatspi2.0-0", "libgtk-3-0", "libxss1", "libgconf-2-4",
        # Development tools
        "vim", "nano", "htop", "tree", "unzip", "jq"
    ])
    .pip_install([
        # Core dependencies
        "modal", "langchain", "langchain-groq", "langchain-core", "langchain-community",
        # Data science & ML
        "pandas", "numpy", "matplotlib", "scikit-learn", "torch", "transformers",
        # Web & API
        "fastapi", "uvicorn", "requests", "aiohttp", "gradio",
        # Development tools
        "black", "flake8", "pytest", "jupyter", "ipython", "pydantic", "pydantic-settings",
        # Project specific
        "python-dotenv", "typing-extensions"
    ])
    .run_commands([
        # Download and install OpenVSCode Server
        "cd /tmp && curl -fsSL https://github.com/gitpod-io/openvscode-server/releases/download/openvscode-server-v1.85.2/openvscode-server-v1.85.2-linux-x64.tar.gz | tar -xz",
        "mv /tmp/openvscode-server-v1.85.2-linux-x64 /opt/openvscode-server",
        "chmod +x /opt/openvscode-server/bin/openvscode-server",
        
        # Create workspace directory structure
        "mkdir -p /workspace/atolye-sefi",
        "mkdir -p /workspace/.vscode-server",
        "mkdir -p /workspace/.local/share",
        
        # Set proper permissions
        "chown -R root:root /workspace",
        "chmod -R 755 /workspace"
    ])
    # Copy our project files into the image
    .add_local_dir(".", "/workspace/atolye-sefi")
    .workdir("/workspace/atolye-sefi")
)

def setup_vscode_workspace():
    """Configure VS Code workspace with optimal settings"""
    
    # VS Code workspace settings
    vscode_settings = {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.terminal.activateEnvironment": True,
        "terminal.integrated.defaultProfile.linux": "bash",
        "files.autoSave": "onDelay",
        "files.autoSaveDelay": 1000,
        "editor.formatOnSave": True,
        "python.formatting.provider": "black",
        "python.linting.enabled": True,
        "python.linting.flake8Enabled": True,
        "workbench.colorTheme": "Default Dark+",
        "editor.fontSize": 14,
        "terminal.integrated.fontSize": 13,
        "explorer.confirmDelete": False,
        "git.autofetch": True,
        "extensions.autoUpdate": False
    }
    
    # Create .vscode directory and settings
    vscode_dir = Path("/workspace/atolye-sefi/.vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    import json
    with open(vscode_dir / "settings.json", "w") as f:
        json.dump(vscode_settings, f, indent=2)
    
    # Create launch configuration for debugging
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Atölye Şefi Agent",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/agents/react_agent_v3.py",
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}"
            },
            {
                "name": "Python: Dashboard",
                "type": "python", 
                "request": "launch",
                "program": "${workspaceFolder}/app/dashboard.py",
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}"
            }
        ]
    }
    
    with open(vscode_dir / "launch.json", "w") as f:
        json.dump(launch_config, f, indent=2)
    
    # Create tasks for common operations
    tasks_config = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Run Atölye Şefi Agent",
                "type": "shell",
                "command": "python",
                "args": ["agents/react_agent_v3.py"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "new"
                }
            },
            {
                "label": "Start Dashboard",
                "type": "shell", 
                "command": "python",
                "args": ["app/dashboard.py"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always", 
                    "focus": False,
                    "panel": "new"
                }
            },
            {
                "label": "Test Agent Integration",
                "type": "shell",
                "command": "python", 
                "args": ["test_dashboard_integration.py"],
                "group": "test"
            }
        ]
    }
    
    with open(vscode_dir / "tasks.json", "w") as f:
        json.dump(tasks_config, f, indent=2)
    
    print("✅ VS Code workspace configured successfully!")

def setup_agent_environment():
    """Setup Atölye Şefi agent environment variables and configuration"""
    
    # Create .env file with necessary configurations
    env_content = """# Atölye Şefi Environment Configuration
# Generated by Modal VS Code setup

# Required API Keys (set these with your actual keys)
GROQ_API_KEY=your_groq_api_key_here
RUNPOD_API_KEY=your_runpod_api_key_here
MODAL_TOKEN_ID=your_modal_token_id_here

# Optional API Keys
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Agent Configuration
AGENT_MODEL_NAME=llama3-70b-8192
AGENT_SYSTEM_PROMPT=You are a helpful MLOps agent.
RUNPOD_SIMULATION_MODE=true

# VS Code Integration
VSCODE_WORKSPACE=/workspace/atolye-sefi
MODAL_ENVIRONMENT=vscode
"""
    
    with open("/workspace/atolye-sefi/.env", "w") as f:
        f.write(env_content)
    
    # Create agent startup script
    startup_script = """#!/bin/bash
# Atölye Şefi Agent Startup Script

echo "🚀 Atölye Şefi - VS Code Environment"
echo "=================================="
echo ""
echo "📁 Workspace: /workspace/atolye-sefi"
echo "🧠 Agent: ReactAgent V3 with file creation"
echo "🔧 Tools: Modal.com serverless execution"
echo ""
echo "Available commands:"
echo "  atolye-test    - Test agent integration"
echo "  atolye-dashboard - Start Gradio dashboard"
echo "  atolye-agent   - Run agent directly"
echo ""
"""
    
    with open("/workspace/atolye-sefi/startup.sh", "w") as f:
        f.write(startup_script)
    
    os.chmod("/workspace/atolye-sefi/startup.sh", 0o755)
    
    # Create custom terminal commands
    bashrc_addition = """
# Atölye Şefi Custom Commands
alias atolye-test='python test_dashboard_integration.py'
alias atolye-dashboard='python app/dashboard.py'
alias atolye-agent='python agents/react_agent_v3.py'
alias atolye-help='cat startup.sh'

# Welcome message
if [ -f "/workspace/atolye-sefi/startup.sh" ]; then
    /workspace/atolye-sefi/startup.sh
fi
"""
    
    with open("/root/.bashrc", "a") as f:
        f.write(bashrc_addition)
    
    print("✅ Agent environment configured successfully!")

@modal.web_endpoint(
    image=vscode_image,
    volumes={"/workspace": workspace_volume},
    timeout=3600,  # 1 hour timeout
    min_containers=1,   # Keep one instance warm
    allow_concurrent_inputs=5,
    cpu=2,         # 2 CPU cores
    memory=4096,   # 4GB RAM
)
def vscode_server():
    """
    🖥️ Start OpenVSCode Server with Atölye Şefi integration
    
    Provides:
    - Browser-based VS Code environment
    - Pre-configured Python development setup
    - Integrated Atölye Şefi agent tools
    - Persistent workspace storage
    """
    
    print("🚀 Starting Atölye Şefi VS Code Environment...")
    
    # Setup workspace and environment
    setup_vscode_workspace()
    setup_agent_environment()
    
    # Change to workspace directory
    os.chdir("/workspace/atolye-sefi")
    
    # Start OpenVSCode Server
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "3000",
        "--without-connection-token",  # Development mode - remove for production
        "--accept-server-license-terms",
        "--server-data-dir", "/workspace/.vscode-server",
        "--user-data-dir", "/workspace/.local/share",
        "--extensions-dir", "/workspace/.vscode-extensions"
    ]
    
    print("🌐 VS Code Server starting on port 3000...")
    print("📁 Workspace: /workspace/atolye-sefi")
    print("🔗 Access URL will be provided by Modal...")
    
    # Start the server
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Monitor the server
    try:
        while True:
            output = process.stdout.readline()
            if output:
                print(f"[VS Code] {output.strip()}")
            elif process.poll() is not None:
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("🛑 Shutting down VS Code Server...")
        process.terminate()
        process.wait()
    
    return "VS Code Server stopped"

@app.function(
    image=vscode_image,
    volumes={"/workspace": workspace_volume},
    timeout=300,
    cpu=1,
    memory=1024
)
def setup_workspace():
    """
    🔧 Setup and verify workspace configuration
    Useful for testing and troubleshooting
    """
    
    print("🔧 Setting up Atölye Şefi workspace...")
    
    # Setup configurations
    setup_vscode_workspace()
    setup_agent_environment()
    
    # Verify setup
    workspace_path = Path("/workspace/atolye-sefi")
    
    verification_results = {
        "workspace_exists": workspace_path.exists(),
        "agents_dir": (workspace_path / "agents").exists(),
        "tools_dir": (workspace_path / "tools").exists(),
        "vscode_settings": (workspace_path / ".vscode" / "settings.json").exists(),
        "env_file": (workspace_path / ".env").exists(),
        "agent_v3": (workspace_path / "agents" / "react_agent_v3.py").exists()
    }
    
    print("📊 Workspace Verification Results:")
    for check, result in verification_results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}: {result}")
    
    # List key files
    if workspace_path.exists():
        print(f"\n📁 Workspace Contents:")
        for item in sorted(workspace_path.iterdir()):
            if item.is_dir():
                print(f"  📁 {item.name}/")
            else:
                print(f"  📄 {item.name}")
    
    return verification_results

# 🚀 DEVELOPMENT HELPER FUNCTIONS

@app.function(
    image=vscode_image,
    volumes={"/workspace": workspace_volume},
    timeout=60
)
def test_agent():
    """
    🧪 Test Atölye Şefi agent in VS Code environment
    """
    
    os.chdir("/workspace/atolye-sefi")
    
    print("🧪 Testing Atölye Şefi Agent in VS Code environment...")
    
    try:
        # Import and test agent
        import sys
        sys.path.append("/workspace/atolye-sefi")
        
        from agents.react_agent_v3 import ReactAgentV3
        
        agent = ReactAgentV3()
        
        # Test basic functionality
        test_queries = [
            "merhaba",
            "2+2 hesapla", 
            "hesap makinesi kodu yaz ve test_calculator.py dosyasına kaydet"
        ]
        
        results = []
        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            result = agent.run(query)
            results.append({
                "query": query,
                "success": not result["result"].startswith("❌"),
                "execution_time": result.get("execution_time", 0),
                "method": result.get("method", "unknown")
            })
            print(f"✅ Result: {result['result'][:100]}...")
        
        # Check if files were created
        test_calc_exists = Path("/workspace/atolye-sefi/test_calculator.py").exists()
        
        summary = {
            "agent_tests": results,
            "file_creation_test": test_calc_exists,
            "workspace_writable": True,
            "total_tests": len(test_queries),
            "passed_tests": sum(1 for r in results if r["success"])
        }
        
        print(f"\n📊 Test Summary:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed_tests']}")
        print(f"  File Creation: {'✅' if test_calc_exists else '❌'}")
        
        return summary
        
    except Exception as e:
        print(f"❌ Agent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# 🎯 MAIN ENTRY POINTS

@app.local_entrypoint()
def main():
    """
    🎯 Main entry point for VS Code environment
    
    Usage:
        modal run infrastructure.modal_vscode::main
    """
    print("🚀 Atölye Şefi - Modal VS Code Integration")
    print("=" * 50)
    
    # Test workspace setup first
    print("🔧 Setting up workspace...")
    setup_result = setup_workspace.remote()
    print(f"Setup result: {setup_result}")
    
    # Test agent functionality
    print("\n🧪 Testing agent...")
    test_result = test_agent.remote()
    print(f"Test result: {test_result}")
    
    print("\n🌐 Starting VS Code Server...")
    print("Access your environment at the URL provided by Modal")
    
    # Start VS Code server
    vscode_server.remote()

if __name__ == "__main__":
    # For direct execution
    print("🖥️ Atölye Şefi - Modal VS Code Server")
    print("To run: modal run infrastructure.modal_vscode::main")
    print("To serve: modal serve infrastructure.modal_vscode::vscode_server")