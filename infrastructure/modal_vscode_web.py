#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - MODAL VSCODE WEB ENDPOINT
VS Code Server with proper web endpoint configuration
"""

import modal
import subprocess
import time
from pathlib import Path

# Initialize Modal app
app = modal.App("atolye-sefi-vscode")

# Workspace volume
workspace_volume = modal.Volume.from_name("atolye-vscode-workspace", create_if_missing=True)

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
        "fastapi[standard]", "starlette", "httpx"
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
@modal.asgi_app()
def vscode():
    """VS Code Web Endpoint"""
    
    print("🚀 Starting VS Code Web Server...")
    
    # Use pre-loaded project files from image
    workspace_path = Path("/workspace/atolye-sefi")
    
    import os
    os.chdir(str(workspace_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📂 Files available: {list(workspace_path.iterdir()) if workspace_path.exists() else 'Directory not found'}")
    
    # Start VS Code Server
    cmd = [
        "/opt/openvscode-server/bin/openvscode-server",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 VS Code starting on port 8080...")
    
    # Start process in background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for startup
    time.sleep(10)
    
    if process.poll() is None:
        print("✅ VS Code started successfully!")
        
        # Create FastAPI app that proxies to VS Code
        from fastapi import FastAPI, Request, Response
        from fastapi.responses import StreamingResponse
        import httpx
        
        app_fastapi = FastAPI()
        
        @app_fastapi.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        async def proxy_to_vscode(request: Request, path: str = ""):
            """Proxy all requests to VS Code server"""
            url = f"http://localhost:8080/{path}"
            if request.url.query:
                url += f"?{request.url.query}"
            
            # Get request body
            body = await request.body()
            
            # Prepare headers (exclude some that httpx handles)
            headers = dict(request.headers)
            headers.pop('host', None)
            headers.pop('content-length', None)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.request(
                        method=request.method,
                        url=url,
                        content=body,
                        headers=headers
                    )
                    
                    # Return response
                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                    
                except Exception as e:
                    print(f"❌ Proxy error: {e}")
                    return Response(f"VS Code server error: {e}", status_code=500)
        
        return app_fastapi
    
    else:
        stdout, stderr = process.communicate()
        print(f"❌ VS Code failed to start")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        
        from fastapi import FastAPI
        from fastapi.responses import PlainTextResponse
        
        error_app = FastAPI()
        
        @error_app.get("/{path:path}")
        async def error_handler():
            return PlainTextResponse(f"❌ VS Code failed to start.\nstdout: {stdout}\nstderr: {stderr}")
        
        return error_app

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - VS Code Web Endpoint")
    print("To serve: modal serve infrastructure.modal_vscode_web::vscode")