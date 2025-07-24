#!/usr/bin/env python3
"""
Modal Cloud + Dashboard Launcher
Runs Modal serve and Dashboard in the same process
"""

import asyncio
import threading
import time
import os
import sys

def start_modal_serve():
    """Start Modal serve in background thread"""
    print("🌩️ Starting Modal serve...")
    os.chdir("/home/berkayhsrt/Atolye_Sefi")
    os.system("modal serve tools/modal_executor.py")

def start_dashboard():
    """Start Dashboard after Modal is ready"""
    print("⏳ Waiting for Modal to be ready...")
    time.sleep(15)  # Wait longer for Modal to initialize
    
    print("🚀 Starting Dashboard...")
    os.chdir("/home/berkayhsrt/Atolye_Sefi")
    
    # Import and run dashboard
    sys.path.append("/home/berkayhsrt/Atolye_Sefi")
    from app.dashboard import demo
    
    print("✅ Dashboard starting with Modal Cloud integration!")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

if __name__ == "__main__":
    print("🎯 MODAL CLOUD + DASHBOARD LAUNCHER")
    print("=" * 40)
    
    # Start Modal serve in background thread
    modal_thread = threading.Thread(target=start_modal_serve, daemon=True)
    modal_thread.start()
    
    # Start Dashboard in main thread
    start_dashboard()
