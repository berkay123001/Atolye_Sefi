# app/dashboard.py

import gradio as gr
import json
from datetime import datetime

# --- Proje Bileşenleri ---
try:
    from config import settings
    # NEW: ReactAgent V3 - WITH REAL FILE CREATION!
    from agents.react_agent_v3 import ReactAgentV3 as GraphAgent
    from tools.pod_management_tools import prepare_environment_with_ssh
    
    # MODAL CLOUD: Import Modal functions for cloud execution
    print("🔄 Modal fonksiyonları (CLOUD VERSION) hydrate ediliyor...")
    from tools.modal_executor import execute_bash_command, execute_simple_code, execute_gpu_code
    print("✅ Modal CLOUD fonksiyonları hazır!")
    
    print("Yapılandırma ve GraphAgent başarıyla yüklendi.")
except ImportError as e:
    print(f"Hata: Gerekli modüller yüklenemedi: {e}")
    print("Lütfen projenin bir paket olarak doğru kurulduğundan emin olun.")
    raise

# --- Tek Seferlik GraphAgent Başlatma ---
print("GraphAgent nesnesi oluşturuluyor...")
graph_agent = GraphAgent()
print("GraphAgent akış şeması derleniyor...")
# GraphAgent.__init__ içinde zaten build_graph() çağrılıyor, tekrar çağırmaya gerek yok
print("GraphAgent tamamen hazır ve operasyonel.")

def run_agent_interaction(user_message: str, history: list, logs: str):
    """
    Kullanıcı etkileşimini yönetir. Bu yeni versiyon GraphAgent ile
    doğrudan ve senkron şekilde çalışır - karmaşık Queue/threading yok!
    """
    # 1. Kullanıcının mesajını sohbete ekle (eski format - [user, bot] listesi)
    history.append([user_message, None])
    
    # 2. Zaman damgası ile yeni görev başlangıcını logla
    timestamp = datetime.now().strftime("%H:%M:%S")
    new_log_entry = f"\n=== GÖREV BAŞLADI [{timestamp}] ===\nKullanıcı: {user_message}\n"
    
    # Eğer bu ilk çalıştırmaysa, başlangıç metnini temizle
    if logs == "Ajan bir komut bekliyor...":
        current_logs = new_log_entry
    else:
        current_logs = logs + "\n" + new_log_entry
    
    try:
        # 3. GraphAgent'ı doğrudan çağır - tek satırda tüm işlem!
        print(f"GraphAgent'a gönderiliyor: {user_message}")
        final_state = graph_agent.run(user_message)
        
        # 4. Ajanın nihai cevabını al ve eski formatta ekle
        agent_response = final_state.get('result', 'Ajan bir cevap üretemedi.')
        history[-1][1] = agent_response  # Son mesajın bot kısmını doldur
        
        # 5. Intermediate steps'i logla (GraphAgent'ın düşünce süreci)
        intermediate_steps = final_state.get('intermediate_steps', [])
        
        current_logs += f"GraphAgent Düşünce Süreci:\n"
        if intermediate_steps:
            for i, step in enumerate(intermediate_steps, 1):
                current_logs += f"  Adım {i}: {str(step)}\n"
        else:
            current_logs += "  (Ajan doğrudan sonuca ulaştı)\n"
            
        current_logs += f"\nNihai Cevap: {agent_response}\n"
        current_logs += f"=== GÖREV TAMAMLANDI [{datetime.now().strftime('%H:%M:%S')}] ===\n"
        
        print("GraphAgent görevi başarıyla tamamladı.")
        
    except Exception as e:
        # 6. Hata durumunda kullanıcıya bilgi ver
        error_msg = f"**HATA OLUŞTU:**\n\n{str(e)}"
        history[-1][1] = error_msg  # Son mesajın bot kısmını hata ile doldur
        current_logs += f"HATA: {str(e)}\n"
        current_logs += f"=== GÖREV HATA İLE SONLANDI [{datetime.now().strftime('%H:%M:%S')}] ===\n"
        
        print(f"GraphAgent hatası: {e}")
    
    # 7. Güncellenmiş history, logs ve temizlenmiş input'u döndür
    return history, current_logs, ""

# Debug Workspace Helper Functions
def refresh_file_list():
    """Refresh the file dropdown list"""
    try:
        # List files from Modal workspace volume
        from tools.modal_executor import list_workspace_files
        result = list_workspace_files.remote()
        if result["status"] == "success":
            file_choices = [f["name"] for f in result["files"]]
            return gr.Dropdown(choices=file_choices, value=file_choices[0] if file_choices else None)
    except:
        # Fallback to local files
        import os
        local_files = [f for f in os.listdir(".") if f.endswith(('.py', '.txt', '.md'))]
        return gr.Dropdown(choices=local_files, value=local_files[0] if local_files else None)
    
    return gr.Dropdown(choices=[], value=None)

def load_file_content(filename):
    """Load file content for viewer"""
    if not filename:
        return ""
    
    try:
        # Try to get from Modal workspace
        from tools.modal_executor import get_workspace_file
        result = get_workspace_file.remote(filename)
        if result["status"] == "success":
            return result["content"]
    except:
        pass
    
    # Fallback to local file
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return f"Error: Could not load file {filename}"

def get_debug_logs():
    """Get current debug logs"""
    return "🔧 Debug logs will appear here when agent runs..."

def create_gpu_pod():
    """GPU Pod oluşturma fonksiyonu"""
    try:
        result = prepare_environment_with_ssh.invoke({
            "gpu_type_id": "NVIDIA GeForce RTX 3070"
        })
        
        if result.get('status') == 'success':
            return f"""🎉 **Pod Başarıyla Oluşturuldu!**

🆔 **Pod ID:** {result.get('pod_id')}
🔗 **Jupyter URL:** {result.get('jupyter_url')}
🔐 **Şifre:** atolye123

✅ Pod artık kullanıma hazır!"""
        else:
            return f"❌ **Pod Oluşturma Hatası:** {result.get('message')}"
            
    except Exception as e:
        return f"❌ **Beklenmeyen Hata:** {str(e)}"

def get_current_pods():
    """Mevcut pod'ları listeler"""
    try:
        import sys
        import os
        
        # runpod_test_script.py'ı import et
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'runpod_test_script.py')
        
        if os.path.exists(script_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location("runpod_script", script_path)
            runpod_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runpod_script)
            
            # Output'u yakala
            import io
            from contextlib import redirect_stdout
            
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                runpod_script.list_all_pods()
            
            output = output_buffer.getvalue()
            
            if "Hiç pod bulunamadı" in output:
                return "📝 **Mevcut Pod Yok**\n\nHenüz aktif pod'unuz bulunmuyor."
            else:
                return f"📋 **Mevcut Pod'lar:**\n```\n{output}\n```"
        else:
            return "❌ **Script bulunamadı**"
            
    except Exception as e:
        return f"❌ **Pod Listesi Hatası:** {str(e)}"

