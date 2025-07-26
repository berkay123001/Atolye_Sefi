#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - SIMPLIFIED MODAL VSCODE INTEGRATION
Cloud-based VS Code environment - Simplified version for testing
"""

import modal
import subprocess
import time
from pathlib import Path

# Initialize Modal app
app = modal.App("atolye-sefi-vscode")

# Workspace volume
workspace_volume = modal.Volume.from_name("atolye-vscode-workspace", create_if_missing=True)

# Simple VS Code image
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
)

@app.function(
    image=vscode_image,
    volumes={"/workspace": workspace_volume},
    timeout=3600,
    max_containers=1
)
def start_vscode():
    """Start VS Code Server"""
    
    print("🚀 Starting VS Code Server...")
    
    # Create workspace structure
    workspace_path = Path("/workspace/atolye-sefi")
    workspace_path.mkdir(exist_ok=True)
    
    # Copy current project files if needed
    import os
    os.chdir(str(workspace_path))
    
    # Start VS Code Server
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 Starting VS Code on port 8000...")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for startup
    time.sleep(5)
    
    if process.poll() is None:
        print("✅ VS Code Server started successfully!")
        print("🔗 Server running on port 8000")
        
        # Keep running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("🛑 Shutting down...")
            process.terminate()
    else:
        stdout, stderr = process.communicate()
        print(f"❌ VS Code failed to start")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
    
    return "VS Code Server finished"

@app.function(
    image=vscode_image,
    volumes={"/workspace": workspace_volume}
)
def test_workspace():
    """Test workspace setup"""
    
    print("🧪 Testing workspace...")
    
    workspace_path = Path("/workspace/atolye-sefi")
    workspace_path.mkdir(exist_ok=True)
    
    # Test file creation
    test_file = workspace_path / "test.py"
    test_file.write_text("print('Hello from Modal VS Code!')")
    
    # Test Python execution
    import subprocess
    result = subprocess.run(["python", str(test_file)], capture_output=True, text=True)
    
    print(f"✅ Workspace test: {result.stdout.strip()}")
    print(f"📁 Workspace path: {workspace_path}")
    print(f"📄 Test file exists: {test_file.exists()}")
    
    return {
        "workspace_path": str(workspace_path),
        "test_file_exists": test_file.exists(),
        "python_output": result.stdout.strip()
    }

@app.local_entrypoint()
def main():
    """Main entry point"""
    print("🧪 Testing VS Code setup...")
    
    # Test workspace first
    test_result = test_workspace.remote()
    print(f"Test result: {test_result}")
    
    # Start VS Code
    print("🚀 Starting VS Code Server...")
    vscode_result = start_vscode.remote()
    print(f"VS Code result: {vscode_result}")

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Simple Modal VS Code Server")
    print("To test: modal run infrastructure.modal_vscode_simple")
    print("To serve: modal serve infrastructure.modal_vscode_simple::start_vscode")