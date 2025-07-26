#!/usr/bin/env python3
"""
🧠 ATOLYE SEFI - LANGCHAIN REACT AGENT
Professional ReAct Agent migration from custom GraphAgent
Maintains Modal.com integration + performance optimizations
"""

import sys
import os
import re
import time
from typing import Dict, List, Any, Optional, Union

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# LangChain imports
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool, BaseTool
from langchain_groq import ChatGroq
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage

# Project imports
from config import settings
from tools.modal_executor import execute_code_locally, execute_bash_locally

class PerformanceCallbackHandler(BaseCallbackHandler):
    """Performance monitoring for agent execution"""
    
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.llm_calls = 0
        self.tool_calls = 0
        
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
        self.start_time = time.time()
        print(f"🚀 [REACT AGENT] Starting: {inputs.get('input', '')[:50]}...")
        
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        if self.start_time:
            duration = time.time() - self.start_time
            print(f"⚡ [PERFORMANCE] Total time: {duration:.2f}s | LLM calls: {self.llm_calls} | Tool calls: {self.tool_calls}")
            
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        self.llm_calls += 1
        
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        self.tool_calls += 1
        tool_name = serialized.get('name', 'unknown')
        print(f"🔧 [TOOL] {tool_name}: {input_str[:50]}...")

class ModalExecutorTool(BaseTool):
    """Enhanced Modal.com code execution tool"""
    
    name: str = "modal_python_executor"
    description: str = """
    Execute Python code via Modal.com serverless functions.
    Use for: Python scripts, calculations, data processing, ML workflows.
    Input: Python code as string
    Returns: Execution output with status
    
    Examples:
    - print('Hello World')
    - import pandas as pd; df = pd.DataFrame({'A': [1,2,3]}); print(df)
    - import torch; print(torch.cuda.is_available())
    """
    
    def _run(self, code: str) -> Dict[str, Any]:
        """Execute Python code"""
        try:
            print(f"🐍 [MODAL PYTHON] Executing: {code[:100]}...")
            
            # Detect GPU requirement
            gpu_keywords = ["torch", "tensorflow", "cuda", "gpu", "model", "train", "ml", "neural"]
            use_gpu = any(keyword in code.lower() for keyword in gpu_keywords)
            
            if use_gpu:
                print("🔥 GPU workload detected")
            
            result = execute_code_locally(code, use_gpu=use_gpu)
            
            if result["status"] == "success":
                output = result.get("output", "").strip()
                error = result.get("error", "").strip()
                
                # Format response
                if output and error:
                    return f"✅ SUCCESS\nOutput: {output}\nWarnings: {error}"
                elif output:
                    return f"✅ SUCCESS\nOutput: {output}"
                elif error:
                    return f"✅ SUCCESS (no output)\nWarnings: {error}"
                else:
                    return "✅ SUCCESS (executed without output)"
            else:
                error_msg = result.get("error", "Unknown error")
                return f"❌ ERROR\n{error_msg}"
                
        except Exception as e:
            return f"❌ EXECUTION ERROR\n{str(e)}"

class ModalBashTool(BaseTool):
    """Enhanced Modal.com bash execution tool"""
    
    name: str = "modal_bash_executor"
    description: str = """
    Execute bash/shell commands via Modal.com.
    Use for: File operations, system commands, package installation, git operations.
    Input: Bash command as string
    Returns: Command output with status
    
    Examples:
    - ls -la
    - pip install pandas
    - git clone https://github.com/user/repo
    - cat file.txt
    """
    
    def _run(self, command: str) -> Dict[str, Any]:
        """Execute bash command"""
        try:
            print(f"🔧 [MODAL BASH] Executing: {command}")
            
            result = execute_bash_locally(command)
            
            if result["status"] == "success":
                output = result.get("output", "").strip()
                error = result.get("error", "").strip()
                
                if output and error:
                    return f"✅ SUCCESS\nOutput: {output}\nWarnings: {error}"
                elif output:
                    return f"✅ SUCCESS\nOutput: {output}"
                elif error:
                    return f"✅ SUCCESS (no output)\nWarnings: {error}"
                else:
                    return "✅ SUCCESS (command executed)"
            else:
                error_msg = result.get("error", "Unknown error")
                return f"❌ ERROR\n{error_msg}"
                
        except Exception as e:
            return f"❌ EXECUTION ERROR\n{str(e)}"

