#!/usr/bin/env python3
"""
🔧 DOCKER DIRECT TEST
Docker Python client'ının durumunu test edelim
"""

import docker
import os

def main():
    print("🔧 DOCKER DIRECT TEST")
    print("=" * 30)
    
    # Docker environment bilgilerini kontrol et
    print("📋 Docker Environment Variables:")
    docker_vars = [var for var in os.environ.keys() if 'DOCKER' in var.upper()]
    if docker_vars:
        for var in docker_vars:
            print(f"  {var} = {os.environ[var]}")
    else:
        print("  No Docker environment variables found")
    
    print("\n🔍 Docker socket paths:")
    possible_sockets = [
        "/var/run/docker.sock",
        "/home/berkayhsrt/.docker/desktop/docker-cli.sock",
        "unix:///var/run/docker.sock"
    ]
    
    for socket_path in possible_sockets:
        if socket_path.startswith("/"):
            exists = os.path.exists(socket_path)
            print(f"  {socket_path}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
        else:
            print(f"  {socket_path}: URI format")
    
    print("\n🐳 Docker Client Tests:")
    
    # Test 1: Default client
    try:
        print("  Test 1: docker.from_env()")
        client = docker.from_env()
        version = client.version()
        print(f"    ✅ Success: Docker {version.get('Version', 'Unknown')}")
        
        # Container test
        print("  Test 2: Run hello-world container")
        result = client.containers.run("hello-world", remove=True, capture_output=True, text=True)
        print(f"    ✅ Container test successful")
        print(f"    Output: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)