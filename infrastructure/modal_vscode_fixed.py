#!/usr/bin/env python3
"""
🖥️ ATÖLYE ŞEFİ - FIXED MODAL VSCODE
Fixed version with proper FastAPI app pattern
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
        "fastapi[standard]", "uvicorn", "httpx", "websockets"
    ])
    .run_commands([
        # Download and extract VS Code Server
        "cd /tmp && curl -fsSL https://github.com/gitpod-io/openvscode-server/releases/download/openvscode-server-v1.85.2/openvscode-server-v1.85.2-linux-x64.tar.gz | tar -xz",
        "mv /tmp/openvscode-server-v1.85.2-linux-x64 /opt/openvscode-server",
        "chmod +x /opt/openvscode-server/bin/openvscode-server",
        
        # Create workspace
        "mkdir -p /workspace",
        
        # Create missing static files directories and placeholder files
        "mkdir -p /opt/openvscode-server/out",
        "mkdir -p /opt/openvscode-server/node_modules/vscode-regexp-languagedetection/dist",
        
        # Create placeholder files to prevent 404s
        "echo '// VS Code Debug Adapter placeholder' > /opt/openvscode-server/out/vsda.js",
        "echo '// WASM placeholder' > /opt/openvscode-server/out/vsda_bg.wasm",
        "echo '// Language detection placeholder' > /opt/openvscode-server/node_modules/vscode-regexp-languagedetection/dist/index.js",
        
        # Create startup script - simple approach
        "echo '#!/bin/bash' > /usr/local/bin/start-vscode.sh",
        "echo 'cd /workspace' >> /usr/local/bin/start-vscode.sh", 
        "echo '/opt/openvscode-server/bin/openvscode-server --host 0.0.0.0 --port 8080 --without-connection-token --accept-server-license-terms --disable-telemetry &' >> /usr/local/bin/start-vscode.sh",
        "echo 'echo $! > /tmp/vscode.pid' >> /usr/local/bin/start-vscode.sh",
        "echo 'wait' >> /usr/local/bin/start-vscode.sh",
        "chmod +x /usr/local/bin/start-vscode.sh",
        
        # Create sample workspace files
        "mkdir -p /workspace/sample-project",
        "echo 'print(\"Hello from Atölye Şefi VS Code!\")' > /workspace/sample-project/hello.py",
        "echo '# Atölye Şefi VS Code\\n\\nWelcome to your cloud VS Code environment!' > /workspace/sample-project/README.md",
        "echo '{\"name\": \"sample-project\", \"version\": \"1.0.0\"}' > /workspace/sample-project/package.json",
        
        # Create container entrypoint
        "echo '#!/bin/bash' > /usr/local/bin/container-entrypoint.sh",
        "echo 'echo \"Container starting...\"' >> /usr/local/bin/container-entrypoint.sh",
        "echo '/usr/local/bin/start-vscode.sh &' >> /usr/local/bin/container-entrypoint.sh", 
        "echo 'echo \"VS Code started in background\"' >> /usr/local/bin/container-entrypoint.sh",
        "echo 'exec \"$@\"' >> /usr/local/bin/container-entrypoint.sh",
        "chmod +x /usr/local/bin/container-entrypoint.sh"
    ])
    .entrypoint(["/usr/local/bin/container-entrypoint.sh"])
)

# Global VS Code process reference
vscode_process = None
vscode_started = False

# VS Code startup moved to module initialization

# Create FastAPI app
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
import httpx
import websockets
import asyncio

fastapi_app = FastAPI()

# VS Code started automatically by container entrypoint

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080", timeout=3.0)
            return JSONResponse({"status": "healthy", "vscode_status": response.status_code})
    except Exception as e:
        return JSONResponse({"status": "unhealthy", "error": str(e)})

@fastapi_app.get("/")
async def vscode_proxy():
    """Proxy to VS Code - no redirect"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080", timeout=10.0)
            return HTMLResponse(content=response.text)
    except Exception as e:
        return HTMLResponse(content=f"""
        <h1>🖥️ Atölye Şefi VS Code</h1>
        <h2>❌ VS Code Connection Error</h2>
        <p>Error: {e}</p>
        <p><a href="/health">Check Health</a></p>
        <p><a href="/status">Check Status</a></p>
        <p>VS Code server may still be starting up...</p>
        """)

