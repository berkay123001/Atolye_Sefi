#!/usr/bin/env python3
"""
Sıfırdan Pod oluşturup GraphAgent test scripti
"""

import sys
sys.path.append('/home/berkayhsrt/Atolye_Sefi')

print("🚀 Sıfırdan Pod Oluşturma ve Test Başlıyor...")
print("="*60)

# 1. Önce mevcut pod'ları listele
print("\n1️⃣ Mevcut Pod'ları Kontrol Ediyorum...")
try:
    import runpod_test_script
    runpod_test_script.list_all_pods()
except Exception as e:
    print(f"Pod listesi hatası: {e}")

# 2. GraphAgent ile yeni Pod oluştur
print("\n2️⃣ GraphAgent ile Yeni Pod Oluşturuyorum...")
try:
    from agents.graph_agent import GraphAgent
    
    agent = GraphAgent()
    
    # Yeni Pod oluşturma isteği
    result = agent.run("Bana yeni bir GPU Pod oluştur ve Python kod yazacağız")
    
    print("\n📋 GraphAgent Sonucu:")
    print("="*40)
    print(result.get('result', 'Sonuç bulunamadı'))
    
    # Intermediate steps'i de göster
    steps = result.get('intermediate_steps', [])
    if steps:
        print("\n🔧 Yapılan İşlemler:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step.get('step_description', 'N/A')}")
            print(f"     Tool: {step.get('tool_used', 'N/A')}")
            print(f"     Status: {step.get('status', 'N/A')}")
            if step.get('tool_used') == 'find_and_prepare_gpu':
                raw_result = step.get('result', {})
                if 'pod_id' in raw_result:
                    print(f"     🆔 Pod ID: {raw_result['pod_id']}")
                if 'jupyter_url' in raw_result:
                    print(f"     🔗 Jupyter: {raw_result['jupyter_url']}")
            print()
    
    # 3. Pod listesini tekrar kontrol et
    print("\n3️⃣ Yeni Pod Kontrolü...")
    try:
        runpod_test_script.list_all_pods()
    except Exception as e:
        print(f"Pod listesi hatası: {e}")
        
except Exception as e:
    print(f"❌ GraphAgent Hatası: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🏁 Test Tamamlandı!")
