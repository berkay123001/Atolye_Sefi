#!/usr/bin/env python3
"""
Terminal AI Agent - Claude Code Alternative
Professional terminal assistant with real command execution capabilities
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import traceback
import shlex
import re

# Add parent directory to path to import from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from langchain_groq import ChatGroq
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_openai import ChatOpenAI  # GPT-3.5-Turbo backup
    from langchain.schema import HumanMessage
    from dotenv import load_dotenv
    load_dotenv()
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("LangChain dependencies not found. Running in fallback mode.")
    ChatGroq = None
    ChatGoogleGenerativeAI = None  
    ChatOpenAI = None
    HumanMessage = None
    LANGCHAIN_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
except ImportError:
    print("Installing required dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown

@dataclass
class TaskStep:
    id: str
    description: str
    command: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    output: str = ""
    error: str = ""
    timestamp: Optional[datetime] = None

class AdvancedIntentClassifier:
    """LLM-based intent classification for terminal commands vs chat"""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.gemini_available = True  # Track Gemini availability
        
        if self.llm is None and LANGCHAIN_AVAILABLE:
            # Try LLMs in order of preference
            self.llm = self._initialize_best_available_llm()
    
    def _initialize_best_available_llm(self):
        """Initialize the best available LLM with quota checking"""
        
        # 1. Try Gemini first (best Turkish support) with quota check
        if ChatGoogleGenerativeAI and os.getenv("GOOGLE_API_KEY") and self.gemini_available:
            try:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.1,
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    max_retries=0  # Disable LangChain's own retries for clean error handling
                )
                # Quick test to check if Gemini is working
                test_response = llm.invoke([HumanMessage(content="test")])
                print("🤖 [green]Gemini 1.5 Flash initialized (Turkish optimized)[/green]")
                return llm
            except Exception as e:
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    self.gemini_available = False
                    print("⚠️ [yellow]Gemini quota exceeded, switching to backup[/yellow]")
                else:
                    print(f"⚠️ [yellow]Gemini unavailable: {str(e)[:50]}...[/yellow]")
        
        # 2. Try GPT-3.5-Turbo backup (good Turkish support)
        if ChatOpenAI and os.getenv("OPENAI_API_KEY"):
            try:
                llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.1,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
                print("🧠 [cyan]GPT-3.5-Turbo initialized (good Turkish support)[/cyan]")
                return llm
            except Exception as e:
                print(f"⚠️ [yellow]GPT-3.5-Turbo unavailable: {str(e)[:50]}...[/yellow]")
        
        # 3. Fallback to Groq (fast but limited Turkish)
        if ChatGroq and os.getenv("GROQ_API_KEY"):
            try:
                llm = ChatGroq(
                    model_name="llama-3.1-70b-versatile",
                    temperature=0.1
                )
                print("⚡ [magenta]Groq Llama fallback initialized (limited Turkish)[/magenta]")
                return llm
            except Exception as e:
                print(f"⚠️ [yellow]Groq unavailable: {str(e)[:50]}...[/yellow]")
        
        print("❌ [red]No LLM available - using fallback classification only[/red]")
        return None
                
    def classify_intent(self, user_input: str, conversation_history: list = None) -> dict:
        """Classify user input intent using LLM"""
        if not self.llm:
            # Fallback to simple classification
            return self._fallback_classification(user_input)
            
        # Enhanced Turkish-focused prompt for Gemini
        turkish_classification_prompt = f"""Sen Türkçe uzmanı bir intent classifier'sın. 
Terminal AI agent için kullanıcı girdisini analiz et ve doğru kategoriyi belirle.

KATEGORILER:
1. CHAT - Sohbet, selamlaşma, yetenek soruları, bilgi istekleri
2. FILE_OPERATION - Dosya işlemleri (oluşturma, düzenleme, okuma, silme)
3. SYSTEM_COMMAND - Terminal komutları, paket kurulumu, sistem işlemleri
4. CODE_GENERATION - Kod yazma, geliştirme, programlama
5. EXPLANATION - Açıklama, yardım, dokümantasyon
6. PROJECT_MANAGEMENT - Çok adımlı proje görevleri

ÖNEMLİ TÜRKÇE PATTERN'LAR (Yüksek güvenle CHAT):
- "neler yapabilirsin", "ne yapabilirsin", "hangi özelliklerin var" → CHAT
- "merhaba", "nasılsın", "selam", "orda mısın" → CHAT  
- "hangi dosya dizininde", "nerede çalışıyorsun" → CHAT
- "sen kimsin", "ne tür bir asistansın" → CHAT

ÖRNEKLER:
Girdi: "sen neler yapabilirsin" → Intent: CHAT, Confidence: 0.95
Girdi: "hangi dosya dizininde çalışıyorsun" → Intent: CHAT, Confidence: 0.95
Girdi: "python dosyası oluştur" → Intent: FILE_OPERATION, Confidence: 0.90
Girdi: "run ls komutu" → Intent: SYSTEM_COMMAND, Confidence: 0.90

BAĞLAM:
Önceki konuşma: {conversation_history[-3:] if conversation_history else "Yok"}
Mevcut girdi: "{user_input}"

