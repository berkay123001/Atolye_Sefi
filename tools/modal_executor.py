"""
Modal.com Serverless Code Executor - LOCAL DEVELOPMENT VERSION
Replaces SSH system with cloud functions
"""

import modal
import os
from typing import Dict, Any, Optional, List
import logging

# Set Modal token from environment if available
try:
    from config import settings
    if hasattr(settings, 'MODAL_TOKEN_ID'):
        os.environ['MODAL_TOKEN_ID'] = settings.MODAL_TOKEN_ID
        print(f"🔐 Modal token set from environment: {settings.MODAL_TOKEN_ID[:10]}...")
except ImportError:
    pass

# Initialize Modal app - use "main" for serve mode compatibility  
app = modal.App("main")

# Base image with common ML/AI packages
base_image = modal.Image.debian_slim().pip_install([
    "torch", "transformers", "pandas", "numpy", 
    "matplotlib", "scikit-learn", "requests", "pillow",
    "opencv-python", "seaborn", "plotly", "jupyter"
])

# Workspace volume for persistent file storage
workspace_volume = modal.Volume.from_name("atolye-workspace", create_if_missing=True)

# LOCAL DEVELOPMENT: Direct execution without serve mode
def execute_code_locally(code: str, use_gpu: bool = False) -> Dict[str, Any]:
    """Local development version - executes code directly"""
    try:
        import subprocess
        import sys
        
        # Create temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute locally
        result = subprocess.run([sys.executable, temp_file], 
                              capture_output=True, text=True, timeout=30)
        
        # Cleanup
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return {
                "status": "success",
                "output": result.stdout,
                "error": result.stderr
            }
        else:
            return {
                "status": "error", 
                "output": result.stdout,
                "error": result.stderr
            }
            
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e)
        }

def execute_bash_locally(command: str) -> Dict[str, Any]:
    """Local development version - executes bash directly"""
    try:
        import subprocess
        
        result = subprocess.run(command, shell=True, 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {
                "status": "success",
                "output": result.stdout,
                "error": result.stderr
            }
        else:
            return {
                "status": "error",
                "output": result.stdout, 
                "error": result.stderr
            }
            
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e)
        }

@app.function(
    gpu="T4",
    timeout=3600,
    image=base_image,
    memory=8192
)
def execute_gpu_code(code: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
    """Execute Python code in Modal cloud with GPU access."""
    import sys
    from io import StringIO
    import subprocess
    
    # Install additional requirements if provided
    if requirements:
        try:
            for req in requirements:
                subprocess.run([sys.executable, "-m", "pip", "install", req], 
                             check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "output": "",
                "error": f"Failed to install requirements: {e.stderr}"
            }
    
    # Capture output
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    
    try:
        # Execute the code
        exec(code, {"__name__": "__main__"})
        
        output = stdout_capture.getvalue()
        error_output = stderr_capture.getvalue()
        
        return {
            "status": "success",
            "output": output,
            "error": error_output if error_output else None,
            "gpu_info": "GPU T4 available"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "output": stdout_capture.getvalue(),
            "error": f"{type(e).__name__}: {str(e)}\n{stderr_capture.getvalue()}"
        }
        
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

# Workspace file management functions
@app.function(
    timeout=120,
    image=base_image,
    volumes={"/workspace": workspace_volume}
)
def save_generated_code(filename: str, content: str) -> Dict[str, Any]:
    """Save generated code to workspace volume"""
    try:
        with open(f"/workspace/{filename}", "w", encoding="utf-8") as f:
            f.write(content)
        
        # Commit changes to volume
        workspace_volume.commit()
        
        return {
            "status": "success",
            "message": f"✅ {filename} saved to workspace",
            "filename": filename
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"❌ Failed to save {filename}: {str(e)}"
        }

@app.function(
    timeout=60,
    image=base_image,
    volumes={"/workspace": workspace_volume}
)
def list_workspace_files() -> Dict[str, Any]:
    """List all files in workspace"""
    try:
        import os
        files = []
        
        if os.path.exists("/workspace"):
            for item in os.listdir("/workspace"):
                item_path = os.path.join("/workspace", item)
                if os.path.isfile(item_path):
                    with open(item_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    files.append({
                        "name": item,
                        "content": content,
                        "size": len(content)
                    })
        
        return {
            "status": "success",
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list files: {str(e)}",
            "files": []
        }

@app.function(
    timeout=60,
    image=base_image,
    volumes={"/workspace": workspace_volume}
)
def get_workspace_file(filename: str) -> Dict[str, Any]:
    """Get specific file content from workspace"""
    try:
        file_path = f"/workspace/{filename}"
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"File {filename} not found"
            }
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "status": "success",
            "filename": filename,
            "content": content
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to read {filename}: {str(e)}"
        }

