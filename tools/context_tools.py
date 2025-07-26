"""
🧠 CONTEXT TOOLS - GitHub Copilot-level Project Awareness
Professional project context scanning and caching for GraphAgent
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import time

@dataclass
class FileContext:
    """Structured file context information"""
    path: str
    size: int
    last_modified: float
    content_preview: str  # First 500 chars for performance
    file_type: str
    is_code: bool
    imports: List[str]  # For Python files
    classes: List[str]  # For Python files
    functions: List[str]  # For Python files

@dataclass
class ProjectContext:
    """Complete project context"""
    root_path: str
    scan_timestamp: float
    total_files: int
    code_files: int
    file_tree: Dict[str, Any]
    files: Dict[str, FileContext]
    dependencies: Dict[str, List[str]]  # requirements.txt, package.json, etc.
    architecture_summary: str
    key_entry_points: List[str]

class ProjectContextManager:
    """
    High-performance project context manager with intelligent caching
    Provides GitHub Copilot-level project awareness
    """
    
    def __init__(self, root_path: str = None, cache_duration: int = 300):
        """
        Initialize context manager
        
        Args:
            root_path: Project root directory (auto-detect if None)
            cache_duration: Cache validity in seconds (default: 5 minutes)
        """
        self.root_path = root_path or self._detect_project_root()
        self.cache_duration = cache_duration
        self.cache_file = os.path.join(self.root_path, '.context_cache.json')
        self._context_cache: Optional[ProjectContext] = None
        
        # Performance settings
        self.max_file_size = 1024 * 1024  # 1MB max file size
        self.content_preview_length = 500  # First 500 chars
        self.max_files_scan = 1000  # Prevent runaway scans
        
        # File type patterns
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', 
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.sql', '.html', '.css', '.scss', '.less', '.vue', '.svelte'
        }
        
        self.ignore_patterns = {
            '__pycache__', '.git', '.svn', 'node_modules', '.venv', 'venv',
            '.env', 'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj',
            '.pytest_cache', '.mypy_cache', '.coverage', 'htmlcov'
        }
        
        self.config_files = {
            'requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml',
            'setup.py', 'Dockerfile', 'docker-compose.yml', '.env.example',
            'config.py', 'settings.py', 'CLAUDE.md', 'README.md'
        }
    
    def _detect_project_root(self) -> str:
        """Auto-detect project root directory"""
        current = os.getcwd()
        indicators = {'.git', 'requirements.txt', 'package.json', 'pyproject.toml', 'CLAUDE.md'}
        
        path = Path(current)
        for parent in [path] + list(path.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return str(parent)
        
        return current
    
    def get_project_context(self, force_refresh: bool = False) -> ProjectContext:
        """
        Get complete project context with intelligent caching
        
        Args:
            force_refresh: Force rescan even if cache is valid
            
        Returns:
            ProjectContext with complete project information
        """
        if not force_refresh and self._is_cache_valid():
            if self._context_cache:
                return self._context_cache
            
            # Try loading from disk cache
            cached_context = self._load_cache_from_disk()
            if cached_context:
                self._context_cache = cached_context
                return cached_context
        
        # Perform fresh scan
        print("🔍 Scanning project structure...")
        start_time = time.time()
        
        context = self._scan_project()
        
        # Cache results
        self._context_cache = context
        self._save_cache_to_disk(context)
        
        scan_time = time.time() - start_time
        print(f"✅ Project scanned: {context.total_files} files ({context.code_files} code files) in {scan_time:.2f}s")
        
        return context
    
    def _scan_project(self) -> ProjectContext:
        """Perform comprehensive project scan"""
        files = {}
        file_tree = {}
        dependencies = {}
        scanned_count = 0
        
        # Walk directory tree
        for root, dirs, filenames in os.walk(self.root_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
            
            if scanned_count >= self.max_files_scan:
                print(f"⚠️ Scan limit reached ({self.max_files_scan} files)")
                break
            
            rel_root = os.path.relpath(root, self.root_path)
            if rel_root == '.':
                rel_root = ''
            
            for filename in filenames:
                if scanned_count >= self.max_files_scan:
                    break
                    
                full_path = os.path.join(root, filename)
                rel_path = os.path.join(rel_root, filename) if rel_root else filename
                
                try:
                    file_context = self._analyze_file(full_path, rel_path)
                    if file_context:
                        files[rel_path] = file_context
                        
                        # Handle dependencies
                        if filename in self.config_files:
                            deps = self._extract_dependencies(full_path, filename)
                            if deps:
                                dependencies[filename] = deps
                        
                        scanned_count += 1
                        
                except Exception as e:
                    print(f"⚠️ Error scanning {rel_path}: {e}")
                    continue
        
        # Build file tree
        file_tree = self._build_file_tree(files.keys())
        
        # Generate architecture summary
        architecture_summary = self._generate_architecture_summary(files)
        
        # Identify key entry points
        key_entry_points = self._identify_entry_points(files)
        
        return ProjectContext(
            root_path=self.root_path,
            scan_timestamp=time.time(),
            total_files=len(files),
            code_files=sum(1 for f in files.values() if f.is_code),
            file_tree=file_tree,
            files=files,
            dependencies=dependencies,
            architecture_summary=architecture_summary,
            key_entry_points=key_entry_points
        )
    
    def _analyze_file(self, full_path: str, rel_path: str) -> Optional[FileContext]:
        """Analyze individual file and extract context"""
        try:
            stat = os.stat(full_path)
            
            # Skip large files for performance
            if stat.st_size > self.max_file_size:
                return None
            
            # Determine file type
            ext = Path(full_path).suffix.lower()
            is_code = ext in self.code_extensions
            file_type = ext[1:] if ext else 'unknown'
            
            # Read content preview
            content_preview = ""
            imports = []
            classes = []
            functions = []
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(self.content_preview_length)
                    content_preview = content
                    
                    # Extract Python-specific information
                    if ext == '.py' and content:
                        imports = self._extract_python_imports(content)
                        classes = self._extract_python_classes(content)
                        functions = self._extract_python_functions(content)
                        
            except UnicodeDecodeError:
                # Binary file, skip content analysis
                content_preview = "<binary file>"
            
            return FileContext(
                path=rel_path,
                size=stat.st_size,
                last_modified=stat.st_mtime,
                content_preview=content_preview,
                file_type=file_type,
                is_code=is_code,
                imports=imports,
                classes=classes,
                functions=functions
            )
            
        except Exception as e:
            print(f"⚠️ Error analyzing {rel_path}: {e}")
            return None
    
    def _extract_python_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code"""
        imports = []
        lines = content.split('\n')[:50]  # Only check first 50 lines for performance
        
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return imports
    
    def _extract_python_classes(self, content: str) -> List[str]:
        """Extract class definitions from Python code"""
        classes = []
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('class ') and ':' in stripped:
                class_name = stripped.split('class ')[1].split('(')[0].split(':')[0].strip()
                classes.append(class_name)
        
        return classes
    
    def _extract_python_functions(self, content: str) -> List[str]:
        """Extract function definitions from Python code"""
        functions = []
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') and ':' in stripped:
                func_name = stripped.split('def ')[1].split('(')[0].strip()
                functions.append(func_name)
        
        return functions
    
    def _extract_dependencies(self, file_path: str, filename: str) -> List[str]:
        """Extract dependencies from config files"""
        deps = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if filename == 'requirements.txt':
                    deps = [line.strip().split('==')[0].split('>=')[0].split('<=')[0] 
                           for line in content.split('\n') 
                           if line.strip() and not line.startswith('#')]
                
                elif filename == 'package.json':
                    try:
                        data = json.loads(content)
                        deps.extend(data.get('dependencies', {}).keys())
                        deps.extend(data.get('devDependencies', {}).keys())
                    except json.JSONDecodeError:
                        pass
                
        except Exception:
            pass
        
        return [dep for dep in deps if dep]
    
    def _build_file_tree(self, file_paths: List[str]) -> Dict[str, Any]:
        """Build hierarchical file tree structure"""
        tree = {}
        
        for path in file_paths:
            parts = path.split(os.sep)
            current = tree
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Leaf node (file)
                    current[part] = None
                else:
                    # Directory node
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        return tree
    
    def _generate_architecture_summary(self, files: Dict[str, FileContext]) -> str:
        """Generate high-level architecture summary"""
        summary_parts = []
        
        # Count file types
        type_counts = {}
        for file_ctx in files.values():
            if file_ctx.is_code:
                type_counts[file_ctx.file_type] = type_counts.get(file_ctx.file_type, 0) + 1
        
        if type_counts:
            summary_parts.append(f"Code files: {dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True))}")
        
        # Key frameworks/libraries
        all_imports = []
        for file_ctx in files.values():
            all_imports.extend(file_ctx.imports)
        
        frameworks = set()
        for imp in all_imports:
            if 'flask' in imp.lower():
                frameworks.add('Flask')
            elif 'django' in imp.lower():
                frameworks.add('Django')
            elif 'fastapi' in imp.lower():
                frameworks.add('FastAPI')
            elif 'langchain' in imp.lower():
                frameworks.add('LangChain')
            elif 'modal' in imp.lower():
                frameworks.add('Modal.com')
            elif 'torch' in imp.lower():
                frameworks.add('PyTorch')
            elif 'tensorflow' in imp.lower():
                frameworks.add('TensorFlow')
        
        if frameworks:
            summary_parts.append(f"Frameworks: {', '.join(sorted(frameworks))}")
        
        return ' | '.join(summary_parts) if summary_parts else "Mixed codebase"
    
    def _identify_entry_points(self, files: Dict[str, FileContext]) -> List[str]:
        """Identify key entry points in the project"""
        entry_points = []
        
        # Look for main files
        main_patterns = ['main.py', 'app.py', 'server.py', 'manage.py', 'run.py']
        for pattern in main_patterns:
            if pattern in files:
                entry_points.append(pattern)
        
        # Look for files with main execution
        for path, file_ctx in files.items():
            if file_ctx.file_type == 'py' and '__main__' in file_ctx.content_preview:
                if path not in entry_points:
                    entry_points.append(path)
        
        # Add important config files
        config_files = ['config.py', 'settings.py', 'CLAUDE.md']
        for config_file in config_files:
            if config_file in files and config_file not in entry_points:
                entry_points.append(config_file)
        
        return entry_points[:10]  # Limit to top 10
    
    def _is_cache_valid(self) -> bool:
        """Check if current cache is still valid"""
        if not self._context_cache:
            return False
        
        age = time.time() - self._context_cache.scan_timestamp
        return age < self.cache_duration
    
    def _load_cache_from_disk(self) -> Optional[ProjectContext]:
        """Load cached context from disk"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check cache age
            age = time.time() - data.get('scan_timestamp', 0)
            if age > self.cache_duration:
                return None
            
            # Convert file contexts back to dataclass instances
            files = {}
            for path, file_data in data.get('files', {}).items():
                files[path] = FileContext(
                    path=file_data['path'],
                    size=file_data['size'],
                    last_modified=file_data['last_modified'],
                    content_preview=file_data['content_preview'],
                    file_type=file_data['file_type'],
                    is_code=file_data['is_code'],
                    imports=file_data['imports'],
                    classes=file_data['classes'],
                    functions=file_data['functions']
                )
            
            return ProjectContext(
                root_path=data['root_path'],
                scan_timestamp=data['scan_timestamp'],
                total_files=data['total_files'],
                code_files=data['code_files'],
                file_tree=data['file_tree'],
                files=files,
                dependencies=data['dependencies'],
                architecture_summary=data['architecture_summary'],
                key_entry_points=data['key_entry_points']
            )
            
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            return None
    
    def _save_cache_to_disk(self, context: ProjectContext):
        """Save context cache to disk"""
        try:
            # Convert to serializable format
            data = asdict(context)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def get_file_context(self, file_path: str) -> Optional[FileContext]:
        """Get context for a specific file"""
        context = self.get_project_context()
        return context.files.get(file_path)
    
    def search_files(self, query: str, file_type: str = None) -> List[FileContext]:
        """Search files by content or name"""
        context = self.get_project_context()
        results = []
        
        query_lower = query.lower()
        
        for file_ctx in context.files.values():
            if file_type and file_ctx.file_type != file_type:
                continue
            
            # Search in file path
            if query_lower in file_ctx.path.lower():
                results.append(file_ctx)
                continue
            
            # Search in content preview
            if query_lower in file_ctx.content_preview.lower():
                results.append(file_ctx)
                continue
            
            # Search in imports/classes/functions
            if any(query_lower in item.lower() for item in 
                   file_ctx.imports + file_ctx.classes + file_ctx.functions):
                results.append(file_ctx)
        
        return results
    
    def get_context_summary(self) -> str:
        """Get a concise project context summary for LLM"""
        context = self.get_project_context()
        
        summary = f"""