SADECE JSON döndür:
{{
    "intent": "kategori_adı",
    "confidence": 0.95,
    "entities": {{
        "filename": "dosya_adı_varsa",
        "command": "komut_varsa", 
        "language": "programlama_dili_varsa"
    }},
    "requires_execution": true,
    "suggested_response_type": "chat_response",
    "reasoning": "bu kategoriyi seçme nedeni"
}}"""

        try:
            response = self.llm.invoke([HumanMessage(content=turkish_classification_prompt)])
            return self._parse_json_safe(response.content)
        except Exception as e:
            # Check if it's a quota/rate limit error for silent handling
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                # Silent failover - no noisy error messages
                if not hasattr(self, '_quota_warning_shown'):
                    print("🔄 [yellow]Switching to backup LLM...[/yellow]")
                    self._quota_warning_shown = True
            else:
                print(f"⚠️ LLM error: {str(e)[:50]}...")
            
            # Try backup LLMs before fallback
            backup_result = self._try_backup_llms(user_input, turkish_classification_prompt)
            if backup_result:
                return backup_result
            return self._fallback_classification(user_input)
    
    def _try_backup_llms(self, user_input: str, prompt: str) -> dict:
        """Try backup LLMs when primary fails"""
        backup_llms = []
        
        # Try GPT-3.5-Turbo if available
        if ChatOpenAI and os.getenv("OPENAI_API_KEY") and not isinstance(self.llm, ChatOpenAI):
            try:
                backup_llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.1,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
                backup_llms.append(("GPT-3.5-Turbo", backup_llm))
            except:
                pass
        
        # Try Groq if available  
        if ChatGroq and os.getenv("GROQ_API_KEY") and not isinstance(self.llm, ChatGroq):
            try:
                backup_llm = ChatGroq(
                    model_name="llama-3.1-70b-versatile",
                    temperature=0.1
                )
                backup_llms.append(("Groq", backup_llm))
            except:
                pass
        
        # Try each backup LLM silently
        for llm_name, backup_llm in backup_llms:
            try:
                response = backup_llm.invoke([HumanMessage(content=prompt)])
                result = self._parse_json_safe(response.content)
                # Only show success message once per session
                if not hasattr(self, f'_{llm_name.lower()}_success_shown'):
                    print(f"✅ [green]{llm_name} backup activated[/green]")
                    setattr(self, f'_{llm_name.lower()}_success_shown', True)
                return result
            except Exception as e:
                # Silent failure - only log critical errors
                if "auth" in str(e).lower() or "key" in str(e).lower():
                    print(f"🔑 [red]{llm_name} authentication failed[/red]")
                continue
        
        return None
    
    def _fallback_classification(self, user_input: str) -> dict:
        """Simple keyword-based fallback classification"""
        text_lower = user_input.lower()
        
        # Chat patterns - but exclude if it's a file creation request
        chat_patterns = [
            'merhaba', 'selam', 'nasılsın', 'orda mısın', 'how are you', 'are you there',
            'neler yapabilir', 'ne yapabilir', 'hangi özelliklerin var', 'nasıl yardım',
            'ne için kullanılır', 'yeteneklerin', 'what can you do', 'what are your capabilities',
            'hangi dosya dizininda', 'hangi klasörde', 'nerede çalışıyorsun', 'nerede bulunuyorsun', 'where are you working',
            'sen kimsin', 'who are you', 'ne tür', 'what kind of'
        ]
        standalone_greetings = ['hello', 'hi', 'hey']
        
        # Check for standalone greetings only
        words = text_lower.split()
        if len(words) == 1 and words[0] in standalone_greetings:
            return {
                "intent": "CHAT",
                "confidence": 0.9,
                "entities": {},
                "requires_execution": False,
                "suggested_response_type": "chat_response"
            }
        
        # Check for other chat patterns (but not if it contains creation words)
        if any(pattern in text_lower for pattern in chat_patterns) and not any(word in text_lower for word in ['create', 'make', 'write', 'build']):
            return {
                "intent": "CHAT",
                "confidence": 0.9,
                "entities": {},
                "requires_execution": False,
                "suggested_response_type": "chat_response"
            }
        
        # Command patterns  
        if text_lower.startswith('run '):
            return {
                "intent": "SYSTEM_COMMAND", 
                "confidence": 0.8,
                "entities": {"command": user_input.replace('run ', '')},
                "requires_execution": True,
                "suggested_response_type": "command_execution"
            }
        elif text_lower.startswith('install ') or 'kütüphanesi kur' in text_lower or 'kütüphane kur' in text_lower:
            if 'kütüphanesi kur' in text_lower:
                package = text_lower.replace('kütüphanesi kur', '').strip()
            elif 'kütüphane kur' in text_lower:
                package = text_lower.replace('kütüphane kur', '').strip()
            else:
                package = text_lower.replace('install ', '').strip()
            return {
                "intent": "SYSTEM_COMMAND", 
                "confidence": 0.9,
                "entities": {"command": f"pip install {package}"},
                "requires_execution": True,
                "suggested_response_type": "command_execution"
            }
        elif any(cmd in text_lower for cmd in ['npm', 'pip', 'git']):
            return {
                "intent": "SYSTEM_COMMAND", 
                "confidence": 0.8,
                "entities": {"command": user_input},
                "requires_execution": True,
                "suggested_response_type": "command_execution"
            }
        
        # File operations - Turkish and English patterns
        turkish_file_patterns = ['oluştur', 'yaz', 'script', 'dosya oluştur', 'dosya yaz', 'python oluştur', 'merhaba dünya']
        english_file_patterns = ['create file', 'create a file', 'create python', 'create a python', 'write file', 'make file']
        
        if any(pattern in text_lower for pattern in turkish_file_patterns + english_file_patterns):
            return {
                "intent": "FILE_OPERATION",
                "confidence": 0.9,
                "entities": {},
                "requires_execution": True,
                "suggested_response_type": "file_operation"
            }
        elif any(word in text_lower for word in ['edit', 'read', 'delete']):
            return {
                "intent": "FILE_OPERATION",
                "confidence": 0.7,
                "entities": {},
                "requires_execution": True,
                "suggested_response_type": "file_operation"
            }
        
        # Default to system command
        return {
            "intent": "SYSTEM_COMMAND",
            "confidence": 0.6,
            "entities": {"command": user_input},
            "requires_execution": True,
            "suggested_response_type": "command_execution"
        }
    
    def _parse_json_safe(self, content: str) -> dict:
        """Safely parse JSON from LLM response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._fallback_classification("unknown")
        except Exception:
            return self._fallback_classification("unknown")

