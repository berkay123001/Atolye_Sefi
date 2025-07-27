#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - SIMPLE VS CODE PROXY
Minimal proxy without complex FastAPI routing
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
        "pandas", "numpy", "requests", "pydantic", "python-dotenv",
        "fastapi[standard]", "uvicorn"
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
    """Simple VS Code Server"""
    
    print("🚀 Starting Simple VS Code Server...")
    
    # Use pre-loaded project files
    workspace_path = Path("/workspace/atolye-sefi")
    
    import os
    os.chdir(str(workspace_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Start VS Code Server
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 VS Code starting on port 8080...")
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for startup
    time.sleep(5)
    
    if process.poll() is None:
        print("✅ VS Code started successfully!")
        
        # Simple FastAPI proxy
        from fastapi import FastAPI
        import httpx
        from starlette.responses import StreamingResponse
        
        app_fastapi = FastAPI()
        
        @app_fastapi.get("/")
        async def root():
            """Root endpoint - redirect to VS Code"""
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://localhost:8080/")
                    return StreamingResponse(
                        iter([response.content]),
                        media_type="text/html",
                        status_code=response.status_code
                    )
                except Exception as e:
                    return {"error": f"VS Code connection failed: {e}"}
        
        @app_fastapi.get("/{path:path}")
        async def proxy_get(path: str):
            """Proxy GET requests"""
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.get(f"http://localhost:8080/{path}")
                    return StreamingResponse(
                        iter([response.content]),
                        media_type=response.headers.get("content-type", "text/html"),
                        status_code=response.status_code
                    )
                except Exception as e:
                    return {"error": f"Proxy error: {e}"}
        
        return app_fastapi
    
    else:
        stdout, stderr = process.communicate()
        print(f"❌ VS Code failed to start")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        
        from fastapi import FastAPI
        
        error_app = FastAPI()
        
        @error_app.get("/")
        async def error():
            return {"error": "VS Code failed to start", "stdout": stdout, "stderr": stderr}
        
        return error_app

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Simple VS Code Proxy")
    print("To serve: modal serve -m infrastructure.modal_vscode_simple_proxy")