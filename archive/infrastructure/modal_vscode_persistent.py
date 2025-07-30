#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - PERSISTENT MODAL VSCODE
Single persistent container with proper file persistence
"""

import modal
import subprocess
import time
from pathlib import Path

# Initialize Modal app
app = modal.App("atolye-sefi-vscode-persistent")

# Persistent workspace volume
workspace_volume = modal.Volume.from_name("atolye-vscode-workspace", create_if_missing=True)

# VS Code image with better setup
vscode_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install([
        "curl", "wget", "git", "build-essential", 
        "libnss3", "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0", "libgbm1",
        "vim", "nano", "htop", "tree", "openssh-client"
    ])
    .pip_install([
        "modal", "langchain", "langchain-groq", "langchain-core",
        "pandas", "numpy", "requests", "pydantic", "python-dotenv"
    ])
    .run_commands([
        # Download and extract VS Code Server
        "cd /tmp && curl -fsSL https://github.com/gitpod-io/openvscode-server/releases/download/openvscode-server-v1.85.2/openvscode-server-v1.85.2-linux-x64.tar.gz | tar -xz",
        "mv /tmp/openvscode-server-v1.85.2-linux-x64 /opt/openvscode-server",
        "chmod +x /opt/openvscode-server/bin/openvscode-server",
        
        # Create directories
        "mkdir -p /workspace",
        "mkdir -p /opt/openvscode-server/out",
        "mkdir -p /opt/openvscode-server/node_modules/vscode-regexp-languagedetection/dist",
        
        # Create placeholder files
        "echo '// Debug adapter' > /opt/openvscode-server/out/vsda.js",
        "echo '// WASM placeholder' > /opt/openvscode-server/out/vsda_bg.wasm", 
        "echo '// Language detection' > /opt/openvscode-server/node_modules/vscode-regexp-languagedetection/dist/index.js",
    ])
)

@app.function(
    image=vscode_image,
    volumes={"/workspace": workspace_volume},
    timeout=0,  # Run indefinitely
    cpu=2,
    memory=4096,
    allow_concurrent_inputs=100  # Allow multiple connections to same container
)
def run_persistent_vscode():
    """Run VS Code in persistent mode"""
    
    print("🚀 Starting persistent VS Code server...")
    
    # Setup workspace
    workspace_path = Path("/workspace")
    
    # Create sample project if not exists
    sample_project = workspace_path / "sample-project"
    if not sample_project.exists():
        sample_project.mkdir(exist_ok=True)
        (sample_project / "hello.py").write_text('print("Hello from Atölye Şefi VS Code!")')
        (sample_project / "README.md").write_text("# Atölye Şefi VS Code\n\nWelcome to your persistent cloud VS Code!")
        (sample_project / "test.txt").write_text("This file tests persistence across sessions.")
    
    import os
    os.chdir(str(workspace_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📂 Files in workspace: {list(workspace_path.iterdir())}")
    
    # Start VS Code Server
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--without-connection-token",
        "--accept-server-license-terms",
        "--disable-telemetry",
        "--disable-update-check"
    ]
    
    print("🌐 Starting VS Code on port 8080...")
    
    # Start VS Code process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Wait for startup
    time.sleep(10)
    
    if process.poll() is None:
        print("✅ VS Code Server started successfully!")
        print("🔗 Server is running persistently")
        print("📁 Workspace files are persistent via Modal volume")
        
        # Keep process alive and monitor
        try:
            while process.poll() is None:
                time.sleep(30)
                print("💓 VS Code heartbeat - server is healthy")
                
                # Check workspace files periodically
                files = list(workspace_path.iterdir())
                print(f"📊 Workspace files: {len(files)} items")
                
        except KeyboardInterrupt:
            print("🛑 Shutting down VS Code...")
            process.terminate()
            process.wait()
            
        return {"status": "completed", "message": "VS Code server stopped"}
    
    else:
        stdout, stderr = process.communicate()
        print(f"❌ VS Code failed to start: {stdout}")
        return {"status": "failed", "error": stdout}

@app.function(
    image=vscode_image,
    volumes={"/workspace": workspace_volume}
)
def check_workspace():
    """Check workspace contents"""
    workspace_path = Path("/workspace")
    
    files = []
    if workspace_path.exists():
        for item in workspace_path.rglob("*"):
            if item.is_file():
                files.append({
                    "path": str(item.relative_to(workspace_path)),
                    "size": item.stat().st_size,
                    "modified": item.stat().st_mtime
                })
    
    return {
        "workspace_exists": workspace_path.exists(),
        "total_files": len(files),
        "files": files[:10]  # Show first 10 files
    }

@app.local_entrypoint()
def main():
    """Main entry point - start persistent VS Code"""
    print("🎯 Atölye Şefi - Persistent VS Code Server")
    print("=" * 50)
    
    # Check workspace first
    workspace_info = check_workspace.remote()
    print(f"📊 Workspace info: {workspace_info}")
    
    print("\n🚀 Starting persistent VS Code server...")
    print("📡 This will run indefinitely until manually stopped")
    print("🔗 Use Modal dashboard or tunnel to access")
    
    # Start VS Code in persistent mode
    result = run_persistent_vscode.remote()
    print(f"🏁 VS Code result: {result}")

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Persistent Modal VS Code")
    print()
    print("Commands:")
    print("  modal run infrastructure.modal_vscode_persistent  # Start persistent VS Code")
    print("  modal run infrastructure.modal_vscode_persistent::check_workspace  # Check files")
    print()
    print("After starting, use Modal dashboard to tunnel to port 8080!")
    print("Or use: modal container exec <container-id> -- curl localhost:8080")