class ResponseRouter:
    """Route responses based on intent classification"""
    
    def __init__(self, llm=None, console=None):
        self.llm = llm
        self.console = console or Console()
        
    def route_response(self, intent_result: dict, user_input: str) -> dict:
        """Route response based on classified intent"""
        intent = intent_result.get('intent', 'SYSTEM_COMMAND')
        
        if intent == "CHAT":
            return self.handle_chat(user_input)
        elif intent == "SYSTEM_COMMAND":
            return self.handle_system_command(user_input, intent_result)
        elif intent == "FILE_OPERATION":
            return self.handle_file_operation(user_input, intent_result)
        elif intent == "CODE_GENERATION":
            return self.handle_code_generation(user_input, intent_result)
        elif intent == "PROJECT_MANAGEMENT":
            return self.handle_project_management(user_input, intent_result)
        else:
            return self.handle_explanation(user_input)
    
    def handle_chat(self, user_input: str) -> dict:
        """Handle casual conversation"""
        text_lower = user_input.lower()
        
        # Turkish responses
        if any(word in text_lower for word in ['merhaba', 'selam']):
            response = "💬 Merhaba! Terminal AI Agent'ına hoş geldin! Size nasıl yardımcı olabilirim?"
        elif any(word in text_lower for word in ['orda mısın', 'orada mısın']):
            response = "💬 Evet, buradayım! Terminal komutları çalıştırabilirim. Nasıl yardımcı olabilirim?"
        elif any(word in text_lower for word in ['nasılsın', 'naber']):
            response = "💬 İyiyim, teşekkürler! Terminal komutları çalıştırmaya hazırım. Sen nasılsın?"
        elif any(word in text_lower for word in ['teşekkür', 'sağol']):
            response = "💬 Rica ederim! Başka bir şeye ihtiyacın olursa söyle."
        elif any(word in text_lower for word in ['görüşürüz', 'hoşça kal']):
            response = "💬 Görüşürüz! İyi çalışmalar!"
        elif any(pattern in text_lower for pattern in ['neler yapabilir', 'ne yapabilir', 'hangi özellik']):
            response = """💬 Ben bir Terminal AI Agent'ıyım! Şunları yapabilirim:
• 🤖 Doğal dil ile terminal komutları çalıştırma
• 📁 Dosya oluşturma, düzenleme ve okuma
• 📦 Paket kurulumu (pip, npm vs.)
• 🐍 Python kodu yazma ve çalıştırma
• 💬 Türkçe ve İngilizce sohbet
• 🔧 Hata analizi ve öneriler"""
        elif any(pattern in text_lower for pattern in ['hangi dosya', 'hangi klasör', 'nerede çalışıyorsun', 'nerede bulunuyorsun', 'dizin']):
            response = f"💬 Ben şu anda şu dizinde çalışıyorum: `{os.getcwd()}`"
        elif any(pattern in text_lower for pattern in ['sen kimsin', 'ne tür']):
            response = "💬 Ben Terminal AI Agent'ıyım! Claude Code benzeri yeteneklerle terminal komutları çalıştırabilen bir yapay zeka asistanıyım."
        
        # English responses
        elif any(word in text_lower for word in ['hello', 'hi', 'hey']):
            response = "💬 Hello! Welcome to Terminal AI Agent! How can I help you?"
        elif 'are you there' in text_lower:
            response = "💬 Yes, I'm here! Ready to execute terminal commands. What do you need?"
        elif 'how are you' in text_lower:
            response = "💬 I'm doing great! Ready to help with terminal tasks. How are you?"
        elif any(word in text_lower for word in ['thank you', 'thanks']):
            response = "💬 You're welcome! Let me know if you need anything else."
        elif any(word in text_lower for word in ['bye', 'goodbye']):
            response = "💬 Goodbye! Have a great day!"
        else:
            response = "💬 İlginç! Ben terminal komutları çalıştırabilen bir AI asistanıyım. 'help' yazarak özelliklerimi görebilirsin."
        
        return {"type": "chat", "response": response, "execute": False}
    
    def handle_system_command(self, user_input: str, intent_result: dict) -> dict:
        """Handle system commands"""
        command = intent_result.get('entities', {}).get('command', user_input)
        
        # Clean up command
        if user_input.lower().startswith('run '):
            command = user_input[4:].strip()
        elif 'kütüphanesi kur' in user_input.lower():
            package = user_input.lower().replace('kütüphanesi kur', '').strip()
            command = f"pip install {package}"
        elif 'kütüphane kur' in user_input.lower():
            package = user_input.lower().replace('kütüphane kur', '').strip()
            command = f"pip install {package}"
        
        return {
            "type": "command",
            "commands": [command],
            "description": f"Execute: {command}",
            "execute": True
        }
    
    def handle_file_operation(self, user_input: str, intent_result: dict) -> dict:
        """Handle file operations with self-testing"""
        # Simple file operation handling
        text_lower = user_input.lower()
        
        if 'create' in text_lower and 'file' in text_lower:
            filename = self._extract_filename(user_input)
            return {
                "type": "command",
                "commands": [f"touch {filename}"],
                "description": f"Create file: {filename}",
                "execute": True
            }
        elif ('create' in text_lower or 'oluştur' in text_lower) and ('python' in text_lower or '.py' in text_lower or 'merhaba dünya' in text_lower):
            if 'merhaba dünya' in text_lower:
                filename = "merhaba_dunya.py"
                content = 'print("Merhaba, Dünya!")'
            elif 'broken' in text_lower:  # Test case for syntax error
                filename = "broken_test.py"
                content = 'print("Hello World"'  # Missing closing parenthesis
            else:
                filename = "hello_world.py"
                content = 'print("Hello, World!")'
            
            # Create commands with self-testing
            commands = [
                f"echo '{content}' > {filename}",
                f"python -m py_compile {filename}",  # Syntax check
                f"python {filename}"  # Test execution
            ]
            
            return {
                "type": "self_tested_command", 
                "commands": commands,
                "filename": filename,
                "content": content,
                "description": f"Create and test Python file: {filename}",
                "execute": True
            }
        else:
            return self.handle_system_command(user_input, intent_result)
    
    def handle_code_generation(self, user_input: str, intent_result: dict) -> dict:
        """Handle code generation requests"""
        # For now, delegate to file operations
        return self.handle_file_operation(user_input, intent_result)
    
    def handle_project_management(self, user_input: str, intent_result: dict) -> dict:
        """Handle multi-step project tasks"""
        text_lower = user_input.lower()
        
        if 'flask app' in text_lower:
            return {
                "type": "multi_command",
                "commands": [
                    "mkdir flask_app && cd flask_app",
                    "python -m venv venv",
                    "pip install flask",
                    "echo 'from flask import Flask\\napp = Flask(__name__)\\n\\n@app.route(\"/\")\\ndef hello():\\n    return \"Hello, World!\"\\n\\nif __name__ == \"__main__\":\\n    app.run(debug=True)' > app.py"
                ],
                "description": "Create Flask application",
                "execute": True
            }
        else:
            return self.handle_system_command(user_input, intent_result)
    
    def handle_explanation(self, user_input: str) -> dict:
        """Handle explanation requests"""
        return {
            "type": "chat",
            "response": f"💬 Bu konuda size yardımcı olmaya çalışayım. '{user_input}' hakkında daha spesifik bir soru sorabilir misiniz?",
            "execute": False
        }
    
    def _extract_filename(self, text: str) -> str:
        """Extract filename from user input"""
        words = text.split()
        for i, word in enumerate(words):
            if word == "file" and i + 1 < len(words):
                return words[i + 1]
        return "new_file.txt"