class CodeAnalyzerTool(BaseTool):
    """Smart code analysis and auto-fixing tool"""
    
    name: str = "code_analyzer"
    description: str = """
    Analyze code requirements and suggest optimal execution strategy.
    Use for: Complex requests, multi-step tasks, code optimization.
    Input: Task description or code to analyze
    Returns: Analysis and recommended approach
    """
    
    def _run(self, task: str) -> str:
        """Analyze task and suggest approach"""
        try:
            task_lower = task.lower().strip()
            
            # Simple task detection
            simple_patterns = {
                "hello world": "Simple print statement detected. Use: print('Hello World!')",
                "calculate": "Simple calculation detected. Use basic arithmetic operations.",
                "time": "Time query detected. Use: import datetime; print(datetime.datetime.now())",
                "version": "Version check detected. Use: import sys; print(sys.version)"
            }
            
            for pattern, suggestion in simple_patterns.items():
                if pattern in task_lower:
                    return f"📋 ANALYSIS: {suggestion}"
            
            # Complex task detection
            if any(keyword in task_lower for keyword in ["calculator", "app", "program", "script"]):
                return "📋 ANALYSIS: Complex application detected. Recommend multi-step approach with functions and user interaction."
            
            if any(keyword in task_lower for keyword in ["file", "create", "write", "save"]):
                return "📋 ANALYSIS: File operation detected. Use file I/O operations with proper error handling."
            
            if any(keyword in task_lower for keyword in ["install", "pip", "package"]):
                return "📋 ANALYSIS: Package installation detected. Use bash command: pip install <package>"
            
            if any(keyword in task_lower for keyword in ["torch", "tensorflow", "ml", "model", "gpu"]):
                return "📋 ANALYSIS: ML/AI workload detected. GPU execution recommended for optimal performance."
            
            return "📋 ANALYSIS: General task detected. Recommend Python execution with appropriate libraries."
            
        except Exception as e:
            return f"❌ ANALYSIS ERROR: {str(e)}"