🏗️ PROJECT CONTEXT SUMMARY:
📁 Root: {os.path.basename(context.root_path)}
📊 Files: {context.total_files} total ({context.code_files} code files)
🔧 Architecture: {context.architecture_summary}
🚀 Entry Points: {', '.join(context.key_entry_points[:5])}
📦 Dependencies: {', '.join(list(context.dependencies.keys())[:3])}

📂 Key Directories:
{self._format_file_tree(context.file_tree, max_depth=2)}
        """.strip()
        
        return summary
    
    def _format_file_tree(self, tree: Dict[str, Any], prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
        """Format file tree for display"""
        if current_depth >= max_depth:
            return ""
        
        lines = []
        items = list(tree.items())[:10]  # Limit items
        
        for i, (name, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            lines.append(f"{prefix}{current_prefix}{name}")
            
            if isinstance(subtree, dict) and subtree:
                next_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(self._format_file_tree(subtree, next_prefix, max_depth, current_depth + 1))
        
        return "\n".join(filter(None, lines))

# Global instance for easy access
project_context = ProjectContextManager()

def get_project_context_summary() -> str:
    """Quick access function for project context summary"""
    return project_context.get_context_summary()

def search_project_files(query: str, file_type: str = None) -> List[FileContext]:
    """Quick access function for file search"""
    return project_context.search_files(query, file_type)

def get_project_file_context(file_path: str) -> Optional[FileContext]:
    """Quick access function for specific file context"""
    return project_context.get_file_context(file_path)