@dataclass
class ConversationEntry:
    timestamp: datetime
    user_input: str
    agent_response: str
    task_steps: List[TaskStep]
    success: bool = True

class CommandExecutor:
    def __init__(self, console: Console):
        self.console = console
        self.working_directory = os.getcwd()
        
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Execute a command safely and return success, stdout, stderr"""
        try:
            # Security check for dangerous commands
            dangerous_patterns = [
                r'rm\s+-rf\s+/',
                r'sudo\s+rm',
                r'>\s*/dev/',
                r'dd\s+if=',
                r'mkfs\.',
                r'fdisk',
                r'format'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, "", f"Dangerous command blocked: {command}"
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_directory
            )
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Execution error: {str(e)}"
    
    def change_directory(self, path: str) -> bool:
        """Change working directory"""
        try:
            os.chdir(path)
            self.working_directory = os.getcwd()
            return True
        except Exception:
            return False

class ErrorHandler:
    def __init__(self, console: Console):
        self.console = console
        
    def analyze_error(self, command: str, stderr: str) -> List[str]:
        """Analyze error and suggest fixes"""
        suggestions = []
        
        # Common error patterns and fixes
        error_fixes = {
            "command not found": ["Check if the command is installed", "Try: which {command}"],
            "permission denied": ["Try with sudo", "Check file permissions"],
            "no such file or directory": ["Check if path exists", "Use absolute path"],
            "port already in use": ["Kill process using port", "Use different port"],
            "connection refused": ["Check if service is running", "Verify network connectivity"],
            "python: can't open file": ["Check Python file path", "Verify file exists"],
            "npm: command not found": ["Install Node.js and npm", "Check PATH environment"],
            "pip: command not found": ["Install Python pip", "Use python -m pip instead"],
        }
        
        stderr_lower = stderr.lower()
        for error_pattern, fixes in error_fixes.items():
            if error_pattern in stderr_lower:
                suggestions.extend(fixes)
        
        return suggestions if suggestions else ["Check command syntax", "Verify prerequisites"]

class TaskPlanner:
    def __init__(self, console: Console):
        self.console = console
        
    def decompose_task(self, user_input: str) -> List[TaskStep]:
        """Decompose user request into executable steps"""
        steps = []
        
        # Check if this is a chat/conversation (not a command)
        if self._is_chat_message(user_input):
            return []  # Return empty steps for chat messages
        
        # Simple pattern matching for common tasks
        if "create flask app" in user_input.lower():
            steps = [
                TaskStep("1", "Create project directory", "mkdir flask_app && cd flask_app"),
                TaskStep("2", "Create virtual environment", "python -m venv venv"),
                TaskStep("3", "Activate virtual environment", "source venv/bin/activate || venv\\Scripts\\activate"),
                TaskStep("4", "Install Flask", "pip install flask flask-login"),
                TaskStep("5", "Create app.py", None),  # Will be handled by file operations
                TaskStep("6", "Create templates directory", "mkdir templates static"),
                TaskStep("7", "Test application", "python app.py")
            ]
        elif "install" in user_input.lower():
            package = user_input.lower().replace("install", "").strip()
            steps = [
                TaskStep("1", f"Install {package}", f"pip install {package}")
            ]
        elif "create" in user_input.lower() and "file" in user_input.lower():
            filename = self._extract_filename(user_input)
            steps = [
                TaskStep("1", f"Create file {filename}", f"touch {filename}")
            ]
        elif "run" in user_input.lower():
            command = user_input.replace("run", "").strip()
            steps = [
                TaskStep("1", f"Execute: {command}", command)
            ]
        else:
            # Generic task - try to execute as command
            steps = [
                TaskStep("1", "Execute command", user_input)
            ]
        
        return steps
    
    def _is_chat_message(self, text: str) -> bool:
        """Check if input is a chat message rather than a command"""
        text_lower = text.lower()
        
        # Skip if it's a command (starts with "run")
        if text_lower.startswith('run '):
            return False
        
        # Common greetings and chat patterns (Turkish and English)
        chat_patterns = [
            'merhaba', 'selam',
            'nasılsın', 'how are you', 'naber', 'ne var ne yok',
            'orda mısın', 'are you there', 'orada mısın',
            'yardım', 'help me', 'bana yardım et',
            'teşekkür', 'thank you', 'thanks', 'sağol',
            'görüşürüz', 'bye', 'goodbye', 'hoşça kal'
        ]
        
        # Standalone greetings only (not in commands)
        standalone_greetings = ['hello', 'hi', 'hey']
        words = text_lower.split()
        if len(words) == 1 and words[0] in standalone_greetings:
            return True
        
        # Check for chat patterns
        for pattern in chat_patterns:
            if pattern in text_lower:
                return True
        
        # Check for question words that typically indicate conversation
        question_words = ['ne', 'nasıl', 'neden', 'kim', 'what', 'how', 'why', 'who', 'when', 'where']
        if len(words) > 0 and words[0] in question_words:
            return True
            
        return False
    
    def _extract_filename(self, text: str) -> str:
        """Extract filename from user input"""
        words = text.split()
        for i, word in enumerate(words):
            if word == "file" and i + 1 < len(words):
                return words[i + 1]
        return "new_file.txt"

class MemorySystem:
    def __init__(self):
        self.conversation_history: List[ConversationEntry] = []
        self.task_history: List[TaskStep] = []
        self.session_file = "terminal_agent_session.json"
        
    def add_conversation(self, entry: ConversationEntry):
        """Add conversation entry to memory"""
        self.conversation_history.append(entry)
        self.task_history.extend(entry.task_steps)
        
    def save_session(self):
        """Save session to file"""
        try:
            data = {
                "conversations": [
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "user_input": entry.user_input,
                        "agent_response": entry.agent_response,
                        "task_steps": [asdict(step) for step in entry.task_steps],
                        "success": entry.success
                    }
                    for entry in self.conversation_history
                ]
            }
            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Silent fail for session saving
    
    def load_session(self):
        """Load previous session"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    # Could implement session loading logic here
        except Exception:
            pass  # Silent fail for session loading

