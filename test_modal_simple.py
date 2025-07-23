#!/usr/bin/env python3
"""
Simple Modal.com test script to verify integration
"""

import os
import sys
sys.path.append('/home/berkayhsrt/Atolye_Sefi')

def test_modal_basic():
    """Test basic Modal functionality"""
    print("🧪 Testing Modal.com integration...")
    
    # Test 1: Simple code execution
    test_code = """
print("Hello from Modal serverless!")
import sys
print(f"Python version: {sys.version}")
print("✅ Modal execution successful!")
"""
    
    try:
        # Import our executor
        from tools.modal_executor import modal_executor
        
        print("🚀 Executing Python code on Modal...")
        result = modal_executor.execute_python_code(test_code, use_gpu=False)
        
        print(f"Status: {result['status']}")
        print(f"Output: {result.get('output', '')}")
        print(f"Error: {result.get('error', 'None')}")
        
        if result["status"] == "success":
            print("✅ Modal integration test PASSED!")
            return True
        else:
            print("❌ Modal integration test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graph_agent():
    """Test GraphAgent with Modal integration"""
    print("\n🧪 Testing GraphAgent with Modal...")
    
    try:
        from agents.graph_agent import GraphAgent
        
        agent = GraphAgent()
        print("✅ GraphAgent created successfully")
        
        # Simple test query
        result = agent.run("merhaba")
        print(f"Result: {result.get('result', '')[:100]}...")
        
        print("✅ GraphAgent test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ GraphAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔥 SSH → Modal Migration Test Suite")
    print("=" * 50)
    
    # Run tests
    modal_test = test_modal_basic()
    graph_test = test_graph_agent()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Modal Integration: {'✅ PASS' if modal_test else '❌ FAIL'}")
    print(f"GraphAgent Integration: {'✅ PASS' if graph_test else '❌ FAIL'}")
    
    if modal_test and graph_test:
        print("\n🎉 All tests PASSED! SSH → Modal migration successful!")
    else:
        print("\n❌ Some tests failed. Check the logs above.")