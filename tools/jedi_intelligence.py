"""
🧬 JEDI INTELLIGENCE - Workspace-Aware Code Intelligence
Professional Python code analysis and completion for GraphAgent
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from pydantic.v1 import BaseModel, Field
from langchain.tools import tool

try:
    import jedi
    JEDI_AVAILABLE = True
except ImportError:
    JEDI_AVAILABLE = False
    print("⚠️ Jedi not installed. Run: pip install jedi")

class JediAnalysisInput(BaseModel):
    code: str = Field(description="Python kodu analiz edilecek")
    line: int = Field(description="Cursor line number (1-based)", default=1)
    column: int = Field(description="Cursor column number (0-based)", default=0)
    file_path: str = Field(description="Dosya yolu (workspace içinde)", default="workspace/temp.py")

class WorkspaceAwareJediIntelligence:
    """
    Workspace-focused Jedi intelligence with project context awareness
    """
    
    def __init__(self, workspace_root: str = None):
        """
        Initialize workspace-aware Jedi intelligence
        
        Args:
            workspace_root: Workspace root directory (default: ./workspace)
        """
        self.workspace_root = workspace_root or os.path.join(os.getcwd(), "workspace")
        self.ensure_workspace_exists()
        
        # Workspace project context
        self.workspace_files = {}
        self.workspace_imports = set()
        self.workspace_classes = set()
        self.workspace_functions = set()
        
        if JEDI_AVAILABLE:
            self.scan_workspace_context()
        
    def ensure_workspace_exists(self):
        """Ensure workspace directory exists"""
        os.makedirs(self.workspace_root, exist_ok=True)
        
        # Create basic workspace structure
        subdirs = ["scripts", "tests", "experiments", "temp"]
        for subdir in subdirs:
            os.makedirs(os.path.join(self.workspace_root, subdir), exist_ok=True)
    
    def scan_workspace_context(self):
        """Scan workspace for existing Python files and context"""
        print(f"🔍 Scanning workspace: {self.workspace_root}")
        
        for root, dirs, files in os.walk(self.workspace_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.workspace_files[file] = content
                            
                            # Extract imports and definitions
                            script = jedi.Script(code=content, path=file_path)
                            
                            # Get imports
                            for name in script.get_names():
                                if name.type == 'module':
                                    self.workspace_imports.add(name.name)
                                elif name.type == 'class':
                                    self.workspace_classes.add(name.name)
                                elif name.type == 'function':
                                    self.workspace_functions.add(name.name)
                                    
                    except Exception as e:
                        print(f"⚠️ Error scanning {file}: {e}")
        
        print(f"✅ Workspace context: {len(self.workspace_files)} files, "
              f"{len(self.workspace_imports)} imports, "
              f"{len(self.workspace_classes)} classes, "
              f"{len(self.workspace_functions)} functions")
    
    def get_completions(self, code: str, line: int = 1, column: int = 0, 
                       file_path: str = None) -> List[Dict[str, Any]]:
        """
        Get code completions with workspace context
        
        Args:
            code: Python code to analyze
            line: Cursor line (1-based)
            column: Cursor column (0-based)  
            file_path: Target file path in workspace
            
        Returns:
            List of completion suggestions
        """
        if not JEDI_AVAILABLE:
            return [{"name": "jedi_not_available", "type": "error"}]
        
        # Ensure file_path is in workspace
        if file_path and not file_path.startswith(self.workspace_root):
            file_path = os.path.join(self.workspace_root, file_path.lstrip('./'))
        
        try:
            # Create Jedi script with workspace context
            script = jedi.Script(
                code=code, 
                path=file_path,
                project=jedi.Project(self.workspace_root)
            )
            
            # Get completions at specific position
            completions_list = script.complete(line, column)
            
            completions = []
            for completion in completions_list:
                completions.append({
                    "name": completion.name,
                    "type": completion.type,
                    "description": completion.description,
                    "complete": completion.complete,
                    "is_workspace": self._is_workspace_symbol(completion.name),
                    "priority": self._calculate_priority(completion)
                })
            
            # Sort by priority (workspace symbols first)
            completions.sort(key=lambda x: x["priority"], reverse=True)
            
            return completions[:20]  # Top 20 suggestions
            
        except Exception as e:
            print(f"❌ Jedi completion error: {e}")
            return [{"name": "error", "type": "error", "description": str(e)}]
    
    def get_definitions(self, code: str, line: int = 1, column: int = 0,
                       file_path: str = None) -> List[Dict[str, Any]]:
        """
        Get symbol definitions with workspace awareness
        """
        if not JEDI_AVAILABLE:
            return []
        
        # Ensure file_path is in workspace
        if file_path and not file_path.startswith(self.workspace_root):
            file_path = os.path.join(self.workspace_root, file_path.lstrip('./'))
        
        try:
            script = jedi.Script(
                code=code,
                path=file_path,
                project=jedi.Project(self.workspace_root)
            )
            
            # Get definitions at specific position  
            definitions_list = script.goto(line, column)
            
            definitions = []
            for definition in definitions_list:
                definitions.append({
                    "name": definition.name,
                    "type": definition.type,
                    "module_path": str(definition.module_path) if definition.module_path else None,
                    "line": definition.line,
                    "column": definition.column,
                    "description": definition.description,
                    "is_workspace": self._is_workspace_file(definition.module_path),
                    "full_name": definition.full_name
                })
            
            return definitions
            
        except Exception as e:
            print(f"❌ Jedi definition error: {e}")
            return []
    
    def analyze_code_errors(self, code: str, file_path: str = None) -> List[Dict[str, Any]]:
        """
        Analyze code for syntax and semantic errors
        """
        if not JEDI_AVAILABLE:
            return []
        
        # Ensure file_path is in workspace
        if file_path and not file_path.startswith(self.workspace_root):
            file_path = os.path.join(self.workspace_root, file_path.lstrip('./'))
        
        try:
            script = jedi.Script(
                code=code,
                path=file_path,
                project=jedi.Project(self.workspace_root)
            )
            
            errors = []
            try:
                for error in script._get_module_context().tree.get_error_node_list():
                    errors.append({
                        "type": "syntax_error", 
                        "message": str(error),
                        "line": error.start_pos[0] if hasattr(error, 'start_pos') else 0,
                        "column": error.start_pos[1] if hasattr(error, 'start_pos') else 0,
                        "severity": "error"
                    })
            except:
                # Fallback: basic syntax check
                import ast
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    errors.append({
                        "type": "syntax_error",
                        "message": str(e),
                        "line": e.lineno or 0,
                        "column": e.offset or 0,
                        "severity": "error"
                    })
            
            return errors
            
        except Exception as e:
            print(f"❌ Jedi error analysis failed: {e}")
            return []
    
    def generate_workspace_context_summary(self) -> str:
        """
        Generate a summary of workspace context for LLM
        """
        summary = f"""