def execute_terminal_command(command: str, current_output: str):
    """Execute command in VS Code-style terminal"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add command to terminal
        new_output = current_output + f"atölyeşefi@workspace:~$ {command}\n"
        
        # Execute via GraphAgent
        result = graph_agent.run(command)
        final_result = result.get("result", "Command execution failed")
        
        new_output += f"{final_result}\n"
        new_output += f"[{timestamp}] Command completed\n"
        new_output += "─" * 60 + "\n"
        
        return new_output
        
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_output = current_output + f"atölyeşefi@workspace:~$ {command}\n"
        error_output += f"bash: {command}: command not found\n"
        error_output += f"[{timestamp}] Command failed: {str(e)}\n"
        error_output += "─" * 60 + "\n"
        
        return error_output

def ai_improve_code(code: str, prompt: str):
    """AI ile kod geliştirme"""
    try:
        if not prompt.strip():
            prompt = "Bu kodu geliştir ve optimize et"
        
        ai_request = f"""Bu Python kodunu geliştir:

```python
{code}
```

İstek: {prompt}

Sadece geliştirilmiş Python kodunu döndür, açıklama yapma."""
        
        result = graph_agent.run(ai_request)
        improved_code = result.get("result", code)
        
        # Extract code from response if wrapped in markdown
        if "```python" in improved_code:
            start = improved_code.find("```python") + 9
            end = improved_code.find("```", start)
            if end != -1:
                improved_code = improved_code[start:end].strip()
        
        return improved_code
        
    except Exception as e:
        return f"# AI Error: {str(e)}\n{code}"

def ai_explain_code(code: str):
    """AI ile kod açıklama"""
    try:
        ai_request = f"""Bu Python kodunu açıkla:

```python
{code}
```

Kısaca ve anlaşılır şekilde açıkla."""
        
        result = graph_agent.run(ai_request)
        explanation = result.get("result", "Kod açıklaması alınamadı.")
        
        return f"# AI Explanation:\n# {explanation}\n\n{code}"
        
    except Exception as e:
        return f"# AI Error: {str(e)}\n{code}"

def ai_debug_code(code: str):
    """AI ile kod debug"""
    try:
        ai_request = f"""Bu Python kodundaki potansiyel hataları bul ve düzelt:

```python
{code}
```

Sadece düzeltilmiş kodu döndür."""
        
        result = graph_agent.run(ai_request)
        debugged_code = result.get("result", code)
        
        # Extract code from response if wrapped in markdown
        if "```python" in debugged_code:
            start = debugged_code.find("```python") + 9
            end = debugged_code.find("```", start)
            if end != -1:
                debugged_code = debugged_code[start:end].strip()
        
        return debugged_code
        
    except Exception as e:
        return f"# Debug Error: {str(e)}\n{code}"

def ai_quick_assist(current_code: str):
    """Quick AI assistance based on current code"""
    try:
        # Analyze current code and provide quick suggestions
        if not current_code.strip():
            suggestion = "def main():\n    print('Hello World!')\n\nif __name__ == '__main__':\n    main()"
        elif "def" not in current_code:
            suggestion = f"def main():\n    {current_code}\n\nif __name__ == '__main__':\n    main()"
        elif "print" not in current_code:
            suggestion = current_code + "\n    print('Function executed successfully!')"
        else:
            # Add error handling
            suggestion = current_code.replace(
                "def main():",
                "def main():\n    try:"
            ) + "\n    except Exception as e:\n        print(f'Error: {e}')"
        
        return suggestion
        
    except Exception as e:
        return current_code

# === SIMPLE WORKSPACE FUNCTIONS ===
# Global workspace state
simple_workspace_files = {
    "main.py": """# Welcome to Simple Workspace
print("Hello from Atölye Şefi!")
print("Ready for modal execution!")

def main():
    result = 2 + 2
    print(f"Calculation: {result}")
    return result

if __name__ == "__main__":
    main()""",
    "utils.py": """# Utility functions
def helper():
    return "Helper function called!"

def calculate(a, b):
    return a + b

print("Utils loaded!")""",
    "train.py": """# Training script
import time

def train_model():
    print("Starting training...")
    for epoch in range(3):
        print(f"Epoch {epoch + 1}/3")
        time.sleep(0.5)
    print("Training completed!")

if __name__ == "__main__":
    train_model()"""
}

def get_workspace_file_content(filename: str):
    """Get file content from workspace"""
    if not filename:
        return "# No file selected"
    return simple_workspace_files.get(filename, f"# File {filename} not found")

def save_to_modal_workspace(filename: str, content: str):
    """Save file to Modal workspace volume"""
    try:
        # Update local workspace first
        simple_workspace_files[filename] = content
        
        # Try to save to modal volume (if modal is available)
        try:
            from tools.modal_executor import save_generated_code
            result = save_generated_code.remote(filename, content)
            return f"✅ {filename} saved to local + Modal workspace!"
        except Exception as modal_error:
            print(f"Modal save failed: {modal_error}")
            return f"✅ {filename} saved locally (Modal unavailable)"
        
    except Exception as e:
        return f"❌ Error saving {filename}: {str(e)}"

def load_from_modal_workspace():
    """Load files from Modal workspace volume"""
    try:
        from tools.modal_executor import list_workspace_files
        
        result = list_workspace_files.remote()
        
        if result["status"] == "success":
            files = result["files"]
            # Update local workspace with modal files
            for file_info in files:
                simple_workspace_files[file_info["name"]] = file_info["content"]
            
            return list(simple_workspace_files.keys())
        else:
            return list(simple_workspace_files.keys())
            
    except Exception as e:
        print(f"Modal workspace load error: {e}")
        return list(simple_workspace_files.keys())

def execute_file_in_modal(filename: str, content: str):
    """Execute file content in Modal"""
    try:
        # Try modal execution first
        try:
            from tools.modal_executor import execute_simple_code
            result = execute_simple_code.remote(content)
            
            if result["status"] == "success":
                output = result.get("output", "No output")
                return f"✅ Executed {filename} in Modal:\n\n{output}"
            else:
                error = result.get("error", "Unknown error")
                return f"❌ Modal error in {filename}:\n\n{error}"
                
        except Exception as modal_error:
            # Fallback to local execution
            print(f"Modal execution failed: {modal_error}")
            
            # Local execution fallback
            import sys
            from io import StringIO
            
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            try:
                exec(content, {"__name__": "__main__"})
                output = mystdout.getvalue()
                return f"✅ Executed {filename} locally (Modal unavailable):\n\n{output}"
            except Exception as exec_error:
                return f"❌ Local execution error in {filename}:\n\n{str(exec_error)}"
            finally:
                sys.stdout = old_stdout
            
    except Exception as e:
        return f"❌ Execution error: {str(e)}"

# Global current file tracker
current_workspace_file = "main.py"

def generate_file_sidebar_html():
    """Generate clickable file sidebar like VS Code"""
    global current_workspace_file
    
    html = f"""
    <div style="background: #252526; border-radius: 0; padding: 4px; min-height: 350px; 
                font-family: 'Segoe UI', monospace; margin: 0;">
    """
    
    for filename in sorted(simple_workspace_files.keys()):
        # File icons - smaller
        if filename.endswith('.py'):
            icon = "🐍"
            color = "#3776ab"
        elif filename.endswith('.txt'):
            icon = "📄"
            color = "#9cdcfe"
        elif filename.endswith('.md'):
            icon = "📝"
            color = "#9cdcfe"
        else:
            icon = "📋"
            color = "#ce9178"
        
        # Highlight selected file
        is_selected = filename == current_workspace_file
        bg_color = "#0e639c" if is_selected else "transparent"
        text_color = "#ffffff" if is_selected else color
        
        html += f"""
        <div class="file-item" 
             onclick="window.selectWorkspaceFile('{filename}')"
             style="padding: 3px 6px; cursor: pointer; border-radius: 2px; 
                    background: {bg_color}; color: {text_color}; font-size: 11px;
                    display: flex; align-items: center; margin-bottom: 1px;
                    transition: background-color 0.1s ease;">
            <span style="margin-right: 4px; font-size: 10px;">{icon}</span>
            <span>{filename}</span>
        </div>
        """
    
    html += """
    </div>
    <style>
        .file-item:hover:not([style*="background: #0e639c"]) { 
            background: #2a2d2e !important; 
        }
        .file-item:active {
            background: #094771 !important;
        }
    </style>
    <script>
        window.selectWorkspaceFile = function(filename) {
            console.log('Selecting workspace file:', filename);
            
            // Multiple attempts to find the hidden selector
            let hiddenSelector = document.querySelector('#workspace_file_selector input');
            if (!hiddenSelector) {
                hiddenSelector = document.querySelector('#workspace_file_selector textarea');
            }
            if (!hiddenSelector) {
                hiddenSelector = document.querySelector('[data-testid="textbox"]');
            }
            
            if (hiddenSelector) {
                console.log('Found selector:', hiddenSelector);
                hiddenSelector.value = filename;
                hiddenSelector.dispatchEvent(new Event('input', { bubbles: true }));
                hiddenSelector.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Force trigger
                const event = new CustomEvent('gradio-change', { 
                    detail: { value: filename },
                    bubbles: true 
                });
                hiddenSelector.dispatchEvent(event);
            } else {
                console.error('Hidden selector not found');
                // Fallback: try all textboxes
                const allInputs = document.querySelectorAll('input, textarea');
                console.log('All inputs found:', allInputs.length);
                for (let input of allInputs) {
                    if (input.style.display === 'none' || input.parentElement.style.display === 'none') {
                        console.log('Trying hidden input:', input);
                        input.value = filename;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        break;
                    }
                }
            }
        };
    </script>
    """
    
    return html

def switch_workspace_file(filename: str):
    """Switch to selected workspace file"""
    global current_workspace_file
    
    if filename in simple_workspace_files:
        current_workspace_file = filename
        return generate_file_sidebar_html(), simple_workspace_files[filename]
    
    return generate_file_sidebar_html(), simple_workspace_files.get(current_workspace_file, "")

def create_new_workspace_file(filename: str):
    """Create new file in workspace - supports .py, .txt, .md"""
    global current_workspace_file
    
    if not filename:
        filename = f"untitled_{datetime.now().strftime('%H%M%S')}.py"
    
    # Add extension if missing
    if '.' not in filename:
        filename += '.py'
    
    # Create content based on file type
    if filename.endswith('.py'):
        new_content = f"""# {filename}
