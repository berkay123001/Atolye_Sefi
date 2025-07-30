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
        "pandas", "numpy", "requests", "pydantic", "python-dotenv",
        "fastapi[standard]", "uvicorn", "requests", "httpx"
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
    cpu=2,
    memory=4096
)
@modal.fastapi_endpoint()
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
        "--port", "8080",
        "--without-connection-token",
        "--accept-server-license-terms"
    ]
    
    print("🌐 Starting VS Code on port 8080...")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for startup - VS Code needs more time
    time.sleep(15)
    
    # Check if VS Code is actually responding
    import requests
    for i in range(10):
        try:
            response = requests.get('http://localhost:8080', timeout=2)
            if response.status_code == 200:
                print(f"✅ VS Code responding after {5 + 15 + i*2} seconds")
                break
        except:
            pass
        time.sleep(2)
    
    if process.poll() is None:
        print("✅ VS Code Server started successfully!")
        print("🔗 Server running on port 8080")
        
        # Create FastAPI app with health check and proxy
        from fastapi import FastAPI, Request
        from fastapi.responses import HTMLResponse, RedirectResponse
        import httpx
        
        app_fastapi = FastAPI()
        
        @app_fastapi.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8080", timeout=5.0)
                    return {"status": "healthy", "vscode_status": int(response.status_code)}
            except Exception as e:
                return {"status": "unhealthy", "error": str(e)}
        
        @app_fastapi.get("/")
        async def vscode_proxy():
            """Direct access to VS Code"""
            return RedirectResponse(url="http://localhost:8080", status_code=302)
        
        @app_fastapi.get("/direct")
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
        
        return app_fastapi
    else:
        stdout, stderr = process.communicate()
        print(f"❌ VS Code failed to start")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse
        
        error_app = FastAPI()
        
        @error_app.get("/")
        async def error_page():
            return HTMLResponse(content=f"""
            <h1>❌ VS Code Failed to Start</h1>
            <pre>stdout: {stdout}</pre>
            <pre>stderr: {stderr}</pre>
            """)
        
        return error_app

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