@app.function(
    timeout=600,
    image=base_image,
    memory=2048
)
def execute_simple_code(code: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
    """Execute simple Python code without GPU."""
    import sys
    from io import StringIO
    import subprocess
    
    # Install additional requirements if provided
    if requirements:
        try:
            for req in requirements:
                subprocess.run([sys.executable, "-m", "pip", "install", req], 
                             check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "output": "",
                "error": f"Failed to install requirements: {e.stderr}"
            }
    
    # Capture output
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    
    try:
        # Execute the code
        exec(code, {"__name__": "__main__"})
        
        output = stdout_capture.getvalue()
        error_output = stderr_capture.getvalue()
        
        return {
            "status": "success",
            "output": output,
            "error": error_output if error_output else None,
            "gpu_info": "CPU only"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "output": stdout_capture.getvalue(),
            "error": f"{type(e).__name__}: {str(e)}\n{stderr_capture.getvalue()}"
        }
        
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

@app.function(
    timeout=300,
    image=modal.Image.debian_slim().pip_install(["requests"])
)
def execute_bash_command(command: str) -> Dict[str, Any]:
    """Execute bash commands in Modal."""
    import subprocess
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr if result.stderr else None,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "output": "",
            "error": "Command timed out after 300 seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e)
        }

class ModalExecutor:
    """Local interface for Modal serverless functions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._modal_healthy = None  # Cache health status
        self._last_health_check = 0
        
    def check_modal_health(self, force_check: bool = False) -> bool:
        """Check if Modal.com is available and healthy"""
        import time
        
        # Use cached result if recent (30 seconds)
        current_time = time.time()
        if not force_check and self._modal_healthy is not None:
            if current_time - self._last_health_check < 30:
                return self._modal_healthy
        
        try:
            self.logger.info("🔍 Checking Modal.com health...")
            # Quick health check with timeout
            result = modal_health_check.remote()
            self._modal_healthy = result.get("status") == "success"
            self._last_health_check = current_time
            
            if self._modal_healthy:
                self.logger.info("✅ Modal.com is healthy")
            else:
                self.logger.warning("⚠️ Modal.com health check failed")
                
            return self._modal_healthy
            
        except Exception as e:
            self.logger.warning(f"❌ Modal.com not available: {e}")
            self._modal_healthy = False
            self._last_health_check = current_time
            return False
        
    def execute_python_code(self, code: str, use_gpu: bool = False, 
                          requirements: list = []) -> Dict[str, Any]:
        """HYBRID: Execute Python code with Modal.com primary + local fallback"""
        
        # 1. Smart Detection: Check Modal.com health
        modal_available = self.check_modal_health()
        
        if modal_available:
            # 2. Primary Execution: Try Modal.com serverless
            try:
                if use_gpu:
                    self.logger.info("🚀 PRIMARY: Executing code with GPU on Modal.com...")
                    result = execute_gpu_code.remote(code, requirements)
                else:
                    self.logger.info("🚀 PRIMARY: Executing code on Modal.com...")
                    result = execute_simple_code.remote(code, requirements)
                    
                self.logger.info(f"✅ Modal.com execution completed: {result['status']}")
                result["execution_method"] = "Modal.com Cloud"
                return result
                
            except Exception as e:
                self.logger.warning(f"⚠️ Modal.com failed, falling back to local: {e}")
                # Mark Modal as unhealthy for future requests
                self._modal_healthy = False
        
        # 3. Fallback Execution: Local subprocess with graceful degradation
        self.logger.info("🔄 FALLBACK: Executing code locally...")
        return self._execute_local_fallback(code, use_gpu, requirements)
    
    def _execute_local_fallback(self, code: str, use_gpu: bool, requirements: list) -> Dict[str, Any]:
        """Local fallback execution with subprocess"""
        try:
            import subprocess
            import sys
            import tempfile
            import os
            
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute locally
                result = subprocess.run([sys.executable, temp_file], 
                                      capture_output=True, text=True, timeout=30)
                
                # Cleanup
                os.unlink(temp_file)
                
                if result.returncode == 0:
                    return {
                        "status": "success",
                        "output": result.stdout,
                        "error": result.stderr if result.stderr else None,
                        "execution_method": f"Local {'GPU-sim' if use_gpu else 'CPU'}",
                        "gpu_info": "GPU simulation" if use_gpu else "CPU only"
                    }
                else:
                    return {
                        "status": "error",
                        "output": result.stdout,
                        "error": result.stderr,
                        "execution_method": "Local CPU"
                    }
                    
            except subprocess.TimeoutExpired:
                os.unlink(temp_file)
                return {
                    "status": "error",
                    "output": "",
                    "error": "Local execution timed out after 30 seconds",
                    "execution_method": "Local CPU"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"Local fallback failed: {str(e)}",
                "execution_method": "Local CPU"
            }
    
    def execute_bash_command(self, command: str) -> Dict[str, Any]:
        """HYBRID: Execute bash command with Modal.com primary + local fallback"""
        
        # 1. Smart Detection: Check Modal.com health
        modal_available = self.check_modal_health()
        
        if modal_available:
            # 2. Primary Execution: Try Modal.com
            try:
                self.logger.info(f"🚀 PRIMARY: Executing bash on Modal.com: {command}")
                result = execute_bash_command.remote(command)
                self.logger.info(f"✅ Modal.com bash completed: {result['status']}")
                result["execution_method"] = "Modal.com Cloud"
                return result
                
            except Exception as e:
                self.logger.warning(f"⚠️ Modal.com bash failed, falling back to local: {e}")
                self._modal_healthy = False
        
        # 3. Fallback Execution: Local bash
        self.logger.info(f"🔄 FALLBACK: Executing bash locally: {command}")
        return self._execute_bash_fallback(command)
    
    def _execute_bash_fallback(self, command: str) -> Dict[str, Any]:
        """Local bash fallback execution"""
        try:
            import subprocess
            
            result = subprocess.run(command, shell=True, 
                                  capture_output=True, text=True, timeout=30)
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "return_code": result.returncode,
                "execution_method": "Local Bash"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "output": "",
                "error": "Local bash command timed out after 30 seconds",
                "execution_method": "Local Bash"
            }
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"Local bash execution failed: {str(e)}",
                "execution_method": "Local Bash"
            }

# Health check function for Modal.com connectivity
@app.function(image=base_image, timeout=10)
def modal_health_check():
    """Quick health check for Modal.com availability"""
    import time
    return {
        "status": "success", 
        "timestamp": time.time(),
        "message": "Modal.com is healthy and ready"
    }

# Simple test function for CLI
@app.function(image=base_image)
def simple_test():
    """Simple test function for Modal.com"""
    print("🎉 Modal.com is working!")
    return {"status": "success", "message": "Modal.com cloud execution successful!"}

# Global executor instance
modal_executor = ModalExecutor()