class TerminalAgent:
    def __init__(self):
        self.console = Console()
        self.executor = CommandExecutor(self.console)
        self.error_handler = ErrorHandler(self.console)
        self.planner = TaskPlanner(self.console)  # Keep for compatibility
        self.memory = MemorySystem()
        
        # New LLM-based components  
        self.llm = None
        if LANGCHAIN_AVAILABLE:
            # Use the same intelligent LLM selection as AdvancedIntentClassifier
            self.llm = self._initialize_best_available_llm()
        
        # Initialize components after LLM is ready
        self._init_components()
    
    def _initialize_best_available_llm(self):
        """Initialize the best available LLM with quota checking (same as AdvancedIntentClassifier)"""
        
        # 1. Try Gemini first (best Turkish support) with quota check
        if ChatGoogleGenerativeAI and os.getenv("GOOGLE_API_KEY"):
            try:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.1,
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    max_retries=0  # Disable LangChain's own retries for clean error handling
                )
                # Quick test to check if Gemini is working
                test_response = llm.invoke([HumanMessage(content="test")])
                self.console.print("[green]🤖 Gemini 1.5 Flash ready (Turkish optimized)[/green]")
                return llm
            except Exception as e:
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    self.console.print("[yellow]🔄 Gemini quota exceeded, using backup LLM[/yellow]")
                else:
                    self.console.print(f"[yellow]⚠️ Gemini unavailable, trying alternatives[/yellow]")
        
        # 2. Try GPT-3.5-Turbo backup (good Turkish support)
        if ChatOpenAI and os.getenv("OPENAI_API_KEY"):
            try:
                llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.1,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
                self.console.print("[cyan]🧠 GPT-3.5-Turbo ready (good Turkish support)[/cyan]")
                return llm
            except Exception as e:
                self.console.print(f"[yellow]⚠️ GPT-3.5-Turbo unavailable[/yellow]")
        
        # 3. Fallback to Groq (fast but limited Turkish)
        if ChatGroq and os.getenv("GROQ_API_KEY"):
            try:
                llm = ChatGroq(
                    model_name="llama-3.1-70b-versatile",
                    temperature=0.1
                )
                self.console.print("[magenta]⚡ Groq Llama ready (limited Turkish)[/magenta]")
                return llm
            except Exception as e:
                self.console.print(f"[yellow]⚠️ Groq unavailable[/yellow]")
        
        self.console.print("[red]❌ No LLM available - using pattern-based fallback only[/red]")
        return None
    
    def _init_components(self):
        """Initialize agent components after LLM is ready"""
        self.intent_classifier = AdvancedIntentClassifier(self.llm)
        self.response_router = ResponseRouter(self.llm, self.console)
        self.conversation_history = []
        
        # Load previous session
        self.memory.load_session()
        
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = """
# 🤖 Terminal AI Agent

Professional terminal assistant with real command execution capabilities.
Similar to Claude Code, but running locally!

**Features:**
- Natural language → Terminal commands
- Multi-step task decomposition  
- Real-time command execution
- Error detection and self-correction
- File operations and code generation
- Session memory and history

**Commands:**
- Type your request in natural language
- `help` - Show help information
- `history` - Show conversation history
- `clear` - Clear screen
- `exit` - Exit the agent

**Examples:**
- "Create a Flask app with user authentication"
- "Install pandas and create a data analysis script"
- "Set up a React project with TypeScript"
- "Show me the contents of config.py"
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="🚀 Terminal Agent Ready",
            border_style="blue"
        ))
    
    def process_request(self, user_input: str) -> str:
        """Process user request using advanced intent classification"""
        start_time = datetime.now()
        
        # Handle special commands
        if user_input.lower() in ['exit', 'quit']:
            return "exit"
        elif user_input.lower() == 'help':
            return self._show_help()
        elif user_input.lower() == 'history':
            return self._show_history()
        elif user_input.lower() == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            return ""
        
        # Step 1: Classify intent using LLM
        self.console.print(f"\n🧠 [bold blue]Analyzing intent:[/bold blue] {user_input}")
        intent_result = self.intent_classifier.classify_intent(user_input, self.conversation_history)
        
        # Show intent classification
        intent = intent_result.get('intent', 'UNKNOWN')
        confidence = intent_result.get('confidence', 0.0)
        self.console.print(f"🎯 [yellow]Intent:[/yellow] {intent} ([green]{confidence:.2f}[/green] confidence)")
        
        # Step 2: Route response based on intent
        if confidence < 0.5:  # Lowered threshold from 0.7
            self.console.print("❓ [red]Intent unclear, using fallback handling...[/red]")
        
        response = self.response_router.route_response(intent_result, user_input)
        
        # Step 3: Execute response
        result = self._execute_response(response, intent_result)
        
        # Step 4: Update conversation history
        self.conversation_history.append({
            "user": user_input,
            "intent": intent_result,
            "response": response,
            "timestamp": start_time
        })
        
        return result
    
    def _execute_response(self, response: dict, intent_result: dict) -> str:
        """Execute the routed response"""
        response_type = response.get("type", "command")
        
        if response_type == "chat":
            # Display chat response
            self.console.print(response["response"])
            return "Chat response provided"
            
        elif response_type in ["command", "multi_command"]:
            # Execute commands
            commands = response.get("commands", [])
            description = response.get("description", "Executing commands")
            
            self.console.print(f"\n📋 [blue]{description}[/blue]")
            
            success_count = 0
            for cmd in commands:
                self.console.print(f"⚡ [cyan]Running:[/cyan] {cmd}")
                
                success, stdout, stderr = self.executor.execute_command(cmd)
                
                if success:
                    self.console.print(f"✅ [green]Success[/green]")
                    if stdout.strip():
                        self.console.print(f"   Output: {stdout.strip()}")
                    success_count += 1
                else:
                    self.console.print(f"❌ [red]Error:[/red] {stderr}")
                    # Try to provide suggestions
                    self._handle_command_error(cmd, stderr)
            
            if success_count == len(commands):
                return "✅ Task completed successfully!"
            else:
                return f"⚠️ Task partially completed ({success_count}/{len(commands)} commands succeeded)"
        
        elif response_type == "self_tested_command":
            # Execute commands with self-correction
            return self._execute_self_tested_commands(response)
        
        else:
            return "❌ Unknown response type"
    
    def _execute_self_tested_commands(self, response: dict) -> str:
        """Execute commands with self-testing and error correction"""
        filename = response.get("filename", "unknown.py")
        content = response.get("content", "")
        commands = response.get("commands", [])
        description = response.get("description", "Creating and testing file")
        
        self.console.print(f"\n📋 [blue]{description}[/blue]")
        
        # Step 1: Create file
        create_cmd = commands[0]
        self.console.print(f"📝 [cyan]Creating file:[/cyan] {create_cmd}")
        success, stdout, stderr = self.executor.execute_command(create_cmd)
        
        if not success:
            self.console.print(f"❌ [red]File creation failed:[/red] {stderr}")
            return "❌ Failed to create file"
        
        self.console.print(f"✅ [green]File created successfully[/green]")
        
        # Step 2: Syntax check
        if len(commands) > 1:
            syntax_cmd = commands[1]
            self.console.print(f"🔍 [cyan]Checking syntax:[/cyan] {syntax_cmd}")
            success, stdout, stderr = self.executor.execute_command(syntax_cmd)
            
            if not success:
                self.console.print(f"❌ [red]Syntax error detected:[/red] {stderr}")
                # Try to fix the syntax error
                return self._attempt_syntax_fix(filename, content, stderr)
            
            self.console.print(f"✅ [green]Syntax check passed[/green]")
        
        # Step 3: Test execution
        if len(commands) > 2:
            test_cmd = commands[2]
            self.console.print(f"🚀 [cyan]Testing execution:[/cyan] {test_cmd}")
            success, stdout, stderr = self.executor.execute_command(test_cmd)
            
            if not success:
                self.console.print(f"❌ [red]Execution failed:[/red] {stderr}")
                return f"⚠️ File created but execution failed: {stderr}"
            
            self.console.print(f"✅ [green]Execution successful![/green]")
            if stdout.strip():
                self.console.print(f"📤 [green]Output:[/green] {stdout.strip()}")
        
        return "✅ File created, tested, and verified successfully!"
    
    def _attempt_syntax_fix(self, filename: str, original_content: str, error_message: str) -> str:
        """Attempt to fix syntax errors using LLM"""
        self.console.print("🔧 [yellow]Attempting to fix syntax error...[/yellow]")
        
        if self.llm:
            try:
                fix_prompt = f"""
                The following Python code has a syntax error:
                
                File: {filename}
                Code: {original_content}
                Error: {error_message}
                
                Please provide the corrected Python code. Return ONLY the fixed code, nothing else:
                """
                
                response = self.llm.invoke([HumanMessage(content=fix_prompt)])
                fixed_content = response.content.strip()
                
                # Remove code block markers if present
                if fixed_content.startswith('```python'):
                    fixed_content = fixed_content[9:]
                if fixed_content.startswith('```'):
                    fixed_content = fixed_content[3:]
                if fixed_content.endswith('```'):
                    fixed_content = fixed_content[:-3]
                
                fixed_content = fixed_content.strip()
                
                # Write fixed content
                fix_cmd = f"echo '{fixed_content}' > {filename}"
                self.console.print(f"🔧 [cyan]Applying fix:[/cyan] {fix_cmd}")
                success, stdout, stderr = self.executor.execute_command(fix_cmd)
                
                if success:
                    # Test the fix
                    test_success, test_out, test_err = self.executor.execute_command(f"python {filename}")
                    if test_success:
                        self.console.print(f"✅ [green]Fix successful![/green]")
                        if test_out.strip():
                            self.console.print(f"📤 [green]Output:[/green] {test_out.strip()}")
                        return "✅ Syntax error fixed automatically!"
                    else:
                        self.console.print(f"❌ [red]Fix failed, still has errors:[/red] {test_err}")
                        return f"⚠️ Attempted fix but still has errors: {test_err}"
                else:
                    return f"❌ Failed to apply fix: {stderr}"
                    
            except Exception as e:
                self.console.print(f"❌ [red]Auto-fix failed:[/red] {e}")
        
        return f"❌ Syntax error could not be fixed automatically: {error_message}"
    
    def _handle_command_error(self, failed_command: str, error_message: str):
        """Provide suggestions for failed commands"""
        # Basic error suggestions
        basic_suggestions = []
        
        if "command not found" in error_message.lower():
            basic_suggestions.append("Check if the command is installed")
            basic_suggestions.append("Try using the full path to the command")
        elif "permission denied" in error_message.lower():
            basic_suggestions.append("Try running with sudo")
            basic_suggestions.append("Check file permissions")
        elif "no such file" in error_message.lower():
            basic_suggestions.append("Check if the file path is correct")
            basic_suggestions.append("Verify the file exists")
            
        if basic_suggestions:
            self.console.print(f"💡 [yellow]Suggestions:[/yellow]")
            for suggestion in basic_suggestions:
                self.console.print(f"   • {suggestion}")
        
        # Also try LLM-based error analysis if available
        if self.llm:
            try:
                recovery_prompt = f"""
                Command failed. Provide 2-3 specific suggestions to fix this error.
                
                Failed command: {failed_command}
                Error: {error_message}
                
                Respond with practical suggestions only, one per line:
                """
                
                response = self.llm.invoke([HumanMessage(content=recovery_prompt)])
                self.console.print(f"🤖 [blue]AI Suggestions:[/blue]")
                for line in response.content.strip().split('\n'):
                    if line.strip():
                        self.console.print(f"   • {line.strip()}")
            except Exception:
                pass  # Silent fail for LLM suggestions
    
    def _display_plan(self, steps: List[TaskStep]):
        """Display execution plan"""
        self.console.print("\n📋 [bold green]Execution Plan:[/bold green]")
        for i, step in enumerate(steps, 1):
            self.console.print(f"   Step {i}: {step.description}")
        self.console.print()
    
    def _execute_steps(self, steps: List[TaskStep]) -> bool:
        """Execute all task steps"""
        all_success = True
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            for step in steps:
                task = progress.add_task(f"Executing: {step.description}", total=1)
                step.status = "running"
                step.timestamp = datetime.now()
                
                if step.command:
                    success, stdout, stderr = self.executor.execute_command(step.command)
                    step.output = stdout
                    step.error = stderr
                    
                    if success:
                        step.status = "completed"
                        if stdout.strip():
                            self.console.print(f"✅ [green]{step.description}[/green]")
                            if len(stdout) < 500:  # Show output if not too long
                                self.console.print(f"   Output: {stdout.strip()}")
                    else:
                        step.status = "failed"
                        all_success = False
                        self.console.print(f"❌ [red]{step.description}[/red]")
                        self.console.print(f"   Error: {stderr.strip()}")
                        
                        # Try to suggest fixes
                        suggestions = self.error_handler.analyze_error(step.command, stderr)
                        if suggestions:
                            self.console.print("💡 [yellow]Suggestions:[/yellow]")
                            for suggestion in suggestions:
                                self.console.print(f"   • {suggestion}")
                else:
                    # Handle special operations (like file creation)
                    success = self._handle_special_operation(step)
                    step.status = "completed" if success else "failed"
                    all_success = all_success and success
                
                progress.update(task, completed=1)
                time.sleep(0.1)  # Small delay for visual effect
        
        return all_success
    
    def _handle_special_operation(self, step: TaskStep) -> bool:
        """Handle special operations like file creation"""
        if "Create app.py" in step.description:
            flask_code = '''from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple User class (in production, use a database)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Mock user database
users = {'admin': {'password': 'password'}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
'''
            try:
                with open('app.py', 'w') as f:
                    f.write(flask_code)
                step.output = "Flask app created successfully"
                return True
            except Exception as e:
                step.error = str(e)
                return False
        
        return True
    
    def _handle_chat(self, user_input: str) -> str:
        """Handle chat/conversation messages"""
        text_lower = user_input.lower()
        
        # Turkish responses
        if any(word in text_lower for word in ['merhaba', 'selam']):
            self.console.print("💬 [bold green]Merhaba![/bold green] Terminal AI Agent'ına hoş geldin! Size nasıl yardımcı olabilirim?")
            return "Konuşma için teşekkürler!"
        elif any(word in text_lower for word in ['orda mısın', 'orada mısın']):
            self.console.print("💬 [bold green]Evet, buradayım![/bold green] Terminal komutları çalıştırabilirim. Nasıl yardımcı olabilirim?")
            return "Evet, aktifim!"
        elif any(word in text_lower for word in ['nasılsın', 'naber']):
            self.console.print("💬 [bold green]İyiyim, teşekkürler![/bold green] Terminal komutları çalıştırmaya hazırım. Sen nasılsın?")
            return "İyi gidiyor!"
        elif any(word in text_lower for word in ['teşekkür', 'sağol']):
            self.console.print("💬 [bold green]Rica ederim![/bold green] Başka bir şeye ihtiyacın olursa söyle.")
            return "Bir şey değil!"
        elif any(word in text_lower for word in ['görüşürüz', 'hoşça kal']):
            self.console.print("💬 [bold green]Görüşürüz![/bold green] İyi çalışmalar!")
            return "Hoşça kal!"
        
        # English responses
        elif any(word in text_lower for word in ['hello', 'hi', 'hey']):
            self.console.print("💬 [bold green]Hello![/bold green] Welcome to Terminal AI Agent! How can I help you?")
            return "Hello there!"
        elif 'are you there' in text_lower:
            self.console.print("💬 [bold green]Yes, I'm here![/bold green] Ready to execute terminal commands. What do you need?")
            return "Yes, I'm active!"
        elif 'how are you' in text_lower:
            self.console.print("💬 [bold green]I'm doing great![/bold green] Ready to help with terminal tasks. How are you?")
            return "Doing well!"
        elif any(word in text_lower for word in ['thank you', 'thanks']):
            self.console.print("💬 [bold green]You're welcome![/bold green] Let me know if you need anything else.")
            return "You're welcome!"
        elif any(word in text_lower for word in ['bye', 'goodbye']):
            self.console.print("💬 [bold green]Goodbye![/bold green] Have a great day!")
            return "Goodbye!"
        
        # Default response for other chat messages
        else:
            self.console.print("💬 [bold green]İlginç![/bold green] Ben terminal komutları çalıştırabilen bir AI asistanıyım. 'help' yazarak özelliklerimi görebilirsin.")
            return "Anlıyorum, başka nasıl yardımcı olabilirim?"
    
    def _show_help(self) -> str:
        """Show help information"""
        help_text = """