🧪 **WORKSPACE LABORATORY CONTEXT:**
📁 Location: {os.path.basename(self.workspace_root)}/
📊 Files: {len(self.workspace_files)} Python files analyzed

🧬 **Available Imports:**
{', '.join(sorted(list(self.workspace_imports)[:10]))}

🏗️ **Workspace Classes:**  
{', '.join(sorted(list(self.workspace_classes)[:10]))}

⚡ **Workspace Functions:**
{', '.join(sorted(list(self.workspace_functions)[:10]))}

💡 **Suggestion:** Use existing workspace components when possible!
        """.strip()
        
        return summary
    
    def _is_workspace_symbol(self, symbol_name: str) -> bool:
        """Check if symbol is from workspace"""
        return (symbol_name in self.workspace_classes or 
                symbol_name in self.workspace_functions or
                symbol_name in self.workspace_imports)
    
    def _is_workspace_file(self, file_path) -> bool:
        """Check if file path is in workspace"""
        if not file_path:
            return False
        return str(file_path).startswith(self.workspace_root)
    
    def _calculate_priority(self, completion) -> int:
        """Calculate completion priority (workspace items get higher priority)"""
        priority = 0
        
        # Workspace symbols get highest priority
        if self._is_workspace_symbol(completion.name):
            priority += 100
        
        # Built-in types get medium priority
        if completion.type in ['function', 'class', 'module']:
            priority += 50
        
        # Common names get bonus
        if completion.name in ['print', 'len', 'str', 'int', 'list', 'dict']:
            priority += 25
        
        return priority

# Global workspace-aware Jedi instance
workspace_jedi = WorkspaceAwareJediIntelligence()

@tool(args_schema=JediAnalysisInput)
def jedi_code_analysis(code: str, line: int = 1, column: int = 0, file_path: str = "workspace/temp.py") -> Dict[str, Any]:
    """
    Workspace-aware Python code analysis and completion using Jedi.
    Analyzes code in context of workspace laboratory.
    """
    print(f"\n🧬 [Jedi Intelligence] Analyzing code in workspace context...")
    print(f"📁 Target: {file_path}")
    print(f"📍 Position: Line {line}, Column {column}")
    
    if not JEDI_AVAILABLE:
        return {
            "status": "error",
            "message": "Jedi not available. Install with: pip install jedi",
            "completions": [],
            "definitions": [],
            "errors": []
        }
    
    # Get completions
    completions = workspace_jedi.get_completions(code, line, column, file_path)
    
    # Get definitions
    definitions = workspace_jedi.get_definitions(code, line, column, file_path)
    
    # Analyze errors
    errors = workspace_jedi.analyze_code_errors(code, file_path)
    
    # Generate workspace context
    workspace_context = workspace_jedi.generate_workspace_context_summary()
    
    result = {
        "status": "success",
        "completions": completions,
        "definitions": definitions,
        "errors": errors,
        "workspace_context": workspace_context,
        "workspace_files": list(workspace_jedi.workspace_files.keys()),
        "analysis_info": {
            "total_completions": len(completions),
            "workspace_completions": len([c for c in completions if c.get("is_workspace", False)]),
            "total_definitions": len(definitions),
            "workspace_definitions": len([d for d in definitions if d.get("is_workspace", False)]),
            "syntax_errors": len(errors)
        }
    }
    
    print(f"✅ Analysis complete: {len(completions)} completions, {len(definitions)} definitions, {len(errors)} errors")
    
    return result

@tool
def workspace_context_summary() -> Dict[str, Any]:
    """
    Get current workspace context summary for code generation guidance.
    """
    print("\n🧪 [Workspace Context] Generating laboratory summary...")
    
    context = workspace_jedi.generate_workspace_context_summary()
    
    return {
        "status": "success",
        "workspace_root": workspace_jedi.workspace_root,
        "context_summary": context,
        "files_count": len(workspace_jedi.workspace_files),
        "imports_available": list(workspace_jedi.workspace_imports),
        "classes_available": list(workspace_jedi.workspace_classes),
        "functions_available": list(workspace_jedi.workspace_functions)
    }