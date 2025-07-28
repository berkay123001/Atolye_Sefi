#!/usr/bin/env python3
"""
🚀 ENHANCED FILE OPERATIONS - World-Class File Tool
Using: watchdog + pathlib + shutil (VS Code level performance)
"""

import os
import sys
import time
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import threading
import logging

# World-class libraries - proven by VS Code, PyCharm etc.
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
    
    class FileChangeHandler(FileSystemEventHandler):
        """File change event handler for real-time monitoring"""
        
        def __init__(self, callback: Optional[Callable] = None):
            super().__init__()
            self.callback = callback
            self.changes = []
            
        def on_any_event(self, event):
            """Handle any file system event"""
            if event.is_directory:
                return
                
            change_info = {
                "event_type": event.event_type,
                "file_path": event.src_path,
                "timestamp": datetime.now().isoformat(),
                "is_directory": event.is_directory
            }
            
            self.changes.append(change_info)
            
            if self.callback:
                self.callback(change_info)
            
            # Log the change
            print(f"📁 File {event.event_type}: {event.src_path}")
            
except ImportError:
    print("⚠️ watchdog not installed. File monitoring will be disabled.")
    print("💡 Install with: pip install watchdog")
    WATCHDOG_AVAILABLE = False
    
    # Dummy class for when watchdog is not available
    class FileChangeHandler:
        """File change event handler for real-time monitoring (dummy)"""
        
        def __init__(self, callback: Optional[Callable] = None):
            self.callback = callback
            self.changes = []

