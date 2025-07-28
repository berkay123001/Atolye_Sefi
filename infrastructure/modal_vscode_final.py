#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - FINAL MODAL VSCODE SOLUTION
Hybrid: Web endpoint + Persistent container + Volume persistence
"""

import modal
import subprocess
import time
from pathlib import Path
import asyncio

# Initialize Modal app
app = modal.App("atolye-sefi-vscode-final")

# Persistent volumes
workspace_volume = modal.Volume.from_name("atolye-vscode-workspace", create_if_missing=True)
vscode_data_volume = modal.Volume.from_name("atolye-vscode-data", create_if_missing=True)

# VS Code image with complete setup
vscode_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install([
        "curl", "wget", "git", "build-essential", 
        "libnss3", "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0", "libgbm1",
        "vim", "nano", "htop", "tree", "openssh-client", "unzip"
    ])
    .pip_install([
        "modal", "fastapi[standard]", "uvicorn", "httpx", "websockets",
        "langchain", "langchain-groq", "langchain-core",
        "pandas", "numpy", "requests", "pydantic", "python-dotenv"
    ])
    .run_commands([
        # Download VS Code Server
        "cd /tmp && curl -fsSL https://github.com/gitpod-io/openvscode-server/releases/download/openvscode-server-v1.85.2/openvscode-server-v1.85.2-linux-x64.tar.gz | tar -xz",
        "mv /tmp/openvscode-server-v1.85.2-linux-x64 /opt/openvscode-server",
        "chmod +x /opt/openvscode-server/bin/openvscode-server",
        
        # Create directories for persistent data
        "mkdir -p /workspace",
        "mkdir -p /opt/openvscode-server/out",
        "mkdir -p /opt/openvscode-server/node_modules/vscode-regexp-languagedetection/dist",
        
        # Create placeholder files for missing assets
        "echo '// Debug adapter placeholder' > /opt/openvscode-server/out/vsda.js",
        "echo '// WASM placeholder' > /opt/openvscode-server/out/vsda_bg.wasm",
        "echo '// Language detection placeholder' > /opt/openvscode-server/node_modules/vscode-regexp-languagedetection/dist/index.js",
        
        # Create VS Code startup script - line by line to avoid Dockerfile issues
        "echo '#!/bin/bash' > /usr/local/bin/start-vscode.sh",
        "echo 'cd /workspace' >> /usr/local/bin/start-vscode.sh",
        "echo 'export HOME=/vscode-settings' >> /usr/local/bin/start-vscode.sh",
        "echo '/opt/openvscode-server/bin/openvscode-server --host 0.0.0.0 --port 8080 --without-connection-token --accept-server-license-terms --disable-telemetry --disable-update-check --user-data-dir /vscode-settings/.openvscode-server /workspace' >> /usr/local/bin/start-vscode.sh",
        "chmod +x /usr/local/bin/start-vscode.sh"
    ])
)

# Global VS Code process state
vscode_process = None
vscode_ready = False

def ensure_vscode_running():
    """Ensure VS Code is running in background"""
    global vscode_process, vscode_ready
    
    # Check if already running
    if vscode_process and vscode_process.poll() is None:
        return True
    
    print("🚀 Starting VS Code server...")
    
    # Setup workspace with sample files
    workspace_path = Path("/workspace")
    sample_project = workspace_path / "sample-project"
    if not sample_project.exists():
        sample_project.mkdir(parents=True, exist_ok=True)
        (sample_project / "hello.py").write_text('print("Hello from Persistent VS Code!")\nprint("Files are saved across sessions!")')
        (sample_project / "README.md").write_text("# Atölye Şefi VS Code\n\n✅ Persistent workspace\n✅ Settings saved\n✅ Extensions preserved")
        (sample_project / "notes.txt").write_text("This file demonstrates persistence.\nEdit and save - it will be preserved!")
    
    # Start VS Code process
    vscode_process = subprocess.Popen(
        ["/usr/local/bin/start-vscode.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True
    )
    
    # Wait for startup
    time.sleep(8)
    
    # Check if responsive
    import requests
    for i in range(10):
        try:
            response = requests.get("http://localhost:8080", timeout=3)
            if response.status_code == 200:
                print(f"✅ VS Code ready after {8 + i*2} seconds")
                vscode_ready = True
                return True
        except:
            pass
        time.sleep(2)
    
    print("✅ VS Code started (may still be initializing)")
    vscode_ready = True
    return True

# FastAPI app for proxy
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
import httpx

fastapi_app = FastAPI()

@fastapi_app.on_event("startup")
async def startup_event():
    """Start VS Code on FastAPI startup"""
    ensure_vscode_running()

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    global vscode_ready, vscode_process
    
    status = "unknown"
    if vscode_process:
        if vscode_process.poll() is None:
            status = "running"
        else:
            status = "stopped"
    
    return {
        "vscode_ready": vscode_ready,
        "vscode_status": status,
        "pid": vscode_process.pid if vscode_process else None
    }

@fastapi_app.get("/restart")
async def restart_vscode():
    """Restart VS Code server"""
    global vscode_process, vscode_ready
    
    if vscode_process:
        vscode_process.terminate()
        vscode_process.wait()
    
    vscode_ready = False
    success = ensure_vscode_running()
    
    return {"restarted": success, "ready": vscode_ready}

# WebSocket proxy for VS Code
@fastapi_app.websocket("/ws")
async def websocket_proxy(websocket: WebSocket):
    """WebSocket proxy to VS Code"""
    await websocket.accept()
    
    try:
        import websockets
        uri = "ws://localhost:8080/ws"
        async with websockets.connect(uri) as vscode_ws:
            
            async def forward_to_vscode():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await vscode_ws.send(data)
                except:
                    pass
            
            async def forward_to_browser():
                try:
                    async for message in vscode_ws:
                        await websocket.send_text(message)
                except:
                    pass
            
            await asyncio.gather(
                forward_to_vscode(),
                forward_to_browser(),
                return_exceptions=True
            )
    except Exception as e:
        print(f"WebSocket proxy error: {e}")
        await websocket.close()

# Catch-all WebSocket proxy
@fastapi_app.websocket("/{path:path}")
async def websocket_catch_all(websocket: WebSocket, path: str):
    """Catch-all WebSocket proxy"""
    if path in ["health", "restart"]:
        await websocket.close()
        return
        
    await websocket.accept()
    
    try:
        import websockets
        uri = f"ws://localhost:8080/{path}"
        async with websockets.connect(uri) as vscode_ws:
            
            async def forward_to_vscode():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await vscode_ws.send(data)
                except:
                    pass
            
            async def forward_to_browser():
                try:
                    async for message in vscode_ws:
                        await websocket.send_text(message)
                except:
                    pass
            
            await asyncio.gather(
                forward_to_vscode(),
                forward_to_browser(),
                return_exceptions=True
            )
    except Exception as e:
        print(f"WebSocket catch-all error: {e}")
        await websocket.close()

# HTTP proxy for all other requests
@fastapi_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def vscode_proxy(request: Request, path: str = ""):
    """Proxy all requests to VS Code"""
    if path.startswith(("health", "restart")):
        return Response("Not found", status_code=404)
    
    # Ensure VS Code is running
    if not vscode_ready:
        ensure_vscode_running()
    
    url = f"http://localhost:8080/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    body = await request.body()
    headers = dict(request.headers)
    headers.pop('host', None)
    headers.pop('content-length', None)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except Exception as e:
        return HTMLResponse(content=f"""
        <h1>🖥️ Atölye Şefi VS Code</h1>
        <h2>❌ Connection Error</h2>
        <p>Error: {e}</p>
        <p><a href="/health">Check Health</a></p>
        <p><a href="/restart">Restart VS Code</a></p>
        """)

# Modal web endpoint - PERSISTENT container
@app.function(
    image=vscode_image,
    volumes={
        "/workspace": workspace_volume,
        "/vscode-settings": vscode_data_volume
    },
    timeout=0,  # Run indefinitely
    cpu=2,
    memory=4096,
    min_containers=1,  # Keep warm
    max_containers=1   # Single container only
)
@modal.asgi_app()
def vscode_web():
    """VS Code web endpoint with persistence"""
    return fastapi_app

@app.function(
    image=vscode_image,
    volumes={
        "/workspace": workspace_volume,
        "/vscode-settings": vscode_data_volume
    }
)
def check_persistence():
    """Check file persistence"""
    workspace_path = Path("/workspace")
    vscode_data_path = Path("/vscode-settings")
    
    workspace_files = []
    if workspace_path.exists():
        for item in workspace_path.rglob("*"):
            if item.is_file():
                workspace_files.append(str(item.relative_to(workspace_path)))
    
    vscode_files = []
    if vscode_data_path.exists():
        for item in vscode_data_path.rglob("*"):
            if item.is_file():
                vscode_files.append(str(item.relative_to(vscode_data_path)))
    
    return {
        "workspace_files": workspace_files[:10],
        "vscode_data_files": vscode_files[:10],
        "workspace_exists": workspace_path.exists(),
        "vscode_data_exists": vscode_data_path.exists()
    }

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Final Modal VS Code Solution")
    print()
    print("Features:")
    print("✅ Web endpoint - Direct browser access")
    print("✅ Persistent workspace - Files saved")
    print("✅ Persistent VS Code data - Settings/extensions saved") 
    print("✅ Single container - No multiple instances")
    print("✅ WebSocket proxy - Full VS Code functionality")
    print()
    print("Commands:")
    print("  modal serve -m infrastructure.modal_vscode_final")
    print("  modal run infrastructure.modal_vscode_final::check_persistence")
    print()
    print("Access via web URL provided by Modal!")