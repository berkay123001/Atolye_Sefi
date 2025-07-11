#!/usr/bin/env python3
"""
GraphAgent'in gerçek performansını test eder.
"""

import sys
import os
sys.path.append('/home/berkayhsrt/Atolye_Sefi')

try:
    from agents.graph_agent import GraphAgent
    print('✅ GraphAgent imported successfully')
    
    agent = GraphAgent()
    print('✅ GraphAgent created successfully')
    
    # Test query
    query = 'Mevcut POD da bir Python dosyası oluştur ve içine basit bir hello world yazı'
    print(f'\n🎯 Testing query: {query}')
    
    result = agent.run(query)
    print('\n' + '='*60)
    print('FINAL RESULT:')
    print('='*60)
    print(result)
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
