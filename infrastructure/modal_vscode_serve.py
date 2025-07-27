#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - MODAL SERVE VS CODE
Modal serve ile direkt VS Code erişimi
"""

import modal
import subprocess
import time
from pathlib import Path
import os

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
        "pandas", "numpy", "requests", "pydantic", "pydantic-settings", "python-dotenv",
        "httpx"
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
    min_containers=1
)
@modal.web_endpoint()
def start_vscode():
    """Start VS Code Server - Keep Alive"""
    
    print("🚀 Starting VS Code Server (Keep Alive)...")
    
    # Setup workspace
    workspace_path = Path("/workspace/atolye-sefi")
    os.chdir(str(workspace_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📂 Files: {len(list(workspace_path.iterdir()))}")
    
    # Start VS Code on port 8000 for Modal serve
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 Starting VS Code on port 8000...")
    
    # Start VS Code
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Wait for startup
    time.sleep(10)
    
    if process.poll() is None:
        print("✅ VS Code started successfully!")
        print("🔗 VS Code running on port 8000")
        print("📡 Modal serve will expose this as web URL")
        
        # Return simple proxy
        import httpx
        
        async def app_asgi(scope, receive, send):
            if scope["type"] == "http":
                path = scope["path"]
                query = scope.get("query_string", b"").decode()
                url = f"http://localhost:8000{path}"
                if query:
                    url += f"?{query}"
                
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(url)
                        
                        await send({
                            "type": "http.response.start",
                            "status": response.status_code,
                            "headers": [[b"content-type", response.headers.get("content-type", "text/html").encode()]]
                        })
                        
                        await send({
                            "type": "http.response.body",
                            "body": response.content
                        })
                        
                except Exception as e:
                    error_msg = f"VS Code proxy error: {e}"
                    await send({
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [[b"content-type", b"text/plain"]]
                    })
                    await send({
                        "type": "http.response.body",
                        "body": error_msg.encode()
                    })
        
        return app_asgi
    
    else:
        stdout, stderr = process.communicate()
        print(f"❌ VS Code failed: {stdout}")
        return f"Failed: {stdout}"

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Modal Serve VS Code")
    print("To serve: modal serve infrastructure.modal_vscode_serve::start_vscode")