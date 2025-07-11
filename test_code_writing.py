#!/usr/bin/env python3
"""
Pod'da kod yazma test scripti
"""

import sys
sys.path.append('/home/berkayhsrt/Atolye_Sefi')

print("🐍 Pod'da Python Kod Yazma Testi")
print("="*60)

try:
    from agents.graph_agent import GraphAgent
    
    agent = GraphAgent()
    
    # Kod yazma görevi
    query = """
    Mevcut Pod'da (a3z34a02nkwlai) şunları yap:
    1. Fibonacci sayıları hesaplayan bir Python fonksiyonu yaz
    2. İlk 10 Fibonacci sayısını yazdır
    3. Sonuçları bir dosyaya kaydet
    """
    
    print(f"🎯 Görev: {query}")
    print("\n🚀 GraphAgent Çalışıyor...")
    
    result = agent.run(query)
    
    print("\n📋 GraphAgent Sonucu:")
    print("="*40)
    print(result.get('result', 'Sonuç bulunamadı'))
    
    # start_task_on_pod adımlarını bul ve Jupyter kodlarını göster
    steps = result.get('intermediate_steps', [])
    print("\n🔧 Hazırlanan Jupyter Kodları:")
    print("="*40)
    
    jupyter_codes = []
    for step in steps:
        if step.get('tool_used') == 'start_task_on_pod':
            raw_result = step.get('raw_result', {})
            if 'jupyter_code' in raw_result:
                jupyter_codes.append(raw_result['jupyter_code'])
                print(f"📝 Kod {len(jupyter_codes)}:")
                print(raw_result['jupyter_code'])
                print("-" * 20)
    
    if jupyter_codes:
        print(f"\n✨ Toplam {len(jupyter_codes)} kod parçası hazırlandı!")
        print("🔗 Jupyter URL: https://a3z34a02nkwlai-8888.proxy.runpod.net/lab/")
        print("🔐 Şifre: atolye123")
        print("\n💡 Bu kodları Jupyter'da çalıştırabilirsiniz!")
    else:
        print("⚠️ Jupyter kodu bulunamadı.")
        
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🏁 Kod Yazma Testi Tamamlandı!")
