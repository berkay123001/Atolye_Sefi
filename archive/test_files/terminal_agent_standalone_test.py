#!/usr/bin/env python3
"""
🤖 TERMINAL AGENT - Standalone Test Version
Başka IDE'de çalıştırmak için bağımsız test versiyonu

KULLANIM:
1. Bu dosyayı başka IDE'ye kopyala
2. Gerekli dependencies'leri kur: pip install groq pydantic langchain
3. .env dosyasını kopyala (GROQ_API_KEY)
4. python terminal_agent_standalone_test.py çalıştır
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Environment setup
print("🔧 Setting up Terminal Agent Test Environment...")
print("=" * 60)

# Check dependencies
required_packages = ['groq', 'pydantic', 'langchain']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package}: Available")
    except ImportError:
        missing_packages.append(package)
        print(f"❌ {package}: Missing")

if missing_packages:
    print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
    print(f"💡 Install with: pip install {' '.join(missing_packages)}")
    print("\n🔄 Do you want to continue anyway? (y/n): ", end="")
    if input().lower() not in ['y', 'yes', 'evet']:
        print("👋 Exiting...")
        sys.exit(1)

# Check environment variables
print(f"\n🔐 Environment Check:")
if os.getenv('GROQ_API_KEY'):
    print("✅ GROQ_API_KEY: Set")
else:
    print("❌ GROQ_API_KEY: Missing")
    api_key = input("🔑 Enter your GROQ API key (or press Enter to skip): ").strip()
    if api_key:
        os.environ['GROQ_API_KEY'] = api_key
        print("✅ API key set for this session")

print("\n🚀 Starting Terminal Agent...")
print("=" * 60)

# Import and run terminal agent
try:
    # Try to import from current project structure
    from tools.terminal_agent import TerminalAgent
    
    print("✅ Successfully imported TerminalAgent")
    
    # Create and run agent
    agent = TerminalAgent()
    
    print("\n🤖 Terminal Agent Ready!")
    print("💡 Try these commands:")
    print("   - merhaba")
    print("   - create python file hello.py")
    print("   - help")
    print("   - exit")
    print("\n" + "-" * 40)
    
    # Interactive loop
    while True:
        try:
            user_input = input("\n🔥 Terminal> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'çıkış']:
                print("👋 Terminal Agent kapatılıyor...")
                break
            
            if not user_input:
                continue
                
            print(f"\n🤖 Processing: {user_input}")
            response = agent.process_command(user_input)
            print(f"📝 Response: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Terminal Agent interrupted")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("🔄 Continuing...")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\n🔧 Alternative: Running with subprocess...")
    
    # Alternative: Run as subprocess
    import subprocess
    
    try:
        # Find terminal_agent.py
        terminal_agent_path = None
        possible_paths = [
            Path("tools/terminal_agent.py"),
            Path("../tools/terminal_agent.py"),
            Path("./terminal_agent.py")
        ]
        
        for path in possible_paths:
            if path.exists():
                terminal_agent_path = path
                break
        
        if terminal_agent_path:
            print(f"🔍 Found terminal agent at: {terminal_agent_path}")
            subprocess.run([sys.executable, str(terminal_agent_path)])
        else:
            print("❌ terminal_agent.py not found")
            print("💡 Copy the terminal_agent.py file to the same directory")
            
    except Exception as e:
        print(f"❌ Subprocess failed: {e}")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("🔧 Check your setup and try again")

print("\n✅ Terminal Agent Test Complete")