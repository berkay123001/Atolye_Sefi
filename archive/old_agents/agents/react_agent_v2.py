#!/usr/bin/env python3
"""
🧠 ATOLYE SEFI - SIMPLIFIED REACT AGENT V2
Professional Agent without complex LangChain dependencies
Maintains Modal.com integration + performance optimizations
"""

import sys
import os
import time
from typing import Dict, List, Any, Optional

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Minimal imports
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler

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
        print(f"🚀 [REACT AGENT V2] Starting: {inputs.get('input', '')[:50]}...")
        
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        if self.start_time:
            duration = time.time() - self.start_time
            print(f"⚡ [PERFORMANCE] Total time: {duration:.2f}s | LLM calls: {self.llm_calls} | Tool calls: {self.tool_calls}")
            
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        self.llm_calls += 1
        
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        self.tool_calls += 1

class ReactAgentV2:
    """
    Simplified Professional ReAct Agent for Atölye Şefi
    Manual ReAct implementation without complex LangChain dependencies
    """
    
    def __init__(self):
        """Initialize Simplified ReAct Agent with Modal.com integration"""
        print("🧠 [REACT AGENT V2] Initializing simplified professional ReAct system...")
        
        # Initialize LLM with Groq
        self.llm = ChatGroq(
            model_name=settings.AGENT_MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.1,
            max_tokens=4000,
            verbose=True
        )
        
        # Performance monitoring
        self.callback_handler = PerformanceCallbackHandler()
        
        # Define available tools
        self.tools = {
            "modal_python_executor": self._execute_python_code,
            "modal_bash_executor": self._execute_bash_command,
            "code_analyzer": self._analyze_task
        }
        
        print("✅ [REACT AGENT V2] Initialization complete - Ready for professional code execution!")
    
    def _execute_python_code(self, code: str) -> str:
        """Execute Python code via Modal.com"""
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
    
    def _execute_bash_command(self, command: str) -> str:
        """Execute bash command via Modal.com"""
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
    
    def _analyze_task(self, task: str) -> str:
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
            if any(keyword in task_lower for keyword in ["calculator", "hesap makinesi", "app", "program", "script"]):
                return "📋 ANALYSIS: Complex application detected. Creating calculator with file save functionality."
            
            if any(keyword in task_lower for keyword in ["file", "create", "write", "save"]):
                return "📋 ANALYSIS: File operation detected. Use file I/O operations with proper error handling."
            
            if any(keyword in task_lower for keyword in ["install", "pip", "package"]):
                return "📋 ANALYSIS: Package installation detected. Use bash command: pip install <package>"
            
            if any(keyword in task_lower for keyword in ["torch", "tensorflow", "ml", "model", "gpu"]):
                return "📋 ANALYSIS: ML/AI workload detected. GPU execution recommended for optimal performance."
            
            return "📋 ANALYSIS: General task detected. Recommend Python execution with appropriate libraries."
            
        except Exception as e:
            return f"❌ ANALYSIS ERROR: {str(e)}"
    
    def _classify_intent_fast(self, query: str) -> str:
        """Lightning-fast intent classification (0.001s)"""
        query_lower = query.lower().strip()
        
        # Chat patterns - expanded for better conversation
        chat_patterns = ["merhaba", "selam", "nasılsın", "kim", "teşekkür", "nereye", "hangi", "ne zaman", "nasıl"]
        if any(pattern in query_lower for pattern in chat_patterns):
            return "CHAT"
        
        # Help patterns  
        help_patterns = ["neler yapabilir", "komutlar", "yardım", "özellik"]
        if any(pattern in query_lower for pattern in help_patterns):
            return "HELP"
        
        # Code patterns
        code_patterns = ["çalıştır", "kod", "python", "hesapla", "print", "import", "yaz", "oluştur", "dosya"]
        if any(pattern in query_lower for pattern in code_patterns):
            return "CODE"
        
        return "CHAT"  # Default to chat for better conversation
    
    def _handle_chat_fast(self, query: str) -> str:
        """Fast chat response without ReAct overhead"""
        responses = {
            "merhaba": "🤖 Merhaba! Atölye Şefi burada - kod çalıştırmaya hazırım! ⚡",
            "selam": "👋 Selam! Hangi kodu çalıştırmak istersin?",
            "nasılsın": "🚀 Harika! Modal.com sistemleri aktif, kod çalıştırmaya hazırım!",
            "kim": "🧠 Ben Atölye Şefi - profesyonel AI kod asistanınızım. Modal.com üzerinde serverless kod çalıştırırım!",
            "nereye": "📁 Dosyalar geçerli çalışma dizinine (current working directory) kaydediliyor. Genellikle projenin ana klasörü olan `/home/berkayhsrt/Atolye_Sefi/` dizinine kaydediyorum.",
            "hangi": "🤔 Hangi konuda yardım istiyorsun? Kod çalıştırma, dosya oluşturma, veya başka bir şey mi?",
            "teşekkür": "😊 Rica ederim! Başka bir şeye ihtiyacın olursa söyle!"
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
    
    def _execute_react_reasoning(self, query: str) -> Dict[str, Any]:
        """Execute manual ReAct reasoning for complex tasks"""
        
        # Create ReAct prompt
        react_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Atölye Şefi - profesyonel AI kod asistanısın. Modal.com serverless sistemde kod çalıştırırsın.

Available Tools:
- modal_python_executor: Python kodu çalıştır
- modal_bash_executor: Bash komutları çalıştır  
- code_analyzer: Görev analizi yap

🔥 DOSYA OLUŞTURMA KURALI:
Kullanıcı "dosya oluştur", "kaydet", "yaz" dediğinde MUTLAKA şu pattern'i kullan:

```python
# Kod içeriği
code_content = '''
# Burada gerçek kod
'''

# Dosyayı kaydet
with open('dosya_adi.py', 'w', encoding='utf-8') as f:
    f.write(code_content)

print("✅ Dosya 'dosya_adi.py' başarıyla oluşturuldu!")
```

ReAct Format kullan:
Thought: [Görevi analiz et]
Action: [Tool seç: modal_python_executor, modal_bash_executor, veya code_analyzer]
Action Input: [Tool'a gönderilecek input]
Observation: [Tool sonucu - sen doldurmayacaksın, sistem dolduracak]
... (gerektiğinde tekrarla)
Thought: Artık cevabı biliyorum
Final Answer: [Türkçe kapsamlı cevap]

Başla!"""),
            ("user", "Görev: {task}")
        ])
        
        max_iterations = 5
        iteration = 0
        thoughts = []
        
        try:
            # Initial thought
            response = self.llm.invoke(react_prompt.format_messages(task=query))
            content = response.content
            
            while iteration < max_iterations:
                iteration += 1
                print(f"\n🧠 [REACT ITERATION {iteration}]")
                
                # Parse ReAct response
                lines = content.split('\n')
                current_thought = ""
                current_action = ""
                current_action_input = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("Thought:"):
                        current_thought = line.replace("Thought:", "").strip()
                    elif line.startswith("Action:"):
                        current_action = line.replace("Action:", "").strip()
                    elif line.startswith("Action Input:"):
                        current_action_input = line.replace("Action Input:", "").strip()
                    elif line.startswith("Final Answer:"):
                        final_answer = line.replace("Final Answer:", "").strip()
                        # Get remaining content as final answer
                        final_index = content.find("Final Answer:")
                        if final_index != -1:
                            final_answer = content[final_index + len("Final Answer:"):].strip()
                        
                        return {
                            "result": final_answer,
                            "intermediate_steps": thoughts,
                            "iterations": iteration
                        }
                
                # Execute action if found
                if current_action and current_action_input:
                    print(f"🔧 Action: {current_action}")
                    print(f"📥 Input: {current_action_input[:100]}...")
                    
                    # Execute tool
                    if current_action in self.tools:
                        try:
                            observation = self.tools[current_action](current_action_input)
                            print(f"📤 Observation: {observation[:200]}...")
                            
                            # Store step
                            thoughts.append({
                                "thought": current_thought,
                                "action": current_action,
                                "action_input": current_action_input,
                                "observation": observation
                            })
                            
                            # Continue reasoning with observation
                            continue_prompt = ChatPromptTemplate.from_messages([
                                ("system", "ReAct reasoning devam ediyor. Observation'ı kullanarak devam et."),
                                ("user", f"""Previous context:
Thought: {current_thought}
Action: {current_action}
Action Input: {current_action_input}
Observation: {observation}

Original task: {query}

Continue with next Thought or provide Final Answer:""")
                            ])
                            
                            response = self.llm.invoke(continue_prompt.format_messages())
                            content = response.content
                            
                        except Exception as e:
                            observation = f"Tool execution error: {str(e)}"
                            thoughts.append({
                                "thought": current_thought,
                                "action": current_action,
                                "action_input": current_action_input,
                                "observation": observation
                            })
                            break
                    else:
                        observation = f"Unknown tool: {current_action}"
                        thoughts.append({
                            "thought": current_thought,
                            "action": current_action,
                            "action_input": current_action_input,
                            "observation": observation
                        })
                        break
                else:
                    # No valid action found, break
                    break
            
            # If we reach here, provide fallback answer
            return {
                "result": f"ReAct reasoning completed with {iteration} iterations. See intermediate steps for details.",
                "intermediate_steps": thoughts,
                "iterations": iteration
            }
            
        except Exception as e:
            return {
                "result": f"❌ ReAct reasoning error: {str(e)}",
                "intermediate_steps": thoughts,
                "iterations": iteration
            }
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Main execution method - maintains compatibility with GraphAgent interface
        """
        start_time = time.time()
        print(f"\n🚀 [REACT AGENT V2] Processing: {query}")
        
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
            
            # For code tasks, use ReAct reasoning
            print("🧠 [REACT] Using ReAct reasoning for code task...")
            
            react_result = self._execute_react_reasoning(query)
            
            # Format intermediate steps for compatibility
            formatted_steps = []
            for i, step in enumerate(react_result.get("intermediate_steps", [])):
                formatted_steps.append({
                    "step_number": i + 1,
                    "tool_used": step.get("action", "unknown"),
                    "tool_input": step.get("action_input", ""),
                    "result": step.get("observation", ""),
                    "status": "success"
                })
            
            execution_time = time.time() - start_time
            
            print(f"✅ [REACT AGENT V2] Completed in {execution_time:.2f}s")
            
            return {
                "result": react_result.get("result", "No result generated"),
                "intermediate_steps": formatted_steps,
                "plan": [f"ReAct reasoning with {react_result.get('iterations', 0)} iterations"],
                "execution_time": execution_time,
                "method": "react_reasoning",
                "llm_calls": self.callback_handler.llm_calls,
                "tool_calls": len(formatted_steps)
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"❌ ReAct Agent V2 Error: {str(e)}"
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
            print("🌊 [REACT AGENT V2] Async streaming mode...")
            
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
def create_react_agent() -> ReactAgentV2:
    """Create ReactAgentV2 instance - replaces create_graph_agent"""
    return ReactAgentV2()

# Backward compatibility alias
create_graph_agent = create_react_agent

# Test execution
if __name__ == "__main__":
    print("🧪 === REACT AGENT V2 TEST ===")
    
    # Initialize agent
    agent = ReactAgentV2()
    
    # Test queries
    test_queries = [
        "merhaba",  # Chat test
        "neler yapabilirsin",  # Help test
        "print('Hello World from ReAct V2!')",  # Direct Python test
        "2+2*3 hesapla",  # Simple calculation
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🧪 Test: {query}")
        print('='*60)
        
        result = agent.run(query)
        
        print(f"📤 Result: {result['result'][:200]}...")
        print(f"⏱️  Time: {result['execution_time']:.2f}s")
        print(f"🔧 Method: {result['method']}")
        
        if result['intermediate_steps']:
            print(f"📋 Steps: {len(result['intermediate_steps'])}")
        
        print("\n" + "="*60)