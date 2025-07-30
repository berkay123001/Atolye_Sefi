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
        """Enhanced workspace scanning with cross-file analysis"""
        print(f"🔍 Enhanced workspace scanning: {self.workspace_root}")
        
        # Enhanced context storage
        self.workspace_modules = {}  # module_name -> file_path
        self.function_definitions = {}  # function_name -> (file_path, line, signature)
        self.class_definitions = {}  # class_name -> (file_path, line, methods)
        self.import_map = {}  # file_path -> list of imports
        
        for root, dirs, files in os.walk(self.workspace_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.workspace_root)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.workspace_files[relative_path] = content
                            
                            # Enhanced analysis with Jedi
                            script = jedi.Script(code=content, path=file_path)
                            
                            # Analyze imports
                            imports = []
                            for line_num, line in enumerate(content.split('\n'), 1):
                                if line.strip().startswith(('import ', 'from ')):
                                    imports.append((line_num, line.strip()))
                            self.import_map[relative_path] = imports
                            
                            # Analyze definitions using Jedi
                            names = script.get_names(all_scopes=True, definitions=True)
                            for name in names:
                                if name.type == 'module':
                                    module_name = name.name
                                    self.workspace_modules[module_name] = relative_path
                                    self.workspace_imports.add(module_name)
                                    
                                elif name.type == 'class':
                                    class_name = name.name
                                    self.workspace_classes.add(class_name)
                                    
                                    # Get class methods
                                    try:
                                        class_methods = []
                                        for child in name.defined_names():
                                            if child.type == 'function':
                                                class_methods.append(child.name)
                                        
                                        self.class_definitions[class_name] = {
                                            'file': relative_path,
                                            'line': name.line if hasattr(name, 'line') else 0,
                                            'methods': class_methods
                                        }
                                    except:
                                        pass
                                        
                                elif name.type == 'function':
                                    func_name = name.name
                                    self.workspace_functions.add(func_name)
                                    
                                    # Get function signature
                                    try:
                                        signature = name.description if hasattr(name, 'description') else f"def {func_name}():"
                                        self.function_definitions[func_name] = {
                                            'file': relative_path,
                                            'line': name.line if hasattr(name, 'line') else 0,
                                            'signature': signature
                                        }
                                    except:
                                        pass
                                    
                    except Exception as e:
                        print(f"⚠️ Error scanning {file}: {e}")
        
        print(f"✅ Enhanced workspace context: {len(self.workspace_files)} files, "
              f"{len(self.workspace_imports)} imports, "
              f"{len(self.workspace_classes)} classes, "
              f"{len(self.workspace_functions)} functions")
        print(f"🧠 Smart analysis: {len(self.function_definitions)} function definitions, "
              f"{len(self.class_definitions)} class definitions")
    
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
    
    def get_smart_import_suggestions(self, code: str, file_path: str = None) -> List[Dict[str, Any]]:
        """
        🧠 SMART FEATURE: Auto-import resolution with workspace intelligence
        Suggests missing imports based on undefined names and workspace context
        """
        if not JEDI_AVAILABLE:
            return []
        
        suggestions = []
        
        try:
            # Parse code to find undefined names
            import ast
            tree = ast.parse(code)
            
            # Find all names used in code
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Handle module.function calls
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # Find current imports in code
            current_imports = set()
            for line in code.split('\n'):
                line = line.strip()
                if line.startswith('import '):
                    module = line.replace('import ', '').split()[0]
                    current_imports.add(module)
                elif line.startswith('from '):
                    parts = line.split()
                    if len(parts) >= 4:  # from module import item
                        module = parts[1]
                        items = ' '.join(parts[3:]).split(',')
                        current_imports.add(module)
                        for item in items:
                            current_imports.add(item.strip())
            
            # Check workspace for missing imports
            for name in used_names:
                if name not in current_imports and not name.startswith('_'):
                    # Check if it's available in workspace
                    if name in self.workspace_functions:
                        func_info = self.function_definitions.get(name, {})
                        if func_info:
                            module_path = func_info['file'].replace('.py', '').replace('/', '.')
                            suggestions.append({
                                'type': 'workspace_function',
                                'name': name,
                                'suggestion': f"from workspace.{module_path} import {name}",
                                'file': func_info['file'],
                                'priority': 100
                            })
                    
                    elif name in self.workspace_classes:
                        class_info = self.class_definitions.get(name, {})
                        if class_info:
                            module_path = class_info['file'].replace('.py', '').replace('/', '.')
                            suggestions.append({
                                'type': 'workspace_class',
                                'name': name,
                                'suggestion': f"from workspace.{module_path} import {name}",
                                'file': class_info['file'],
                                'priority': 100
                            })
                    
                    # Check common libraries
                    common_imports = {
                        'requests': 'import requests',
                        'json': 'import json',
                        'os': 'import os',
                        'sys': 'import sys',
                        'datetime': 'from datetime import datetime',
                        'pathlib': 'from pathlib import Path',
                        're': 'import re',
                        'math': 'import math',
                        'random': 'import random',
                        'numpy': 'import numpy as np',
                        'pandas': 'import pandas as pd',
                        'matplotlib': 'import matplotlib.pyplot as plt'
                    }
                    
                    if name in common_imports:
                        suggestions.append({
                            'type': 'common_library',
                            'name': name,
                            'suggestion': common_imports[name],
                            'file': 'standard/common',
                            'priority': 75
                        })
            
            # Sort by priority
            suggestions.sort(key=lambda x: x['priority'], reverse=True)
            return suggestions[:10]  # Top 10 suggestions
        
        except Exception as e:
            print(f"⚠️ Smart import analysis error: {e}")
            return []
    
    def get_cross_file_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        🧠 SMART FEATURE: Cross-file symbol tracking and references
        Find where symbols are defined and used across workspace
        """
        if not JEDI_AVAILABLE:
            return []
        
        references = []
        
        try:
            # Check function definitions
            if symbol_name in self.function_definitions:
                func_info = self.function_definitions[symbol_name]
                references.append({
                    'type': 'definition',
                    'symbol': symbol_name,
                    'file': func_info['file'],
                    'line': func_info['line'],
                    'signature': func_info['signature'],
                    'context': 'function_definition'
                })
            
            # Check class definitions
            if symbol_name in self.class_definitions:
                class_info = self.class_definitions[symbol_name]
                references.append({
                    'type': 'definition',
                    'symbol': symbol_name,
                    'file': class_info['file'],
                    'line': class_info['line'],
                    'methods': class_info['methods'],
                    'context': 'class_definition'
                })
            
            # Search for usage across workspace files
            for file_path, content in self.workspace_files.items():
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if symbol_name in line and not line.strip().startswith('#'):
                        # Determine usage context
                        context = 'usage'
                        if f"def {symbol_name}" in line:
                            context = 'definition'
                        elif f"class {symbol_name}" in line:
                            context = 'definition'
                        elif f"import {symbol_name}" in line or f"from {symbol_name}" in line:
                            context = 'import'
                        elif f"{symbol_name}(" in line:
                            context = 'function_call'
                        elif f"{symbol_name}." in line:
                            context = 'attribute_access'
                        
                        references.append({
                            'type': 'usage',
                            'symbol': symbol_name,
                            'file': file_path,
                            'line': line_num,
                            'code_line': line.strip(),
                            'context': context
                        })
            
            return references
        
        except Exception as e:
            print(f"⚠️ Cross-file reference error: {e}")
            return []
    
    def get_type_inference(self, code: str, line: int = 1, column: int = 0, 
                          file_path: str = None) -> Dict[str, Any]:
        """
        🧠 SMART FEATURE: Enhanced type inference with workspace context
        Infer types of variables and expressions using Jedi + workspace knowledge
        """
        if not JEDI_AVAILABLE:
            return {'status': 'error', 'message': 'Jedi not available'}
        
        # Ensure file_path is in workspace
        if file_path and not file_path.startswith(self.workspace_root):
            file_path = os.path.join(self.workspace_root, file_path.lstrip('./'))
        
        try:
            script = jedi.Script(
                code=code,
                path=file_path,
                project=jedi.Project(self.workspace_root)
            )
            
            # Get inferred types at cursor position
            inferred = script.infer(line, column)
            
            type_info = {
                'status': 'success',
                'position': {'line': line, 'column': column},
                'inferred_types': [],
                'workspace_enhanced': False
            }
            
            for inference in inferred:
                type_data = {
                    'name': inference.name,
                    'type': inference.type,
                    'module': str(inference.module_path) if inference.module_path else None,
                    'description': inference.description,
                    'is_builtin': inference.is_builtin_function() if hasattr(inference, 'is_builtin_function') else False
                }
                
                # Enhance with workspace knowledge
                if inference.name in self.workspace_functions:
                    func_info = self.function_definitions[inference.name]
                    type_data['workspace_info'] = {
                        'type': 'workspace_function',
                        'file': func_info['file'],
                        'signature': func_info['signature']
                    }
                    type_info['workspace_enhanced'] = True
                
                elif inference.name in self.workspace_classes:
                    class_info = self.class_definitions[inference.name]
                    type_data['workspace_info'] = {
                        'type': 'workspace_class',
                        'file': class_info['file'],
                        'methods': class_info['methods']
                    }
                    type_info['workspace_enhanced'] = True
                
                type_info['inferred_types'].append(type_data)
            
            return type_info
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Type inference failed: {str(e)}',
                'position': {'line': line, 'column': column}
            }

# Global workspace-aware Jedi instance
workspace_jedi = WorkspaceAwareJediIntelligence()

# Update workspace intelligence periodically
def refresh_workspace_intelligence():
    """Refresh workspace context - call this when files change"""
    if JEDI_AVAILABLE:
        workspace_jedi.scan_workspace_context()
        print("🔄 Workspace intelligence refreshed!")
    else:
        print("⚠️ Jedi not available for refresh")

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

@tool
def jedi_smart_import_suggestions(code: str, file_path: str = "workspace/temp.py") -> Dict[str, Any]:
    """
    🧠 SMART FEATURE: Get intelligent import suggestions for missing symbols.
    Analyzes code and suggests imports from workspace and common libraries.
    """
    print(f"\n🧬 [Smart Import] Analyzing missing imports...")
    
    suggestions = workspace_jedi.get_smart_import_suggestions(code, file_path)
    
    return {
        "status": "success",
        "suggestions": suggestions,
        "total_suggestions": len(suggestions),
        "workspace_suggestions": len([s for s in suggestions if s['type'].startswith('workspace')]),
        "common_suggestions": len([s for s in suggestions if s['type'] == 'common_library'])
    }

@tool
def jedi_cross_file_references(symbol_name: str) -> Dict[str, Any]:
    """
    🧠 SMART FEATURE: Find symbol definitions and usage across workspace files.
    Tracks where functions/classes are defined and used.
    """
    print(f"\n🔍 [Cross-File Analysis] Tracking symbol: {symbol_name}")
    
    references = workspace_jedi.get_cross_file_references(symbol_name)
    
    return {
        "status": "success",
        "symbol": symbol_name,
        "references": references,
        "total_references": len(references),
        "definitions": len([r for r in references if r['type'] == 'definition']),
        "usages": len([r for r in references if r['type'] == 'usage'])
    }

@tool
def jedi_type_inference(code: str, line: int = 1, column: int = 0, file_path: str = "workspace/temp.py") -> Dict[str, Any]:
    """
    🧠 SMART FEATURE: Enhanced type inference with workspace context.
    Infer types of variables and expressions at cursor position.
    """
    print(f"\n🔬 [Type Inference] Analyzing types at line {line}, column {column}")
    
    type_info = workspace_jedi.get_type_inference(code, line, column, file_path)
    
    return type_info