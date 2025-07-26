#!/usr/bin/env python3
"""
🔍 ATÖLYE ŞEFİ - PROFESSIONAL LOGGING SYSTEM
Sistematik log yönetimi ve monitoring
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json


class AtolyeSefiLogger:
    """Professional logging system for Atölye Şefi"""
    
    def __init__(self, name: str = "atolye_sefi"):
        self.name = name
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create specialized loggers
        self.system_logger = self._create_logger("system", "system.log")
        self.agent_logger = self._create_logger("agent", "agent.log")
        self.user_logger = self._create_logger("user", "user_interactions.log")
        self.error_logger = self._create_logger("error", "errors.log")
        
        # Main logger
        self.logger = self._create_logger("main", "atolye_sefi.log")
        
        self.log_startup()
    
    def _create_logger(self, name: str, filename: str) -> logging.Logger:
        """Create a specialized logger with file rotation"""
        
        logger = logging.getLogger(f"{self.name}.{name}")
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Professional formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)20s | %(funcName)15s:%(lineno)4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_startup(self):
        """Log system startup"""
        self.system_logger.info("🚀 Atölye Şefi System Starting")
        self.system_logger.info(f"📁 Logs directory: {self.logs_dir.absolute()}")
        self.system_logger.info(f"🐍 Python version: {sys.version}")
        self.system_logger.info(f"💻 Working directory: {os.getcwd()}")
    
    def log_user_interaction(self, user_query: str, response: str, 
                           execution_time: float, method: str = "unknown"):
        """Log user interactions with structured data"""
        interaction_data = {
            "timestamp": datetime.now().isoformat(),
            "query": user_query,
            "response_length": len(response),
            "execution_time": execution_time,
            "method": method,
            "success": not response.startswith("❌")
        }
        
        self.user_logger.info(f"USER_INTERACTION: {json.dumps(interaction_data, ensure_ascii=False)}")
    
    def log_agent_activity(self, activity: str, details: Dict[str, Any]):
        """Log AI agent activities"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "details": details
        }
        
        self.agent_logger.info(f"AGENT_ACTIVITY: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_file_creation(self, filename: str, success: bool, size: Optional[int] = None):
        """Log file creation events"""
        self.log_agent_activity("file_creation", {
            "filename": filename,
            "success": success,
            "size_bytes": size,
            "full_path": os.path.abspath(filename) if success else None
        })
    
    def log_code_execution(self, code: str, result: Dict[str, Any]):
        """Log code execution events"""
        self.log_agent_activity("code_execution", {
            "code_snippet": code[:200] + "..." if len(code) > 200 else code,
            "status": result.get("status", "unknown"),
            "execution_time": result.get("execution_time", 0),
            "output_length": len(result.get("output", "")),
            "error": result.get("error") if result.get("status") == "error" else None
        })
    
    def log_modal_execution(self, function_name: str, result: Dict[str, Any]):
        """Log Modal.com function executions"""
        self.system_logger.info(f"🚀 Modal function: {function_name}")
        self.log_agent_activity("modal_execution", {
            "function": function_name,
            "status": result.get("status", "unknown"),
            "result": str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
        })
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """Log errors with full context"""
        import traceback
        
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        self.error_logger.error(f"ERROR: {json.dumps(error_data, ensure_ascii=False)}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "seconds"):
        """Log performance metrics"""
        self.system_logger.info(f"📊 PERFORMANCE: {metric_name} = {value:.4f} {unit}")
    
    def log_system_health(self, health_data: Dict[str, Any]):
        """Log system health checks"""
        self.system_logger.info(f"💚 HEALTH_CHECK: {json.dumps(health_data, ensure_ascii=False)}")
    
    def get_recent_logs(self, log_type: str = "main", lines: int = 50) -> str:
        """Get recent log entries"""
        log_file = self.logs_dir / f"{log_type}.log"
        
        if not log_file.exists():
            return f"Log file {log_file} not found"
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except Exception as e:
            return f"Error reading log file: {e}"


# Global logger instance
logger = AtolyeSefiLogger()


# Convenience functions
def log_user_interaction(query: str, response: str, execution_time: float, method: str = "unknown"):
    """Convenience function for logging user interactions"""
    logger.log_user_interaction(query, response, execution_time, method)


def log_agent_activity(activity: str, details: Dict[str, Any]):
    """Convenience function for logging agent activities"""
    logger.log_agent_activity(activity, details)


def log_error(error: Exception, context: Optional[str] = None):
    """Convenience function for logging errors"""
    logger.log_error(error, context)


def log_file_creation(filename: str, success: bool, size: Optional[int] = None):
    """Convenience function for logging file creation"""
    logger.log_file_creation(filename, success, size)


def log_code_execution(code: str, result: Dict[str, Any]):
    """Convenience function for logging code execution"""
    logger.log_code_execution(code, result)


def log_performance_metric(metric_name: str, value: float, unit: str = "seconds"):
    """Convenience function for logging performance metrics"""
    logger.log_performance_metric(metric_name, value, unit)


# Example usage and test
if __name__ == "__main__":
    # Test logging system
    logger.logger.info("🧪 Testing logging system...")
    
    # Test user interaction logging
    log_user_interaction(
        "hesap makinesi oluştur", 
        "✅ Hesap makinesi başarıyla oluşturuldu", 
        1.23, 
        "file_creation"
    )
    
    # Test agent activity logging
    log_agent_activity("file_creation", {
        "filename": "test.py",
        "success": True,
        "method": "direct_write"
    })
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        log_error(e, "Testing error logging system")
    
    # Test performance metric
    log_performance_metric("response_time", 0.156, "seconds")
    
    print("✅ Logging system test completed!")
    print(f"📁 Check logs in: {logger.logs_dir.absolute()}")