class ReactAgent:
    """
    Professional LangChain ReAct Agent for Atölye Şefi
    Replaces custom GraphAgent with industry-standard ReAct pattern
    """
    
    def __init__(self):
        """Initialize ReAct Agent with Modal.com integration"""
        print("🧠 [REACT AGENT] Initializing professional ReAct system...")
        
        # Initialize LLM with Groq
        self.llm = ChatGroq(
            model_name=settings.AGENT_MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.1,  # Balanced creativity/consistency
            max_tokens=4000,  # Adequate for complex reasoning
            verbose=True
        )
        
        # Initialize tools
        self.tools = [
            ModalExecutorTool(),
            ModalBashTool(),
            CodeAnalyzerTool()
        ]
        
        # Create ReAct prompt
        self.prompt = self._create_react_prompt()
        
        # Create ReAct agent (positional arguments)
        self.agent = create_react_agent(
            self.llm,
            self.tools, 
            self.prompt
        )
        
        # Create agent executor with performance monitoring
        self.callback_handler = PerformanceCallbackHandler()
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            callbacks=[self.callback_handler],
            max_iterations=10,
            max_execution_time=300,  # 5 minutes timeout
            handle_parsing_errors=True,
            early_stopping_method="generate"
        )
        
        print("✅ [REACT AGENT] Initialization complete - Ready for professional code execution!")
    
    def _create_react_prompt(self) -> PromptTemplate:
        """Create optimized ReAct prompt for code execution tasks"""
        
        template = """🧠 **ATÖLYE ŞEFİ - PROFESSIONAL REACT AGENT**

You are Atölye Şefi, a professional AI coding assistant specialized in serverless code execution via Modal.com.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

**EXECUTION GUIDELINES:**

For **Simple Tasks** (calculations, prints):
- Use modal_python_executor directly
- Example: print('Hello World') or 2+2*3

For **Complex Tasks** (applications, multi-step):
- First use code_analyzer to plan approach
- Then execute step by step with appropriate tools
- Example: calculator app, file operations, package installation

For **System Operations**:
- Use modal_bash_executor for file management, git, pip install
- Example: ls -la, pip install pandas, git clone

**RESPONSE STYLE:**
- Professional and informative
- Show actual code execution results
- Explain what was accomplished
- Use Turkish when communicating with user

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        return PromptTemplate.from_template(template)
    
    def _classify_intent_fast(self, query: str) -> str:
        """Lightning-fast intent classification (0.001s)"""
        query_lower = query.lower().strip()
        
        # Chat patterns
        chat_patterns = ["merhaba", "selam", "nasılsın", "kim", "teşekkür"]
        if any(pattern in query_lower for pattern in chat_patterns):
            return "CHAT"
        
        # Help patterns  
        help_patterns = ["neler yapabilir", "komutlar", "yardım", "özellik"]
        if any(pattern in query_lower for pattern in help_patterns):
            return "HELP"
        
        # Code patterns
        code_patterns = ["çalıştır", "kod", "python", "hesapla", "print", "import"]
        if any(pattern in query_lower for pattern in code_patterns):
            return "CODE"
        
        return "CODE"  # Default to code execution
    
    def _handle_chat_fast(self, query: str) -> str:
        """Fast chat response without ReAct overhead"""
        responses = {
            "merhaba": "🤖 Merhaba! Atölye Şefi burada - kod çalıştırmaya hazırım! ⚡",
            "selam": "👋 Selam! Hangi kodu çalıştırmak istersin?",
            "nasılsın": "🚀 Harika! Modal.com sistemleri aktif, kod çalıştırmaya hazırım!",
            "kim": "🧠 Ben Atölye Şefi - profesyonel AI kod asistanınızım. Modal.com üzerinde serverless kod çalıştırırım!"
        }
        
        query_lower = query.lower().strip()
        for pattern, response in responses.items():
            if pattern in query_lower:
                return response
        
        return "🤖 Merhaba! Ben Atölye Şefi. Python kodu, bash komutları veya karmaşık uygulamalar çalıştırabilirim. Ne yapmak istersin? ⚡"
    
    def _handle_help_fast(self, query: str) -> str:
        """Fast help response"""
        return """⚡ **ATÖLYE ŞEFİ - YETENEKLER**

🐍 **Python Kodu Çalıştırma:**
• `print('Hello World')` → Anında çalıştırma
• `2+2*3` → Hızlı hesaplama
• `import pandas; df = pd.DataFrame({'A': [1,2,3]}); print(df)` → Veri analizi

🔧 **Bash Komutları:**
• `ls -la` → Dosya listeleme
• `pip install pandas` → Paket kurulum
• `git clone https://github.com/user/repo` → Git işlemleri

🚀 **Karmaşık Uygulamalar:**
• "hesap makinesi yaz" → Tam hesap makinesi uygulaması
• "dosya oluştur" → Dosya oluşturma ve yazma
• "veri analizi yap" → Pandas ile analiz

☁️ **Modal.com Serverless:**
• GPU-accelerated ML workloads
• Auto-scaling container execution
• Cloud-native development environment