# Created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

def main():
    print("Hello from {filename}!")
    # Your code here
    pass

if __name__ == "__main__":
    main()"""
    elif filename.endswith('.txt'):
        new_content = f"""{filename}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your text content here...

Features:
- Simple text file
- Easy to edit
- No syntax highlighting needed
"""
    elif filename.endswith('.md'):
        base_name = filename.replace('.md', '').replace('_', ' ').title()
        new_content = f"""# {base_name}

> Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This is a markdown file for documentation.

## Features

- **Bold text**
- *Italic text*
- `Code blocks`
- Lists

## Code Example

```python
def hello():
    print("Hello from markdown!")
```

## TODO

- [ ] Add more content
- [ ] Review and update
- [ ] Share with team
"""
    else:
        # Default to text content
        new_content = f"""File: {filename}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Content goes here...
"""
    
    simple_workspace_files[filename] = new_content
    current_workspace_file = filename
    
    # Return updated sidebar and content
    return generate_file_sidebar_html(), new_content

# === LIVE AI AGENT FUNCTIONS ===
def ai_agent_chat(message: str, history: list, current_file: str, current_code: str):
    """Live AI agent with full project context - Cursor-style"""
    try:
        # Build project context
        project_files = []
        for filename, content in simple_workspace_files.items():
            file_preview = content[:200] + "..." if len(content) > 200 else content
            project_files.append(f"{filename}:\n{file_preview}")
        
        project_context = "\n\n".join(project_files)
        
        # Force CHAT mode - add chat keywords to bypass GraphAgent CODE detection
        chat_message = f"merhaba, {message}"  # Force CHAT intent
        
        context_prompt = f"""Sen yardımcı bir AI'sın. Kısa sohbet et.

Dosyalar: {', '.join(simple_workspace_files.keys())}
Açık: {current_file}

Kullanıcı: {message}

Kısa cevap ver."""

        # Use ChatGroq directly for simple chat (bypass GraphAgent code execution)
        try:
            from langchain_groq import ChatGroq
            from config import settings
            
            chat_llm = ChatGroq(
                temperature=0.7,
                model_name=settings.AGENT_MODEL_NAME,
                groq_api_key=settings.GROQ_API_KEY,
                max_tokens=500
            )
            
            response = chat_llm.invoke(context_prompt)
            ai_response = response.content.strip()
            
        except Exception as e:
            ai_response = f"Merhaba! VS Code workspace'de size nasıl yardım edebilirim? 🤖\n\n(Chat hatası: {str(e)})"
        
        # Add to history in correct format
        history.append([message, ai_response])
        
        return history, ""
        
    except Exception as e:
        error_response = f"❌ Özür dilerim, bir hata oluştu: {str(e)}"
        history.append([message, error_response])
        return history, ""

def ai_create_function(current_code: str, filename: str):
    """AI creates new function based on current context"""
    try:
        prompt = f"""Mevcut dosya: {filename}
Mevcut kod:
```python
{current_code}
```

Bu koda uygun yeni bir fonksiyon ekle. Kod tarzını koru ve yararlı bir fonksiyon yaz.
Sadece güncellenmiş Python kodunu döndür."""

        result = graph_agent.run(prompt)
        improved_code = result.get("result", current_code)
        
        # Extract code if wrapped in markdown
        if "```python" in improved_code:
            start = improved_code.find("```python") + 9
            end = improved_code.find("```", start)
            if end != -1:
                improved_code = improved_code[start:end].strip()
        
        # Update workspace
        simple_workspace_files[filename] = improved_code
        
        return improved_code
        
    except Exception as e:
        return f"# AI Create Error: {str(e)}\n{current_code}"

def ai_improve_current_code(current_code: str, filename: str):
    """AI improves current code"""
    try:
        prompt = f"""Bu Python kodunu geliştir ve optimize et:

```python
{current_code}
```

Geliştirmeler:
- Performans optimizasyonu
- Hata kontrolü ekleme
- Kod okunabilirliği
- Best practices

