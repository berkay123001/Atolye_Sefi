#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - MODAL TUNNEL VS CODE
Modal tunnel ile VS Code'a erişim (web endpoint'siz)
"""

import modal
import subprocess
import time
from pathlib import Path

# Initialize Modal app
app = modal.App("atolye-sefi-vscode")

# VS Code image
vscode_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install([
        "curl", "wget", "git", "build-essential", 
        "libnss3", "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0", "libgbm1",
        "vim", "nano", "htop", "tree"
    ])
    .pip_install([
        "modal", "langchain", "langchain-groq", "langchain-core",
        "pandas", "numpy", "requests", "pydantic", "pydantic-settings", "python-dotenv"
    ])
    .run_commands([
        "cd /tmp && curl -fsSL https://github.com/gitpod-io/openvscode-server/releases/download/openvscode-server-v1.85.2/openvscode-server-v1.85.2-linux-x64.tar.gz | tar -xz",
        "mv /tmp/openvscode-server-v1.85.2-linux-x64 /opt/openvscode-server",
        "chmod +x /opt/openvscode-server/bin/openvscode-server",
        "mkdir -p /workspace"
    ])
    .add_local_dir(".", "/workspace/atolye-sefi")
)

@app.function(
    image=vscode_image,
    cpu=2,
    memory=4096,
    timeout=3600
)
def run_vscode_with_tunnel():
    """Run VS Code with Modal tunnel access"""
    
    print("🚀 Starting VS Code with Modal Tunnel...")
    
    # Setup workspace
    workspace_path = Path("/workspace/atolye-sefi")
    
    import os
    os.chdir(str(workspace_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📂 Files available: {len(list(workspace_path.iterdir())) if workspace_path.exists() else 0}")
    
    # Start VS Code Server
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 Starting VS Code on port 8080...")
    
    # Start VS Code process
    process = subprocess.Popen(cmd)
    
    # Wait for VS Code to start
    time.sleep(10)
    
    if process.poll() is None:
        print("✅ VS Code Server started successfully!")
        print("🔗 VS Code is running on port 8080")
        print("📡 Use Modal tunnel to access it")
        
        # Create tunnel info
        tunnel_info = {
            "status": "running",
            "port": 8080,
            "message": "VS Code is ready! Use 'modal container exec' to access or set up tunnel."
        }
        
        print(f"📊 Tunnel info: {tunnel_info}")
        
        # Keep the container alive
        try:
            while process.poll() is None:
                time.sleep(30)
                print("💓 VS Code heartbeat - still running...")
                
        except KeyboardInterrupt:
            print("🛑 Shutting down VS Code...")
            process.terminate()
            process.wait()
            
        return tunnel_info
    
    else:
        print("❌ VS Code failed to start")
        return {"status": "failed", "message": "VS Code startup failed"}

@app.function(
    image=vscode_image,
    timeout=60
)
def test_agent():
    """Test agent in container"""
    
    print("🧪 Testing agent in container...")
    
    workspace_path = Path("/workspace/atolye-sefi")
    
    import os
    import sys
    
    os.chdir(str(workspace_path))
    sys.path.append(str(workspace_path))
    
    try:
        from agents.react_agent_v3 import ReactAgentV3
        
        agent = ReactAgentV3()
        
        # Test agent
        result = agent.run("merhaba")
        print(f"✅ Agent test result: {result['result'][:100]}...")
        
        # Test file creation
        file_result = agent.run("hesap makinesi kodu yaz ve test_calc.py dosyasına kaydet")
        print(f"📁 File creation result: {file_result['result'][:100]}...")
        
        # Check if file exists
        test_file = workspace_path / "test_calc.py"
        file_exists = test_file.exists()
        print(f"📄 File created: {file_exists}")
        
        return {
            "agent_test": "success",
            "file_creation": file_exists,
            "workspace_files": len(list(workspace_path.iterdir()))
        }
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return {"agent_test": "failed", "error": str(e)}

@app.local_entrypoint()
def main():
    """Main entry point"""
    print("🎯 Atölye Şefi VS Code Tunnel Setup")
    print("=" * 50)
    
    # Test agent first
    print("🧪 Testing agent...")
    test_result = test_agent.remote()
    print(f"Agent test: {test_result}")
    
    if test_result.get("agent_test") == "success":
        print("\n🚀 Starting VS Code server...")
        print("📡 This will start VS Code in Modal container")
        print("🔗 Use Modal dashboard to access the container")
        
        # Run VS Code
        vscode_result = run_vscode_with_tunnel.remote()
        print(f"VS Code result: {vscode_result}")
    else:
        print("❌ Agent test failed - skipping VS Code start")

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Modal Tunnel VS Code")
    print()
    print("Commands:")
    print("  modal run infrastructure.modal_vscode_tunnel::test_agent")
    print("  modal run infrastructure.modal_vscode_tunnel::run_vscode_with_tunnel") 
    print("  modal run infrastructure.modal_vscode_tunnel  # Test + VS Code")
    print()
    print("After running, use Modal dashboard to access the container!")