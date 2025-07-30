#!/usr/bin/env python3
"""
🧠 GRAPH AGENT RUNNER - Test Workspace
Ana GraphAgent'ı test workspace'de çalıştırmak için runner
"""

import os
import sys
from pathlib import Path

# Proje root'unu path'e ekle
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("🧠 GRAPH AGENT - TEST WORKSPACE RUNNER")
print("=" * 50)
print(f"📁 Test Workspace: {Path(__file__).parent}")
print(f"🔧 Project Root: {project_root}")

def main():
    """GraphAgent'ı test workspace'de çalıştır"""
    
    try:
        # Import Fixed GraphAgent (local version)
        from fixed_graph_agent import GraphAgent
        
        print("✅ Fixed GraphAgent imported successfully")
        
        # Change working directory to test workspace
        os.chdir(Path(__file__).parent)
        print(f"📁 Working directory: {os.getcwd()}")
        
        # Create agent instance
        agent = GraphAgent()
        print("✅ Fixed GraphAgent initialized with all tools")
        
        print("\n🚀 FIXED GRAPH AGENT READY IN TEST WORKSPACE!")
        print("💡 Test Commands:")
        print("   • merhaba (chat)")
        print("   • Python kodu yaz - hello world")
        print("   • Jedi analiz yap - import math")
        print("   • Git durumu kontrol et")
        print("   • workspace dosyalarını listele")
        print("   • help")
        print("   • exit")
        print("\n" + "-" * 40)
        
        # Interactive loop
        while True:
            try:
                user_input = input("\n🧠 Graph> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'çıkış', 'q']:
                    print("👋 Graph Agent kapatılıyor...")
                    break
                
                if not user_input:
                    continue
                
                print(f"🧠 Processing with GraphAgent: {user_input}")
                
                # Process with GraphAgent
                result = agent.run(user_input)
                response = result.get('result', 'No response')
                print(f"📝 Fixed GraphAgent Response:\n{response}")
                
                # Show plan if available
                plan = result.get('plan', [])
                if plan:
                    print(f"📋 Plan: {plan}")
                
                # Show intermediate steps if available
                steps = result.get('intermediate_steps', [])
                if steps:
                    print(f"🔧 Steps executed: {len(steps)}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Graph Agent interrupted")
                break
            except Exception as e:
                print(f"❌ Error processing command: {e}")
                print("🔄 Continuing...")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("🔧 Check your setup and try again")

if __name__ == "__main__":
    main()