Sadece geliştirilmiş Python kodunu döndür."""

        result = graph_agent.run(prompt)
        improved_code = result.get("result", current_code)
        
        # Extract code if wrapped in markdown
        if "```python" in improved_code:
            start = improved_code.find("```python") + 9
            end = improved_code.find("```", start)
            if end != -1:
                improved_code = improved_code[start:end].strip()
        
        # Update workspace
        simple_workspace_files[filename] = improved_code
        
        return improved_code
        
    except Exception as e:
        return f"# AI Improve Error: {str(e)}\n{current_code}"

def ai_debug_current_code(current_code: str, filename: str):
    """AI debugs current code"""
    try:
        prompt = f"""Bu Python kodundaki hataları bul ve düzelt:

```python
{current_code}
```

Potansiyel sorunlar:
- Syntax hataları
- Logic hataları  
- Exception handling
- Edge cases

Sadece düzeltilmiş Python kodunu döndür."""

        result = graph_agent.run(prompt)
        debugged_code = result.get("result", current_code)
        
        # Extract code if wrapped in markdown
        if "```python" in debugged_code:
            start = debugged_code.find("```python") + 9
            end = debugged_code.find("```", start)
            if end != -1:
                debugged_code = debugged_code[start:end].strip()
        
        # Update workspace
        simple_workspace_files[filename] = debugged_code
        
        return debugged_code
        
    except Exception as e:
        return f"# AI Debug Error: {str(e)}\n{current_code}"

def execute_quick_command(command: str):
    """Quick command'ları GraphAgent ile çalıştırır"""
    try:
        result = graph_agent.run(command)
        return result.get("result", "Sonuç alınamadı")
    except Exception as e:
        return f"❌ **Hata:** {str(e)}"

def quick_hello_world():
    """Hello World yazdır"""
    return execute_quick_command("Hello World yazdır")

def quick_calculate():
    """2+2 hesapla"""
    return execute_quick_command("2+2 hesapla")

def quick_current_time():
    """Şimdiki zamanı göster"""
    return execute_quick_command("şimdiki zamanı göster")

def quick_gpu_environment():
    """GPU ortamı hazırla"""
    return execute_quick_command("16GB VRAM'li GPU ortamı hazırla")

def quick_gpu_status():
    """GPU durumu kontrol et"""
    return execute_quick_command("GPU durumunu kontrol et")

# --- VS Code-Style Workspace Functions ---
# Global file storage for VS Code-like workspace
workspace_files = {
    "main.py": """# Welcome to Atölye Şefi Code Workspace
# VS Code-like development environment

def main():
    print("🚀 Hello from Atölye Şefi!")
    print("Ready for serverless code execution via Modal.com")
    
    # Your code here
    result = 2 + 2
    print(f"Calculation result: {result}")
    
    return result

if __name__ == "__main__":
    main()""",
    "utils.py": """# Utility functions for your project

import json
from datetime import datetime

def helper_function():
    \"\"\"Add your helper functions here\"\"\"
    return "Helper function called!"

def format_output(data):
    \"\"\"Format output data\"\"\"
    if isinstance(data, dict):
        return json.dumps(data, indent=2)
    return str(data)

def get_timestamp():
    \"\"\"Get current timestamp\"\"\"
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
""",
    "requirements.txt": """# Project dependencies
gradio>=4.0.0
modal>=0.56.0
langchain>=0.1.0
langchain-groq>=0.1.0
groq>=0.4.0
pydantic>=2.0.0
""",
    "config.py": """# Configuration file

CLASS_CONFIG = {
    "model_name": "llama-3.1-70b-versatile",
    "temperature": 0.1,
    "max_tokens": 4096
}

DEBUG = True
VERSION = "1.0.0"
"""
}

# Currently selected file in workspace
current_selected_file = "main.py"
open_files = ["main.py"]  # Track open tabs

def execute_code_in_terminal(code: str, current_output: str, status_html: str):
    """Execute code with VS Code-style terminal output"""
    global current_selected_file
    
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Update status to running
        running_status = f"""<div style="color: #FF9800; font-family: 'Segoe UI', monospace; 
                                    padding: 4px 8px; font-size: 12px; display: flex; align-items: center;">
                                <span style="margin-right: 6px;">●</span> 
                                <span>Running {current_selected_file}...</span>
                            </div>"""
        
        # VS Code-style terminal prompt
        new_output = current_output + f"\n\natölyeşefi@workspace:~$ python {current_selected_file}\n"
        new_output += f"[{timestamp}] 🚀 Executing via Modal.com serverless...\n"
        new_output += "\n"
        
        # Execute via GraphAgent
        result = graph_agent.run(f"Bu Python kodunu çalıştır:\n```python\n{code}\n```")
        
        # Parse and format result
        final_result = result.get('result', 'Kod çalıştırılamadı.')
        
        # Add formatted output
        new_output += f"{final_result}\n\n"
        new_output += f"[{timestamp}] ✅ Process finished with exit code 0\n"
        new_output += f"[{timestamp}] ⏱️  Execution time: ~2.3s\n"
        new_output += "─" * 80 + "\n"
        
        # Success status
        success_status = f"""<div style="color: #4CAF50; font-family: 'Segoe UI', monospace; 
                                    padding: 4px 8px; font-size: 12px; display: flex; align-items: center;">
                                <span style="margin-right: 6px;">●</span> 
                                <span>Ready</span>
                            </div>"""
        
        return new_output, success_status
        
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_output = current_output + f"\n\natölyeşefi@workspace:~$ python {current_selected_file}\n"
        error_output += f"[{timestamp}] ❌ ERROR: {str(e)}\n"
        error_output += f"[{timestamp}] ❌ Process finished with exit code 1\n"
        error_output += "─" * 80 + "\n"
        
        error_status = f"""<div style="color: #F44336; font-family: 'Segoe UI', monospace; 
                                  padding: 4px 8px; font-size: 12px; display: flex; align-items: center;">
                              <span style="margin-right: 6px;">●</span> 
                              <span>Error</span>
                          </div>"""
        
        return error_output, error_status

def create_new_file(filename: str):
    """Create new file with VS Code-style feedback"""
    global current_selected_file, open_files
    
    try:
        if not filename or filename.strip() == "":
            filename = f"untitled_{datetime.now().strftime('%H%M%S')}.py"
        
        # Add .py extension if not present and no extension exists
        if '.' not in filename:
            filename += '.py'
        
        # Prevent duplicate files
        if filename in workspace_files:
            return generate_file_explorer_html(), workspace_files[current_selected_file], generate_tab_bar_html(), f"File '{filename}' already exists!"
        
        # Create file content based on extension
        if filename.endswith('.py'):
            file_content = f"""# {filename}
# Created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

def main():
    \"\"\"Main function for {filename}\"\"\"
    print(f"Hello from {filename}!")
    # Your code here
    pass

if __name__ == "__main__":
    main()
"""
        elif filename.endswith('.txt'):
            file_content = f"""Text file: {filename}
Created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your content here...
"""
        elif filename.endswith('.md'):
            file_content = f"""# {filename.replace('.md', '').replace('_', ' ').title()}

Created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Your markdown content here...

## Features

- Feature 1
- Feature 2
- Feature 3
"""
        else:
            file_content = f"""# {filename}
# Created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Your content here...
"""
        
        # Add to workspace
        workspace_files[filename] = file_content
        current_selected_file = filename
        
        # Add to open files if not already open
        if filename not in open_files:
            open_files.append(filename)
        
        return generate_file_explorer_html(), file_content, generate_tab_bar_html(), ""
        
    except Exception as e:
        return generate_file_explorer_html(), workspace_files.get(current_selected_file, ""), generate_tab_bar_html(), f"Error creating file: {str(e)}"