@fastapi_app.get("/direct")
async def vscode_direct():
    """Direct VS Code content"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080", timeout=10.0)
            return HTMLResponse(content=response.text)
    except Exception as e:
        return HTMLResponse(content=f"""
        <h1>VS Code Loading Error</h1>
        <p>Error: {e}</p>
        <p><a href="/health">Check Health</a></p>
        <p><a href="/">Try Redirect</a></p>
        """)

@fastapi_app.get("/status")
async def status():
    """VS Code status"""
    import os
    
    if os.path.exists("/tmp/vscode.pid"):
        try:
            with open("/tmp/vscode.pid", "r") as f:
                pid = int(f.read().strip())
            # Check if process exists
            os.kill(pid, 0)
            return {"vscode": "running", "pid": pid, "method": "pid_check"}
        except (OSError, ValueError):
            return {"vscode": "stopped", "error": "stale_pid", "method": "pid_check"}
    else:
        return {"vscode": "unknown", "error": "no_pid_file", "method": "pid_check"}

# WebSocket proxy for VS Code
@fastapi_app.websocket("/ws")
async def websocket_proxy(websocket: WebSocket):
    """WebSocket proxy to VS Code server"""
    await websocket.accept()
    
    try:
        # Connect to VS Code WebSocket
        uri = "ws://localhost:8080/ws"
        async with websockets.connect(uri) as vscode_ws:
            
            async def forward_to_vscode():
                """Forward messages from browser to VS Code"""
                try:
                    while True:
                        data = await websocket.receive_text()
                        await vscode_ws.send(data)
                except Exception as e:
                    print(f"Error forwarding to VS Code: {e}")
            
            async def forward_to_browser():
                """Forward messages from VS Code to browser"""
                try:
                    async for message in vscode_ws:
                        await websocket.send_text(message)
                except Exception as e:
                    print(f"Error forwarding to browser: {e}")
            
            # Run both directions concurrently
            await asyncio.gather(
                forward_to_vscode(),
                forward_to_browser(),
                return_exceptions=True
            )
            
    except Exception as e:
        print(f"WebSocket proxy error: {e}")
        await websocket.close()

# Catch-all WebSocket proxy for any WebSocket path
@fastapi_app.websocket("/{path:path}")
async def websocket_catch_all(websocket: WebSocket, path: str):
    """Catch-all WebSocket proxy"""
    if path in ["health", "status", "direct"]:
        await websocket.close()
        return
        
    await websocket.accept()
    
    try:
        # Try to connect to VS Code WebSocket at the same path
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
        print(f"WebSocket catch-all error for /{path}: {e}")
        await websocket.close()

# Catch-all proxy for VS Code static files and API
@fastapi_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def vscode_full_proxy(request: Request, path: str = ""):
    """Full proxy to VS Code for all routes"""
    if path.startswith(("health", "status", "direct")):
        # Skip our own endpoints
        return Response("Not found", status_code=404)
    
    url = f"http://localhost:8080/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    # Get request body
    body = await request.body()
    
    # Prepare headers
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
            
            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except Exception as e:
        return HTMLResponse(content=f"""
        <h1>🖥️ Atölye Şefi VS Code</h1>
        <h2>❌ Proxy Error</h2>
        <p>Path: /{path}</p>
        <p>Error: {e}</p>
        <p><a href="/health">Check Health</a></p>
        """)

# Mount FastAPI app with Modal
@app.function(
    image=vscode_image,
    volumes={"/workspace": workspace_volume},
    timeout=0,  # No timeout - keep alive
    cpu=2,
    memory=4096,
    min_containers=1,  # Keep container warm
    max_containers=1   # Force single container - no scaling
)
@modal.asgi_app()
def vscode_app():
    """VS Code ASGI app"""
    return fastapi_app

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

if __name__ == "__main__":
    print("🖥️ Atölye Şefi - Fixed Modal VS Code Server")
    print("To serve: modal serve -m infrastructure.modal_vscode_fixed")
    print("Endpoints:")
    print("  / - VS Code redirect")
    print("  /health - Health check") 
    print("  /direct - Direct content")
    print("  /status - VS Code status")