class EnhancedFileOperations:
    """
    World-class file operations using battle-tested libraries
    Performance target: <1ms for basic ops, <100ms for monitoring setup
    """
    
    def __init__(self):
        """Initialize enhanced file operations"""
        self.logger = logging.getLogger("enhanced_file_ops")
        self.observers = {}  # Active file watchers
        self.watchers = {}   # Watcher metadata
        self.operation_count = 0
        self.start_time = time.time()
        
        # Performance tracking
        self.performance_stats = {
            "operations": 0,
            "total_time": 0.0,
            "average_time": 0.0,
            "errors": 0
        }
        
        print("🚀 EnhancedFileOperations initialized")
        print(f"📁 pathlib available: ✅")
        print(f"📁 shutil available: ✅") 
        print(f"👀 watchdog available: {'✅' if WATCHDOG_AVAILABLE else '❌'}")
    
    def _track_performance(self, operation_name: str, start_time: float):
        """Track operation performance"""
        execution_time = time.time() - start_time
        self.performance_stats["operations"] += 1
        self.performance_stats["total_time"] += execution_time
        self.performance_stats["average_time"] = (
            self.performance_stats["total_time"] / self.performance_stats["operations"]
        )
        
        # Performance warning
        if execution_time > 2.0:  # 2 second threshold
            self.logger.warning(f"{operation_name} took {execution_time:.2f}s (slow)")
        
        return execution_time
    
    def _safe_execute(self, operation_name: str, func, *args, **kwargs) -> Dict[str, Any]:
        """Safely execute file operation with error handling"""
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = self._track_performance(operation_name, start_time)
            
            return {
                "success": True,
                "result": result,
                "operation": operation_name,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except FileNotFoundError as e:
            self.performance_stats["errors"] += 1
            return {
                "success": False,
                "error": f"File not found: {str(e)}",
                "error_type": "FileNotFoundError",
                "operation": operation_name,
                "suggestion": "Check if file/directory exists"
            }
            
        except PermissionError as e:
            self.performance_stats["errors"] += 1
            return {
                "success": False,
                "error": f"Permission denied: {str(e)}",
                "error_type": "PermissionError", 
                "operation": operation_name,
                "suggestion": "Check file permissions or run with appropriate privileges"
            }
            
        except Exception as e:
            self.performance_stats["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "operation": operation_name,
                "suggestion": "Check operation parameters and try again"
            }
    
    # === CORE FILE OPERATIONS ===
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Read file content with performance tracking
        Target: <10ms for files under 1MB
        """
        def _read():
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")
            
            content = path.read_text(encoding=encoding)
            return {
                "content": content,
                "size": len(content),
                "path": str(path.absolute()),
                "encoding": encoding
            }
        
        return self._safe_execute("read_file", _read)
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                   create_dirs: bool = True) -> Dict[str, Any]:
        """
        Write file content with automatic directory creation
        Target: <50ms for files under 1MB
        """
        def _write():
            path = Path(file_path)
            
            # Create parent directories if needed
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            path.write_text(content, encoding=encoding)
            return {
                "path": str(path.absolute()),
                "size": len(content),
                "encoding": encoding,
                "created_dirs": create_dirs
            }
        
        return self._safe_execute("write_file", _write)
    
    def create_directory(self, dir_path: str, parents: bool = True) -> Dict[str, Any]:
        """
        Create directory with parent creation support
        Target: <10ms
        """
        def _create_dir():
            path = Path(dir_path)
            if path.exists():
                return {
                    "path": str(path.absolute()),
                    "already_exists": True,
                    "is_directory": path.is_dir()
                }
            
            path.mkdir(parents=parents, exist_ok=True)
            return {
                "path": str(path.absolute()),
                "created": True,
                "parents_created": parents
            }
        
        return self._safe_execute("create_directory", _create_dir)
    
    # === ADVANCED OPERATIONS ===
    
    def copy_file(self, source: str, destination: str, preserve_metadata: bool = True) -> Dict[str, Any]:
        """
        Copy single file with metadata preservation
        Target: <100ms for files under 10MB
        """
        def _copy():
            src_path = Path(source)
            dst_path = Path(destination)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Source file does not exist: {source}")
            
            # Create destination directory if needed
            if not dst_path.parent.exists():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if preserve_metadata:
                shutil.copy2(src_path, dst_path)  # Preserves metadata
            else:
                shutil.copy(src_path, dst_path)   # Just content
            
            return {
                "source": str(src_path.absolute()),
                "destination": str(dst_path.absolute()),
                "size": dst_path.stat().st_size,
                "metadata_preserved": preserve_metadata
            }
        
        return self._safe_execute("copy_file", _copy)
    
    def copy_tree(self, source: str, destination: str, ignore_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Copy entire directory tree with ignore patterns
        Target: <2s for 100 files
        """
        def _copy_tree():
            src_path = Path(source)
            dst_path = Path(destination)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Source directory does not exist: {source}")
            
            # Setup ignore patterns
            ignore_func = None
            if ignore_patterns:
                ignore_func = shutil.ignore_patterns(*ignore_patterns)
            
            # Copy tree (shutil handles everything efficiently)
            shutil.copytree(src_path, dst_path, ignore=ignore_func, dirs_exist_ok=True)
            
            # Count copied files
            copied_files = list(dst_path.rglob('*'))
            copied_count = len([f for f in copied_files if f.is_file()])
            
            return {
                "source": str(src_path.absolute()),
                "destination": str(dst_path.absolute()),
                "files_copied": copied_count,
                "ignored_patterns": ignore_patterns or []
            }
        
        return self._safe_execute("copy_tree", _copy_tree)
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Move file or directory (atomic when possible)
        Target: <50ms for single files
        """
        def _move():
            src_path = Path(source)
            dst_path = Path(destination)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Source does not exist: {source}")
            
            # Create destination directory if needed
            if not dst_path.parent.exists():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use shutil.move for cross-filesystem compatibility
            final_path = shutil.move(str(src_path), str(dst_path))
            
            return {
                "source": str(src_path.absolute()),
                "destination": final_path,
                "was_directory": src_path.is_dir() if src_path.exists() else None
            }
        
        return self._safe_execute("move_file", _move)
    
    def delete_file(self, file_path: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Delete file or directory with safety confirmation
        Target: <10ms
        """
        def _delete():
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "path": file_path,
                    "already_deleted": True
                }
            
            if not confirm:
                return {
                    "path": file_path,
                    "error": "Deletion requires confirmation (confirm=True)",
                    "safety_check": "Prevented accidental deletion"
                }
            
            was_directory = path.is_dir()
            
            if was_directory:
                shutil.rmtree(path)
            else:
                path.unlink()
            
            return {
                "path": str(path.absolute()),
                "deleted": True,
                "was_directory": was_directory
            }
        
        return self._safe_execute("delete_file", _delete)
    
    # === FILE MONITORING ===
    
    def start_watching(self, directory: str, callback: Optional[Callable] = None, 
                      recursive: bool = True) -> Dict[str, Any]:
        """
        Start real-time directory monitoring (VS Code level)
        Target: <100ms setup time
        """
        if not WATCHDOG_AVAILABLE:
            return {
                "success": False,
                "error": "watchdog library not available",
                "suggestion": "Install with: pip install watchdog"
            }
        
        def _start_watching():
            dir_path = Path(directory)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {directory}")
            
            # Create handler
            handler = FileChangeHandler(callback)
            
            # Create observer
            observer = Observer()
            observer.schedule(handler, str(dir_path), recursive=recursive)
            
            # Start monitoring
            observer.start()
            
            # Store watcher info
            watch_id = f"watch_{len(self.observers)}"
            self.observers[watch_id] = observer
            self.watchers[watch_id] = {
                "directory": str(dir_path.absolute()),
                "recursive": recursive,
                "start_time": datetime.now().isoformat(),
                "handler": handler
            }
            
            return {
                "watch_id": watch_id,
                "directory": str(dir_path.absolute()),
                "recursive": recursive,
                "monitoring": True
            }
        
        return self._safe_execute("start_watching", _start_watching)
    
    def stop_watching(self, watch_id: str) -> Dict[str, Any]:
        """
        Stop directory monitoring
        Target: <50ms
        """
        def _stop_watching():
            if watch_id not in self.observers:
                return {
                    "watch_id": watch_id,
                    "already_stopped": True
                }
            
            observer = self.observers[watch_id]
            observer.stop()
            observer.join()
            
            watcher_info = self.watchers.pop(watch_id)
            del self.observers[watch_id]
            
            return {
                "watch_id": watch_id,
                "stopped": True,
                "was_monitoring": watcher_info["directory"]
            }
        
        return self._safe_execute("stop_watching", _stop_watching)
    
    def get_watch_status(self) -> Dict[str, Any]:
        """Get status of all active watchers"""
        return {
            "success": True,
            "active_watchers": len(self.observers),
            "watchers": {
                watch_id: {
                    "directory": info["directory"],
                    "recursive": info["recursive"], 
                    "start_time": info["start_time"],
                    "changes_detected": len(info["handler"].changes)
                }
                for watch_id, info in self.watchers.items()
            }
        }
    
    # === UTILITY OPERATIONS ===
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information
        Target: <10ms
        """
        def _get_info():
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Path does not exist: {file_path}")
            
            stat = path.stat()
            
            info = {
                "path": str(path.absolute()),
                "name": path.name,
                "size": stat.st_size,
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            if path.is_file():
                # Additional file info
                info.update({
                    "extension": path.suffix,
                    "stem": path.stem,
                    "size_human": self._human_readable_size(stat.st_size)
                })
            
            return info
        
        return self._safe_execute("get_file_info", _get_info)
    
    def list_directory(self, directory: str, pattern: str = "*", 
                      recursive: bool = False) -> Dict[str, Any]:
        """
        List directory contents with pattern matching
        Target: <100ms for directories with <1000 files
        """
        def _list_dir():
            dir_path = Path(directory)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {directory}")
            
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))
            
            file_list = []
            for file_path in files:
                stat = file_path.stat()
                file_list.append({
                    "name": file_path.name,
                    "path": str(file_path.absolute()),
                    "is_file": file_path.is_file(),
                    "is_directory": file_path.is_dir(),
                    "size": stat.st_size if file_path.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return {
                "directory": str(dir_path.absolute()),
                "pattern": pattern,
                "recursive": recursive,
                "files": file_list,
                "count": len(file_list)
            }
        
        return self._safe_execute("list_directory", _list_dir)
    
    def calculate_directory_size(self, directory: str) -> Dict[str, Any]:
        """
        Calculate total directory size
        Target: <1s for directories with <1000 files
        """
        def _calc_size():
            dir_path = Path(directory)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {directory}")
            
            total_size = 0
            file_count = 0
            
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                "directory": str(dir_path.absolute()),
                "total_size": total_size,
                "size_human": self._human_readable_size(total_size),
                "file_count": file_count
            }
        
        return self._safe_execute("calculate_directory_size", _calc_size)
    
    @staticmethod
    def _human_readable_size(size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    # === PERFORMANCE & STATUS ===
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        uptime = time.time() - self.start_time
        
        return {
            "success": True,
            "uptime_seconds": uptime,
            "operations_completed": self.performance_stats["operations"],
            "total_execution_time": self.performance_stats["total_time"],
            "average_execution_time": self.performance_stats["average_time"],
            "errors_encountered": self.performance_stats["errors"],
            "operations_per_second": self.performance_stats["operations"] / uptime if uptime > 0 else 0,
            "active_watchers": len(self.observers),
            "memory_usage": "Not implemented"  # Could add psutil integration
        }
    
    def cleanup(self):
        """Cleanup resources (stop all watchers)"""
        for watch_id in list(self.observers.keys()):
            self.stop_watching(watch_id)
        
        print("🧹 EnhancedFileOperations cleanup completed")

# === AUTOGEN COMPATIBILITY ===

def get_enhanced_file_ops_schema() -> Dict[str, Any]:
    """AutoGen-compatible function schema"""
    return {
        "name": "enhanced_file_operations",
        "description": "World-class file operations with real-time monitoring",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "read_file", "write_file", "create_directory",
                        "copy_file", "copy_tree", "move_file", "delete_file",
                        "start_watching", "stop_watching", "get_watch_status",
                        "get_file_info", "list_directory", "calculate_directory_size",
                        "get_performance_stats"
                    ],
                    "description": "File operation to perform"
                },
                "file_path": {"type": "string", "description": "File or directory path"},
                "content": {"type": "string", "description": "Content for write operations"},
                "source": {"type": "string", "description": "Source path for copy/move operations"},
                "destination": {"type": "string", "description": "Destination path for copy/move operations"},
                "directory": {"type": "string", "description": "Directory path for monitoring/listing"},
                "pattern": {"type": "string", "description": "File pattern for filtering"},
                "recursive": {"type": "boolean", "description": "Recursive operation flag"},
                "confirm": {"type": "boolean", "description": "Confirmation for dangerous operations"}
            },
            "required": ["operation"]
        }
    }

# === FACTORY FUNCTION ===

def create_enhanced_file_ops():
    """Factory function for creating EnhancedFileOperations instance"""
    return EnhancedFileOperations()

if __name__ == "__main__":
    # Quick test
    print("🧪 Testing EnhancedFileOperations...")
    
    ops = EnhancedFileOperations()
    
    # Test basic operations
    test_file = "/tmp/test_enhanced_file_ops.txt"
    
    # Write test
    result = ops.write_file(test_file, "Hello Enhanced File Operations!")
    print(f"Write test: {result}")
    
    # Read test
    result = ops.read_file(test_file)
    print(f"Read test: {result}")
    
    # Performance stats
    stats = ops.get_performance_stats()
    print(f"Performance: {stats}")
    
    # Cleanup
    ops.cleanup()
    print("✅ Basic tests completed!")