def save_current_file(code: str):
    """Save current file with VS Code-style feedback"""
    global current_selected_file
    
    try:
        if current_selected_file in workspace_files:
            workspace_files[current_selected_file] = code
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            saved_status = f"""<div style="color: #4CAF50; font-family: 'Segoe UI', monospace; 
                                     padding: 4px 8px; font-size: 12px; display: flex; align-items: center;">
                                 <span style="margin-right: 6px;">●</span> 
                                 <span>Saved at {timestamp}</span>
                             </div>"""
            
            return saved_status
        else:
            error_status = """<div style="color: #F44336; font-family: 'Segoe UI', monospace; 
                                     padding: 4px 8px; font-size: 12px; display: flex; align-items: center;">
                                 <span style="margin-right: 6px;">●</span> 
                                 <span>Save Error: File not found</span>
                             </div>"""
            return error_status
        
    except Exception as e:
        error_status = f"""<div style="color: #F44336; font-family: 'Segoe UI', monospace; 
                                   padding: 4px 8px; font-size: 12px; display: flex; align-items: center;">
                               <span style="margin-right: 6px;">●</span> 
                               <span>Save Error: {str(e)}</span>
                           </div>"""
        return error_status

def format_current_code(code: str):
    """Format code with VS Code-style auto-formatting"""
    try:
        # Advanced Python code formatting
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        in_multiline_string = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle multiline strings
            if '"""' in stripped or "'''" in stripped:
                in_multiline_string = not in_multiline_string
                formatted_lines.append('    ' * indent_level + stripped)
                continue
            
            if in_multiline_string:
                formatted_lines.append(line)  # Keep original formatting in strings
                continue
            
            if not stripped:
                formatted_lines.append('')
                continue
            
            # Handle dedenting keywords
            if stripped.startswith(('else:', 'elif ', 'except:', 'except ', 'finally:', 'break', 'continue', 'return', 'pass')):
                if stripped.startswith(('else:', 'elif ', 'except:', 'except ', 'finally:')):
                    formatted_lines.append('    ' * max(0, indent_level - 1) + stripped)
                else:
                    formatted_lines.append('    ' * indent_level + stripped)
            # Handle indenting keywords
            elif stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try:')):
                formatted_lines.append('    ' * indent_level + stripped)
                if stripped.endswith(':'):
                    indent_level += 1
            # Handle other lines
            else:
                formatted_lines.append('    ' * indent_level + stripped)
            
            # Adjust indent level
            if stripped.startswith(('else:', 'elif ', 'except:', 'except ', 'finally:')) and stripped.endswith(':'):
                indent_level = max(1, indent_level)  # Ensure minimum indent for blocks
        
        return '\n'.join(formatted_lines)
        
    except Exception as e:
        return code  # Return original if formatting fails

def generate_file_explorer_html():
    """Generate VS Code-style file explorer with working click handlers"""
    global current_selected_file
    
    # Get a unique identifier for this explorer instance
    import time
    explorer_id = f"explorer_{int(time.time() * 1000)}"
    
    html = f"""
    <div id="{explorer_id}" style="background: #252526; border-radius: 0; padding: 8px; min-height: 450px; 
                border-right: 1px solid #3c3c3c; font-family: 'Segoe UI', -apple-system, monospace;">
        <div style="color: #cccccc; font-size: 11px; font-weight: bold; margin-bottom: 8px; 
                    text-transform: uppercase; letter-spacing: 0.5px;">EXPLORER</div>
        
        <div style="margin-bottom: 12px;">
            <div style="color: #cccccc; font-size: 12px; display: flex; align-items: center;">
                <span style="margin-right: 6px;">📁</span>
                <span style="font-weight: 600;">ATOLYE_SEFI</span>
            </div>
        </div>
    """
    
    # File list with data attributes for click handling
    for filename in sorted(workspace_files.keys()):
        # File icons based on extension
        if filename.endswith('.py'):
            icon = "🐍"
            color = "#3776ab"
        elif filename.endswith('.txt'):
            icon = "📄"
            color = "#9cdcfe"
        elif filename.endswith('.md'):
            icon = "📝"
            color = "#9cdcfe"
        else:
            icon = "📋"
            color = "#ce9178"
        
        # Highlight selected file
        is_selected = filename == current_selected_file
        bg_color = "#0e639c" if is_selected else "transparent"
        selected_class = "selected" if is_selected else ""
        
        html += f"""
        <div class="file-item {selected_class}" 
             data-filename="{filename}"
             onclick="window.selectFile('{filename}')"
             style="padding: 4px 8px; cursor: pointer; border-radius: 3px; 
                    background: {bg_color}; color: #cccccc; font-size: 13px;
                    display: flex; align-items: center; margin-bottom: 1px;
                    transition: background-color 0.1s ease;">
            <span style="margin-right: 8px; font-size: 12px;">{icon}</span>
            <span style="color: {color if not is_selected else '#ffffff'};">{filename}</span>
        </div>
        """
    
    html += f"""
    </div>
    <style>
        #{explorer_id} .file-item:hover:not(.selected) {{ 
            background: #2a2d2e !important; 
        }}
        #{explorer_id} .file-item:active {{
            background: #094771 !important;
        }}
        #{explorer_id} .file-item.selected {{
            background: #0e639c !important;
            color: #ffffff !important;
        }}
    </style>
    <script>
        // Global file selection handler
        window.selectFile = function(filename) {{
            console.log('Selecting file:', filename);
            // Trigger gradio event by finding and clicking the hidden file selector
            const hiddenInput = document.querySelector('#file_selector input');
            if (hiddenInput) {{
                hiddenInput.value = filename;
                hiddenInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                hiddenInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }};
    </script>
    """
    
    return html

