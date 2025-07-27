#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - PURE HTTP VS CODE
FastAPI'sız, pure HTTP server ile VS Code proxy
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
    timeout=3600
)
@modal.web_endpoint()
def vscode():
    """Pure HTTP VS Code Server - No FastAPI!"""
    
    print("🚀 Starting Pure HTTP VS Code Server...")
    
    # Use pre-loaded project files
    workspace_path = Path("/workspace/atolye-sefi")
    
    import os
    os.chdir(str(workspace_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📂 Files: {list(workspace_path.iterdir()) if workspace_path.exists() else 'None'}")
    
    # Start VS Code Server
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 Starting VS Code on port 8080...")
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for startup
    time.sleep(8)
    
    if process.poll() is None:
        print("✅ VS Code started successfully!")
        
        # Pure ASGI app - NO FASTAPI
        async def app_asgi(scope, receive, send):
            """Pure ASGI application"""
            
            if scope["type"] == "http":
                # Get path
                path = scope["path"]
                method = scope["method"]
                
                print(f"🌐 {method} {path}")
                
                # Simple proxy to VS Code
                import httpx
                
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        url = f"http://localhost:8080{path}"
                        if scope.get("query_string"):
                            url += f"?{scope['query_string'].decode()}"
                        
                        response = await client.get(url)
                        
                        await send({
                            "type": "http.response.start",
                            "status": response.status_code,
                            "headers": [
                                [b"content-type", response.headers.get("content-type", "text/html").encode()],
                                [b"content-length", str(len(response.content)).encode()],
                            ]
                        })
                        
                        await send({
                            "type": "http.response.body",
                            "body": response.content
                        })
                        
                except Exception as e:
                    error_msg = f"VS Code proxy error: {e}"
                    print(f"❌ {error_msg}")
                    
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
        print(f"❌ VS Code failed to start")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        
        # Error ASGI app
        async def error_asgi(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [[b"content-type", b"text/plain"]]
            })
            
            await send({
                "type": "http.response.body",
                "body": f"❌ VS Code failed to start.\nstdout: {stdout}\nstderr: {stderr}".encode()
            })
        
        return error_asgi

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Pure HTTP VS Code")
    print("To serve: modal serve -m infrastructure.modal_vscode_pure")