💡 **Kullanım:** Sadece ne yapmak istediğini söyle, ben halledeyim!"""

    def run(self, query: str) -> Dict[str, Any]:
        """
        Main execution method - maintains compatibility with GraphAgent interface
        """
        start_time = time.time()
        print(f"\n🚀 [REACT AGENT] Processing: {query}")
        
        try:
            # Fast intent classification for optimization
            intent = self._classify_intent_fast(query)
            
            # Handle simple intents quickly
            if intent == "CHAT":
                result = self._handle_chat_fast(query)
                return {
                    "result": result,
                    "intermediate_steps": [],
                    "plan": [],
                    "execution_time": time.time() - start_time,
                    "method": "fast_chat"
                }
            
            elif intent == "HELP":
                result = self._handle_help_fast(query)
                return {
                    "result": result,
                    "intermediate_steps": [],
                    "plan": [],
                    "execution_time": time.time() - start_time,
                    "method": "fast_help"
                }
            
            # For code tasks, use full ReAct reasoning
            print("🧠 [REACT] Using full ReAct reasoning for code task...")
            
            # Reset callback handler
            self.callback_handler = PerformanceCallbackHandler()
            self.executor.callbacks = [self.callback_handler]
            
            # Execute via ReAct agent
            response = self.executor.invoke({"input": query})
            
            # Extract results
            final_result = response.get("output", "No output generated")
            intermediate_steps = response.get("intermediate_steps", [])
            
            # Format intermediate steps for compatibility
            formatted_steps = []
            for i, step in enumerate(intermediate_steps):
                if hasattr(step, 'tool') and hasattr(step, 'tool_input'):
                    formatted_steps.append({
                        "step_number": i + 1,
                        "tool_used": step.tool,
                        "tool_input": step.tool_input,
                        "result": str(step.observation) if hasattr(step, 'observation') else "",
                        "status": "success"
                    })
            
            execution_time = time.time() - start_time
            
            print(f"✅ [REACT AGENT] Completed in {execution_time:.2f}s")
            
            return {
                "result": final_result,
                "intermediate_steps": formatted_steps,
                "plan": [f"ReAct reasoning with {len(formatted_steps)} steps"],
                "execution_time": execution_time,
                "method": "react_reasoning",
                "llm_calls": self.callback_handler.llm_calls,
                "tool_calls": self.callback_handler.tool_calls
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"❌ ReAct Agent Error: {str(e)}"
            print(error_msg)
            
            # Return error in compatible format
            return {
                "result": f"{error_msg}\n\n🔧 **Fallback:** Temel Python çalıştırıcısını deneyin veya sorunu daha basit ifade edin.",
                "intermediate_steps": [{"step_number": 1, "result": error_msg, "status": "error"}],
                "plan": ["Error handling"],
                "execution_time": execution_time,
                "method": "error_fallback"
            }
    
    async def astream(self, input_data: Dict, config: Optional[Dict] = None):
        """
        Async streaming interface for compatibility with GraphAgent
        """
        try:
            print("🌊 [REACT AGENT] Async streaming mode...")
            
            # For streaming, we'll simulate step-by-step execution
            query = input_data.get("input", "")
            
            # Yield initial state
            yield {"status": "starting", "input": query}
            
            # Execute normally and yield final result
            result = self.run(query)
            
            yield {"status": "completed", "result": result}
            
        except Exception as e:
            yield {"status": "error", "error": str(e)}

# Factory function for compatibility
def create_react_agent() -> ReactAgent:
    """Create ReactAgent instance - replaces create_graph_agent"""
    return ReactAgent()

# Backward compatibility alias
create_graph_agent = create_react_agent

# Test execution
if __name__ == "__main__":
    print("🧪 === REACT AGENT TEST ===")
    
    # Initialize agent
    agent = ReactAgent()
    
    # Test queries
    test_queries = [
        "merhaba",  # Chat test
        "neler yapabilirsin",  # Help test
        "2+2 hesapla",  # Simple code test
        "print('Hello World from ReAct!')",  # Direct Python test
        "hesap makinesi uygulaması yaz"  # Complex task test
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🧪 Test: {query}")
        print('='*60)
        
        result = agent.run(query)
        
        print(f"📤 Result: {result['result']}")
        print(f"⏱️  Time: {result['execution_time']:.2f}s")
        print(f"🔧 Method: {result['method']}")
        
        if result['intermediate_steps']:
            print(f"📋 Steps: {len(result['intermediate_steps'])}")
        
        print("\n" + "="*60)