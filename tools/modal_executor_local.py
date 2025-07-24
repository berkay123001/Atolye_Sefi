"""
Modal.com LOCAL DEVELOPMENT VERSION
Direct local execution without serve mode
"""

import subprocess
import sys
import tempfile
import os
from typing import Dict, Any

class ModalExecutor:
    """Local development version of Modal executor"""
    
    @staticmethod
    def execute_python_code(code: str, use_gpu: bool = False, requirements: list = None) -> Dict[str, Any]:
        """Execute Python code locally"""
        try:
            print(f"🐍 LOCAL: Executing Python code (GPU simulation: {use_gpu})")
            
            # Create temp file
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
    
    @staticmethod  
    def execute_bash_command(command: str) -> Dict[str, Any]:
        """Execute bash command locally"""
        try:
            print(f"⚡ LOCAL: Executing bash: {command}")
            
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

# Create global instance
modal_executor = ModalExecutor()

# For backward compatibility, create function aliases
def execute_simple_code(code: str) -> Dict[str, Any]:
    """Local development wrapper"""
    return modal_executor.execute_python_code(code, use_gpu=False)

def execute_gpu_code(code: str) -> Dict[str, Any]:  
    """Local development wrapper"""
    return modal_executor.execute_python_code(code, use_gpu=True)

def execute_bash_command(command: str) -> Dict[str, Any]:
    """Local development wrapper""" 
    return modal_executor.execute_bash_command(command)
