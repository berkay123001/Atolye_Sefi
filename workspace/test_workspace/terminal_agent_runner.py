#!/usr/bin/env python3
"""
🤖 TERMINAL AGENT RUNNER - Test Workspace
Workspace içinde terminal agent'ı çalıştırmak için basit runner
"""

import os
import sys
from pathlib import Path

# Proje root'unu path'e ekle
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("🤖 TERMINAL AGENT - TEST WORKSPACE RUNNER")
print("=" * 50)
print(f"📁 Test Workspace: {Path(__file__).parent}")
print(f"🔧 Project Root: {project_root}")
print(f"🐍 Python Path: {sys.executable}")

def main():
    """Terminal Agent'ı test workspace'de çalıştır"""
    
    try:
        # Import terminal agent
        from tools.terminal_agent import TerminalAgent
        
        print("✅ Terminal Agent imported successfully")
        
        # Change working directory to test workspace
        os.chdir(Path(__file__).parent)
        print(f"📁 Working directory: {os.getcwd()}")
        
        # Create agent instance
        agent = TerminalAgent()
        print("✅ Terminal Agent initialized")
        
        print("\n🚀 TERMINAL AGENT READY IN TEST WORKSPACE!")
        print("💡 Test Commands:")
        print("   • merhaba")
        print("   • create python file hello.py")
        print("   • Python dosyası oluştur test.py")
        print("   • help")
        print("   • exit")
        print("\n" + "-" * 40)
        
        # Interactive loop
        while True:
            try:
                user_input = input("\n🔥 Test> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'çıkış', 'q']:
                    print("👋 Terminal Agent kapatılıyor...")
                    break
                
                if not user_input:
                    continue
                
                print(f"🤖 Processing: {user_input}")
                
                # Process command with the agent
                response = agent.process_request(user_input)
                print(f"📝 Response:\n{response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Terminal Agent interrupted")
                break
            except Exception as e:
                print(f"❌ Error processing command: {e}")
                print("🔄 Continuing...")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the correct directory")
        print("🔧 Try: cd /home/berkayhsrt/Atolye_Sefi/workspace/test_workspace")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("🔧 Check your setup and try again")

if __name__ == "__main__":
    main()