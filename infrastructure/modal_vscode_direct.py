#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - DIRECT VS CODE
VS Code'u direkt expose et - proxy yok!
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
        "pandas", "numpy", "requests", "pydantic", "python-dotenv"
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
    timeout=3600,
    container_idle_timeout=300
)
def start_vscode_server():
    """Start VS Code server and keep it running"""
    
    print("🚀 Starting Direct VS Code Server...")
    
    # Use pre-loaded project files
    workspace_path = Path("/workspace/atolye-sefi")
    
    import os
    os.chdir(str(workspace_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📂 Files: {list(workspace_path.iterdir())[:10] if workspace_path.exists() else 'None'}")
    
    # Start VS Code Server on external port
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8000",  # Use port 8000
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 Starting VS Code on port 8000 (direct access)...")
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for startup
    time.sleep(10)
    
    if process.poll() is None:
        print("✅ VS Code started successfully!")
        print("🔗 VS Code should be accessible via Modal's port forwarding")
        
        # Keep process running and log output
        try:
            for line in process.stdout:
                if line.strip():
                    print(f"[VS Code] {line.strip()}")
                    
                # Check if process is still alive
                if process.poll() is not None:
                    break
                    
        except KeyboardInterrupt:
            print("🛑 Shutting down VS Code...")
            process.terminate()
            process.wait()
            
        return "VS Code server finished"
    
    else:
        stdout, stderr = process.communicate()
        print(f"❌ VS Code failed to start")
        print(f"Output: {stdout}")
        return f"VS Code failed: {stdout}"

# Test function
@app.function(
    image=vscode_image,
    timeout=60
)
def test_workspace():
    """Test workspace setup"""
    
    print("🧪 Testing workspace...")
    
    workspace_path = Path("/workspace/atolye-sefi")
    
    if workspace_path.exists():
        files = list(workspace_path.iterdir())
        print(f"✅ Workspace exists with {len(files)} items")
        print(f"📂 Sample files: {[f.name for f in files[:5]]}")
        
        # Test agent import
        import sys
        sys.path.append(str(workspace_path))
        
        try:
            from agents.react_agent_v3 import ReactAgentV3
            print("✅ ReactAgent V3 import successful")
            return {"status": "success", "files": len(files)}
        except Exception as e:
            print(f"❌ Agent import failed: {e}")
            return {"status": "error", "error": str(e)}
    else:
        print("❌ Workspace not found")
        return {"status": "error", "error": "Workspace not found"}

@app.local_entrypoint()
def main():
    """Main entry point"""
    print("🚀 Starting Atölye Şefi VS Code Environment")
    
    # Test first
    test_result = test_workspace.remote()
    print(f"Test result: {test_result}")
    
    # Start VS Code
    print("🌐 Starting VS Code server...")
    result = start_vscode_server.remote()
    print(f"VS Code result: {result}")

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Direct VS Code")
    print("To test: modal run infrastructure.modal_vscode_direct::test_workspace")
    print("To serve: modal run infrastructure.modal_vscode_direct::start_vscode_server")
    print("To run all: modal run infrastructure.modal_vscode_direct")