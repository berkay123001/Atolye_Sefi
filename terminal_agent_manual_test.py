#!/usr/bin/env python3
"""
Terminal Agent Manual Test - Real Agent Testing
Gerçek terminal agent ile manual test yapalım
"""

import subprocess
import os
import time
from pathlib import Path

def test_terminal_agent():
    """Test terminal agent with real commands"""
    
    print("🤖 Testing Terminal Agent with Real Commands...")
    print("=" * 60)
    
    # Test 1: Simple greeting
    print("\n🧪 Test 1: Greeting Test")
    print("Command: merhaba")
    
    # Test 2: File creation
    print("\n🧪 Test 2: File Creation Test")
    print("Command: create python file hello.py")
    
    # Test 3: Turkish command
    print("\n🧪 Test 3: Turkish Command Test")
    print("Command: Python dosyası oluştur")
    
    # Test 4: Complex task
    print("\n🧪 Test 4: Complex Task Test")
    print("Command: create a simple Flask app")
    
    print("\n" + "=" * 60)
    print("🚀 Ready to test! Let's run the terminal agent...")
    print("Commands to try:")
    print("1. merhaba")
    print("2. create python file hello.py")
    print("3. Python dosyası oluştur 'test.py'")
    print("4. create a simple Flask app")
    print("5. install numpy")
    print("6. help")
    print("7. exit")

def run_terminal_agent():
    """Run the terminal agent"""
    try:
        # Change to the tools directory where terminal_agent.py is located
        tools_dir = Path(__file__).parent / "tools"
        
        print(f"🔧 Starting Terminal Agent from: {tools_dir}")
        print("📝 Type 'exit' to quit the agent")
        print("-" * 50)
        
        # Run the terminal agent
        result = subprocess.run([
            "python", str(tools_dir / "terminal_agent.py")
        ], cwd=str(tools_dir))
        
        print("\n✅ Terminal Agent session ended")
        
    except KeyboardInterrupt:
        print("\n\n👋 Terminal Agent interrupted")
    except Exception as e:
        print(f"\n❌ Error running Terminal Agent: {e}")
        print("\n🔧 Trying alternative method...")
        
        # Alternative: run directly with python
        try:
            os.chdir("tools")
            subprocess.run(["python", "terminal_agent.py"])
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")

if __name__ == "__main__":
    test_terminal_agent()
    
    response = input("\n🚀 Run Terminal Agent now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes', 'evet', 'e']:
        run_terminal_agent()
    else:
        print("👋 Test completed. Run manually with: python tools/terminal_agent.py")