**Terminal AI Agent Help**

The agent understands natural language commands and converts them to terminal operations.

**Example Commands:**
- "Create a Python script that prints hello world"
- "Install numpy and create a data analysis template"
- "Set up a Node.js project with Express"
- "Show me the contents of package.json"
- "Create a directory called 'my_project'"
- "Run pytest on the test files"

**Special Commands:**
- `help` - Show this help
- `history` - Show conversation history  
- `clear` - Clear the screen
- `exit` - Exit the agent

**Features:**
- Multi-step task planning
- Real command execution
- Error analysis and suggestions
- File operations
- Session memory
        """
        self.console.print(Panel(help_text, title="📚 Help", border_style="green"))
        return ""
    
    def _show_history(self) -> str:
        """Show conversation history"""
        if not self.memory.conversation_history:
            self.console.print("📝 No conversation history yet.")
            return ""
        
        table = Table(title="📜 Conversation History")
        table.add_column("Time", style="cyan")
        table.add_column("Request", style="white")
        table.add_column("Status", style="green")
        table.add_column("Steps", justify="center")
        
        for entry in self.memory.conversation_history[-10:]:  # Last 10 entries
            status = "✅" if entry.success else "❌"
            steps_count = str(len(entry.task_steps))
            time_str = entry.timestamp.strftime("%H:%M:%S")
            
            # Truncate long requests
            request = entry.user_input[:50] + "..." if len(entry.user_input) > 50 else entry.user_input
            
            table.add_row(time_str, request, status, steps_count)
        
        self.console.print(table)
        return ""
    
    def run(self):
        """Main run loop"""
        self.display_welcome()
        
        try:
            while True:
                user_input = Prompt.ask("\n🤖 [bold cyan]Agent[/bold cyan]")
                
                if not user_input.strip():
                    continue
                
                result = self.process_request(user_input)
                
                if result == "exit":
                    self.console.print("\n👋 [bold blue]Goodbye! Session saved.[/bold blue]")
                    break
                elif result:
                    self.console.print(f"\n{result}")
                    
        except KeyboardInterrupt:
            self.console.print("\n\n👋 [bold blue]Goodbye! Session saved.[/bold blue]")
        except Exception as e:
            self.console.print(f"\n❌ [bold red]Fatal error:[/bold red] {str(e)}")
            traceback.print_exc()
        finally:
            self.memory.save_session()

if __name__ == "__main__":
    agent = TerminalAgent()
    agent.run()