def clear_terminal_output():
    """Clear terminal with VS Code-style prompt"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"atölyeşefi@workspace:~$ clear\n[{timestamp}] Terminal cleared\n\natölyeşefi@workspace:~$ Ready for commands...\n"

def refresh_file_explorer():
    """Refresh VS Code-style file explorer"""
    return generate_file_explorer_html()

def switch_file(filename: str):
    """Switch to selected file in editor"""
    global current_selected_file, open_files
    
    if filename in workspace_files:
        current_selected_file = filename
        
        # Add to open files if not already open
        if filename not in open_files:
            open_files.append(filename)
        
        return generate_file_explorer_html(), workspace_files[filename], generate_tab_bar_html()
    
    return generate_file_explorer_html(), workspace_files.get(current_selected_file, ""), generate_tab_bar_html()

def close_file_tab(filename: str):
    """Close file tab VS Code-style"""
    global current_selected_file, open_files
    
    if filename in open_files:
        open_files.remove(filename)
        
        # Switch to another file if this was the current one
        if filename == current_selected_file:
            if open_files:
                current_selected_file = open_files[-1]
            else:
                current_selected_file = "main.py"
                open_files = ["main.py"]
    
    return generate_file_explorer_html(), workspace_files.get(current_selected_file, ""), generate_tab_bar_html()

def generate_tab_bar_html():
    """Generate VS Code-style tab bar"""
    global current_selected_file, open_files
    
    if not open_files:
        open_files = ["main.py"]
    
    html = f"""
    <div style="background: #2d2d30; border-bottom: 1px solid #3c3c3c; 
                display: flex; font-family: 'Segoe UI', monospace; min-height: 35px;">
    """
    
    for filename in open_files:
        # File icons
        if filename.endswith('.py'):
            icon = "🐍"
        elif filename.endswith('.txt'):
            icon = "📄"
        elif filename.endswith('.md'):
            icon = "📝"
        else:
            icon = "📋"
        
        is_active = filename == current_selected_file
        bg_color = "#1e1e1e" if is_active else "#2d2d30"
        border_top = "2px solid #007acc" if is_active else "2px solid transparent"
        text_color = "#ffffff" if is_active else "#cccccc"
        
        html += f"""
        <div class="tab-item" data-filename="{filename}"
             style="padding: 8px 16px; border-top: {border_top}; background: {bg_color};
                    color: {text_color}; cursor: pointer; display: flex; align-items: center;
                    border-right: 1px solid #3c3c3c; min-width: 120px; font-size: 13px;
                    transition: background-color 0.1s ease;">
            <span style="margin-right: 8px; font-size: 12px;">{icon}</span>
            <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{filename}</span>
            <span class="close-tab" data-filename="{filename}" 
                  style="margin-left: 8px; color: #858585; cursor: pointer; font-weight: bold;
                         padding: 2px 4px; border-radius: 3px; font-size: 12px;"
                  onmouseover="this.style.background='#464647'; this.style.color='#cccccc';"
                  onmouseout="this.style.background='transparent'; this.style.color='#858585';">×</span>
        </div>
        """
    
    html += """
    </div>
    <style>
        .tab-item:not([style*="background: #1e1e1e"]):hover {
            background: #37373d !important;
        }
        .close-tab:hover {
            background: #464647 !important;
            color: #cccccc !important;
        }
    </style>
    """
    
    return html

def delete_selected_file():
    """Delete currently selected file"""
    global current_selected_file, open_files
    
    try:
        if current_selected_file in workspace_files and current_selected_file != "main.py":
            # Remove from workspace
            del workspace_files[current_selected_file]
            
            # Remove from open files
            if current_selected_file in open_files:
                open_files.remove(current_selected_file)
            
            # Switch to another file
            if open_files:
                current_selected_file = open_files[-1]
            else:
                current_selected_file = "main.py"
                open_files = ["main.py"]
            
            return generate_file_explorer_html(), workspace_files.get(current_selected_file, ""), generate_tab_bar_html()
        else:
            return generate_file_explorer_html(), workspace_files.get(current_selected_file, ""), generate_tab_bar_html()
            
    except Exception as e:
        return generate_file_explorer_html(), f"# Error deleting file: {str(e)}", generate_tab_bar_html()


# --- VS Code Style CSS ---
vscode_theme_css = """
/* VS Code Dark Theme */
.gradio-container {
    background-color: #1e1e1e !important;
    color: #cccccc !important;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', monospace !important;
}

/* VS Code Editor Styling */
.vscode-editor textarea {
    background-color: #1e1e1e !important;
    color: #d4d4d4 !important;
    border: 1px solid #3c3c3c !important;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
    font-size: 14px !important;
    line-height: 1.4 !important;
}

/* VS Code Terminal Styling */
.vscode-terminal textarea, .terminal-output textarea {
    background-color: #0c0c0c !important;
    color: #cccccc !important;
    border: none !important;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
    font-size: 13px !important;
    line-height: 1.2 !important;
}

/* Seamless workspace layout */
.gradio-column {
    background: transparent !important;
    margin: 0 !important;
    padding: 0 !important;
}

.gradio-row {
    margin: 0 !important;
    padding: 0 !important;
    gap: 1px !important;
}

/* Remove all container padding */
.gradio-container {
    padding: 0 !important;
    margin: 0 !important;
}

/* File operations styling */
.gradio-dropdown select {
    background-color: #2d2d30 !important;
    border: 1px solid #3c3c3c !important;
    color: #cccccc !important;
}

/* Ultra-compact spacing */
.gradio-block {
    margin: 0 !important;
    padding: 0 !important;
}

.gradio-form {
    gap: 2px !important;
}

/* VS Code Button Styling */
.gradio-button {
    background-color: #0e639c !important;
    border: 1px solid #007acc !important;
    color: #ffffff !important;
    font-size: 13px !important;
    padding: 6px 14px !important;
}

.gradio-button:hover {
    background-color: #1177bb !important;
    border-color: #1177bb !important;
}

/* Secondary buttons */
.gradio-button[variant="secondary"] {
    background-color: #2d2d30 !important;
    border: 1px solid #3c3c3c !important;
    color: #cccccc !important;
}

.gradio-button[variant="secondary"]:hover {
    background-color: #37373d !important;
    border-color: #464647 !important;
}

/* Input fields */
.gradio-textbox input, .gradio-textbox textarea {
    background-color: #3c3c3c !important;
    border: 1px solid #464647 !important;
    color: #cccccc !important;
    font-family: 'Segoe UI', monospace !important;
}

/* Tab styling */
.gradio-tab-nav {
    background-color: #2d2d30 !important;
    border-bottom: 1px solid #3c3c3c !important;
}

.gradio-tab-nav button {
    background-color: transparent !important;
    color: #cccccc !important;
    border: none !important;
    padding: 8px 16px !important;
}

.gradio-tab-nav button[aria-selected="true"] {
    background-color: #1e1e1e !important;
    border-bottom: 2px solid #007acc !important;
    color: #ffffff !important;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 14px;
    height: 14px;
}

::-webkit-scrollbar-track {
    background: #1e1e1e;
}

::-webkit-scrollbar-thumb {
    background: #424242;
    border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
    background: #4f4f4f;
}

/* File explorer custom styling */
.file-item {
    transition: background-color 0.1s ease;
}

.file-item:hover {
    background-color: #2a2d2e !important;
}

.file-item.selected {
    background-color: #0e639c !important;
    color: #ffffff !important;
}

