"""
Modal.com Serverless Code Executor
Replaces SSH system with cloud functions
"""

import modal
import os
from typing import Dict, Any, Optional
import logging

# Initialize Modal app
app = modal.App("atolye-sefi")

# Base image with common ML/AI packages
base_image = modal.Image.debian_slim().pip_install([
    "torch", "transformers", "pandas", "numpy", 
    "matplotlib", "scikit-learn", "requests", "pillow",
    "opencv-python", "seaborn", "plotly", "jupyter"
])

@app.function(
    gpu="T4",
    timeout=3600,
    image=base_image,
    memory=8192
)
def execute_gpu_code(code: str, requirements: Optional[list] = None) -> Dict[str, Any]:
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

@app.function(
    timeout=600,
    image=base_image,
    memory=2048
)
def execute_simple_code(code: str, requirements: Optional[list] = None) -> Dict[str, Any]:
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
        
    def execute_python_code(self, code: str, use_gpu: bool = False, 
                          requirements: Optional[list] = None) -> Dict[str, Any]:
        """Execute Python code using Modal serverless functions."""
        try:
            if use_gpu:
                self.logger.info("🚀 Executing code with GPU on Modal...")
                result = execute_gpu_code.remote(code, requirements)
            else:
                self.logger.info("🚀 Executing code on Modal...")
                result = execute_simple_code.remote(code, requirements)
                
            self.logger.info(f"✅ Modal execution completed: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Modal execution failed: {e}")
            return {
                "status": "error",
                "output": "",
                "error": f"Modal execution failed: {str(e)}"
            }
    
    def execute_bash_command(self, command: str) -> Dict[str, Any]:
        """Execute bash command using Modal."""
        try:
            self.logger.info(f"🚀 Executing bash command on Modal: {command}")
            result = execute_bash_command.remote(command)
            self.logger.info(f"✅ Bash execution completed: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Bash execution failed: {e}")
            return {
                "status": "error",
                "output": "",
                "error": f"Bash execution failed: {str(e)}"
            }

# Global executor instance
modal_executor = ModalExecutor()