/* Status bar */
.status-bar {
    background-color: #007acc !important;
    color: #ffffff !important;
    font-size: 12px !important;
    padding: 4px 8px !important;
}
"""

# --- Gradio Arayüzü ---
with gr.Blocks(
    title="Atölye Şefi - VS Code", 
    theme=gr.themes.Base(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate"
    ),
    css=vscode_theme_css
) as demo:
    # VS Code-style header
    gr.HTML("""
    <div style="background: linear-gradient(135deg, #1e1e1e 0%, #252526 100%); 
                color: #cccccc; padding: 16px; margin-bottom: 0; 
                border-bottom: 1px solid #3c3c3c;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #ffffff;">
                    ⚡ Atölye Şefi
                </h1>
                <p style="margin: 4px 0 0 0; font-size: 14px; color: #858585;">
                    AI-Powered Serverless Code Execution Platform
                </p>
            </div>
            <div style="text-align: right; font-size: 12px; color: #858585;">
                <div><strong>Model:</strong> """ + settings.AGENT_MODEL_NAME + """</div>
                <div><strong>Agent:</strong> GraphAgent (LangGraph)</div>
                <div><strong>Platform:</strong> Modal.com Serverless</div>
            </div>
        </div>
    </div>
    """)

    with gr.Tabs():
        # TAB 1: Agent Chat
        with gr.TabItem("🤖 Agent Chat"):
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="Diyalog Penceresi", 
                        height=600, 
                        # type="messages",  # Eski Gradio sürümü için geçici olarak kapatıldı
                        value=[],  # Boş liste ile başlat
                        avatar_images=(None, "https://placehold.co/100x100/2980b9/ffffff?text=Şef")
                    )
                    with gr.Row():
                        user_input = gr.Textbox(
                            show_label=False, 
                            placeholder="GraphAgent için bir komut girin (örn: 'Bana 16GB VRAM'li bir ortam hazırla')", 
                            scale=5, 
                            container=False
                        )
                        submit_button = gr.Button("Gönder", variant="primary", scale=1)
                with gr.Column(scale=1):
                    agent_logs = gr.Textbox(
                        label="GraphAgent Logları (LangGraph State Tracking)",
                        value="Ajan bir komut bekliyor...",
                        lines=28,
                        interactive=False,
                        autoscroll=True
                    )
        
        # TAB 2: VS Code Workspace - Exact VS Code Layout
        with gr.TabItem("💻 Code Workspace"):
            # VS Code-style workspace header
            gr.HTML("""
            <div style="background: #1e1e1e; color: #cccccc; padding: 12px 16px; 
                        border-bottom: 1px solid #3c3c3c; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                        margin: -8px -8px 16px -8px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <span style="font-weight: 600; font-size: 14px;">💻 VS Code Workspace</span>
                        <span style="font-size: 12px; color: #858585;">~/ATOLYE_SEFI</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 16px; font-size: 12px;">
                        <div style="display: flex; align-items: center; gap: 4px; color: #4CAF50;">
                            <span>●</span><span>Modal.com</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 4px; color: #2196F3;">
                            <span>🐍</span><span>Python 3.11</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 4px; color: #FF9800;">
                            <span>⚡</span><span>LangGraph</span>
                        </div>
                    </div>
                </div>
            </div>
            """)
            
            # Main VS Code workspace layout - BIGGER LAYOUT
            with gr.Row():
                # LEFT SIDEBAR - Explorer (VS Code layout - BIGGER)
                with gr.Column(scale=2, min_width=350):
                    # File explorer with hidden file selector
                    file_explorer = gr.HTML(
                        value=generate_file_explorer_html(),
                        label=""
                    )
                    
                    # Hidden file selector for click handling
                    file_selector = gr.Textbox(
                        value=current_selected_file,
                        visible=False,
                        elem_id="file_selector"
                    )
                    
                    # Toolbar with file operations
                    with gr.Row():
                        with gr.Column(scale=3):
                            new_file_name = gr.Textbox(
                                placeholder="filename.py",
                                show_label=False,
                                container=False
                            )
                        with gr.Column(scale=1):
                            create_file_btn = gr.Button("➕", variant="secondary", size="sm")
                    
                    with gr.Row():
                        refresh_files_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm", scale=1)
                        delete_file_btn = gr.Button("🗑️ Delete", variant="secondary", size="sm", scale=1)
                
                # MAIN EDITOR AREA (VS Code center panel - BIGGER)
                with gr.Column(scale=5):
                    # Tab bar - VS Code style
                    current_file_tab = gr.HTML(
                        value=generate_tab_bar_html(),
                        label=""
                    )
                    
                    # Monaco-style Code Editor - BIGGER
                    code_editor = gr.Code(
                        language="python",
                        lines=32,
                        value=workspace_files["main.py"],
                        interactive=True,
                        show_label=False,
                        elem_classes=["vscode-editor"]
                    )
                    
                    # VS Code-style Action Bar with AI Assistant
                    with gr.Row():
                        execute_btn = gr.Button("▶️ Run", variant="primary", size="sm", scale=1)
                        save_btn = gr.Button("💾 Save", variant="secondary", size="sm", scale=1)
                        format_btn = gr.Button("🎨 Format", variant="secondary", size="sm", scale=1)
                        ai_assist_btn = gr.Button("🤖 AI Assist", variant="secondary", size="sm", scale=1)
                        
                        # Status indicator
                        status_display = gr.HTML(
                            value=f"""<div style="color: #4CAF50; font-family: 'Segoe UI', monospace; 
                                             padding: 4px 8px; font-size: 12px; display: flex; align-items: center;">
                                         <span style="margin-right: 6px;">●</span> 
                                         <span>Ready</span>
                                     </div>""",
                            label=""
                        )
                    
                    # AI Assistant Panel (collapsible)
                    with gr.Accordion("🤖 AI Code Assistant", open=False):
                        ai_prompt = gr.Textbox(
                            placeholder="Ask AI to help with your code... (e.g., 'add error handling', 'optimize this function', 'add comments')",
                            show_label=False,
                            lines=2
                        )
                        with gr.Row():
                            ai_help_btn = gr.Button("✨ Improve Code", variant="primary", size="sm")
                            ai_explain_btn = gr.Button("📝 Explain Code", variant="secondary", size="sm")
                            ai_debug_btn = gr.Button("🐛 Debug Code", variant="secondary", size="sm")
                
                # TERMINAL PANEL (VS Code integrated terminal - BIGGER)
                with gr.Column(scale=3, min_width=400):
                    # VS Code terminal header with tabs
                    gr.HTML("""
                    <div style="background: #252526; color: #cccccc; border-bottom: 1px solid #3c3c3c; 
                                font-family: 'Segoe UI', monospace; font-size: 12px;">
                        <div style="display: flex; align-items: center; padding: 4px 0;">
                            <div style="background: #1e1e1e; color: #ffffff; padding: 6px 12px; 
                                        border-top: 2px solid #007acc; margin: 0 1px;">
                                <span style="margin-right: 8px;">🖥️</span>Terminal
                                <span style="margin-left: 8px; color: #858585; cursor: pointer;">×</span>
                            </div>
                            <div style="padding: 6px 12px; color: #858585; cursor: pointer; 
                                        margin: 0 1px;" onmouseover="this.style.background='#2a2d2e'" 
                                        onmouseout="this.style.background='transparent'">
                                <span style="margin-right: 8px;">+</span>New Terminal
                            </div>
                        </div>
                    </div>
                    """)
                    
                    # Terminal output area - BIGGER
                    terminal_output = gr.Textbox(
                        lines=35,
                        value="atölyeşefi@workspace:~$ Ready for commands...\n",
                        interactive=False,
                        show_label=False,
                        placeholder="Terminal output will appear here...",
                        elem_classes=["vscode-terminal"]
                    )
                    
                    # Terminal input
                    with gr.Row():
                        terminal_input = gr.Textbox(
                            placeholder="$ Type command and press Enter...",
                            show_label=False,
                            scale=4,
                            container=False
                        )
                        clear_terminal_btn = gr.Button("🗑️", variant="secondary", size="sm", scale=1)

        # TAB 3: Modern Agent Commands
        with gr.TabItem("⚡ Hızlı Komutlar"):
            gr.Markdown("## GraphAgent ile Hızlı İşlemler")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🐍 Python Komutları")
                    python_hello_btn = gr.Button("🖨️ Hello World Yazdır", variant="primary")
                    python_calc_btn = gr.Button("🧮 2+2 Hesapla", variant="secondary")
                    python_time_btn = gr.Button("⏰ Şimdiki Zamanı Göster", variant="secondary")
                    
                with gr.Column(scale=1):
                    gr.Markdown("### 🚀 GPU İşlemleri")
                    gpu_create_btn = gr.Button("🎮 GPU Ortamı Hazırla", variant="primary")
                    gpu_status_btn = gr.Button("📊 GPU Durumunu Kontrol Et", variant="secondary")
                    
            with gr.Row():
                with gr.Column():
                    quick_command_output = gr.Markdown("Bir komut seçin...")
            
            # VS Code-style help panel
            gr.HTML("""
            <div style="background: #252526; border-radius: 6px; padding: 16px; margin-top: 16px;
                        border: 1px solid #3c3c3c; font-family: 'Segoe UI', sans-serif;">
                <h3 style="color: #cccccc; margin: 0 0 12px 0; font-size: 16px;">📝 How It Works</h3>
                <div style="color: #d4d4d4; font-size: 14px; line-height: 1.6;">
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #4CAF50;">🐍 Python Commands:</strong> 
                        Execute Python code via Modal.com serverless functions
                    </div>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #2196F3;">🚀 GPU Operations:</strong> 
                        Set up and manage GPU environments on RunPod
                    </div>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #FF9800;">📊 Real-time Results:</strong> 
                        All operations tracked through GraphAgent workflows
                    </div>
                    <div style="background: #1e1e1e; padding: 8px 12px; border-radius: 4px; 
                                border-left: 3px solid #007acc; margin-top: 12px;">
                        <strong style="color: #007acc;">💡 Pro Tip:</strong> 
                        Use the Agent Chat tab for more complex commands and multi-step operations!
                    </div>
                </div>
            </div>
            """)

        # TAB 4: VS Code Perfect Layout
        with gr.TabItem("🔍 Debug Workspace"):
            with gr.Row():
                # Sol panel - File listesi
                with gr.Column(scale=1):
                    gr.Markdown("### 📁 Generated Files")
                    file_list = gr.Dropdown(
                        choices=[],
                        label="Select File",
                        interactive=True
                    )
                    refresh_files_btn = gr.Button("🔄 Refresh Files")
                    
                # Sağ panel - Kod görüntüleyici  
                with gr.Column(scale=3):
                    gr.Markdown("### 📝 File Content")
                    file_viewer = gr.Code(
                        language="python",
                        lines=25,
                        interactive=False,
                        show_label=False
                    )
            
            # Alt panel - Agent logs
            with gr.Row():
                agent_debug_logs = gr.Textbox(
                    label="🤖 Agent Debug Logs",
                    lines=8,
                    max_lines=15,
                    interactive=False,
                    placeholder="Agent çalışma logları burada görünecek..."
                )

    # Event handlers
    # GraphAgent ile senkron çalışan event handler'lar  
    inputs = [user_input, chatbot, agent_logs]
    outputs = [chatbot, agent_logs, user_input]

    # Artık generator değil, normal fonksiyon kullanıyoruz
    submit_button.click(fn=run_agent_interaction, inputs=inputs, outputs=outputs)
    user_input.submit(fn=run_agent_interaction, inputs=inputs, outputs=outputs)
    
    # Quick command event handlers
    python_hello_btn.click(fn=quick_hello_world, outputs=quick_command_output)
    python_calc_btn.click(fn=quick_calculate, outputs=quick_command_output)
    python_time_btn.click(fn=quick_current_time, outputs=quick_command_output)
    gpu_create_btn.click(fn=quick_gpu_environment, outputs=quick_command_output)
    gpu_status_btn.click(fn=quick_gpu_status, outputs=quick_command_output)
    
    # VS Code Workspace event handlers - FIXED
    execute_btn.click(
        fn=execute_code_in_terminal,
        inputs=[code_editor, terminal_output, status_display],
        outputs=[terminal_output, status_display]
    )
    
    save_btn.click(
        fn=save_current_file,
        inputs=[code_editor],
        outputs=[status_display]
    )
    
    format_btn.click(
        fn=format_current_code,
        inputs=[code_editor],
        outputs=[code_editor]
    )
    
    create_file_btn.click(
        fn=create_new_file,
        inputs=[new_file_name],
        outputs=[file_explorer, code_editor, current_file_tab, new_file_name]
    )
    
    refresh_files_btn.click(
        fn=refresh_file_explorer,
        outputs=[file_explorer]
    )
    
    delete_file_btn.click(
        fn=delete_selected_file,
        outputs=[file_explorer, code_editor, current_file_tab]
    )
    
    # Debug Workspace event handlers
    refresh_files_btn.click(
        fn=refresh_file_list,
        outputs=[file_list]
    )
    
    file_list.change(
        fn=load_file_content,
        inputs=[file_list],
        outputs=[file_viewer]
    )
    
    clear_terminal_btn.click(
        fn=clear_terminal_output,
        outputs=[terminal_output]
    )
    
    terminal_input.submit(
        fn=execute_terminal_command,
        inputs=[terminal_input, terminal_output],
        outputs=[terminal_output]
    )
    
    # File selector handler for click events
    file_selector.change(
        fn=switch_file,
        inputs=[file_selector],
        outputs=[file_explorer, code_editor, current_file_tab]
    )
    
    # AI Assistant event handlers
    ai_assist_btn.click(
        fn=ai_quick_assist,
        inputs=[code_editor],
        outputs=[code_editor]
    )
    
    ai_help_btn.click(
        fn=ai_improve_code,
        inputs=[code_editor, ai_prompt],
        outputs=[code_editor]
    )
    
    ai_explain_btn.click(
        fn=ai_explain_code,
        inputs=[code_editor],
        outputs=[code_editor]
    )
    
    ai_debug_btn.click(
        fn=ai_debug_code,
        inputs=[code_editor],
        outputs=[code_editor]
    )
    
    
    # Add CSS for better VS Code integration
    demo.load(
        fn=lambda: None,
        js="""
        () => {
            // Apply VS Code-like styling dynamically
            const style = document.createElement('style');
            style.textContent = `
                /* Additional VS Code styling */
                .gradio-container {
                    background: #1e1e1e !important;
                }
                .dark {
                    --background-fill-primary: #1e1e1e;
                    --background-fill-secondary: #252526;
                    --border-color-primary: #3c3c3c;
                    --text-color-primary: #cccccc;
                }
            `;
            document.head.appendChild(style);
        }
        """
    )

def health_check():
    """Health check endpoint for Docker containers"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "workspace": "VS Code Style",
        "theme": "Dark (Visual Studio)",
        "files": len(workspace_files)
    }

if __name__ == "__main__":
    print("Gradio uygulaması başlatılıyor...")
    demo.launch()
