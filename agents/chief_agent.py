# agents/chief_agent.py

import sys
import os
from typing import List, Dict, Any

# Proje ana dizinini Python yoluna ekleyerek config.py'yi import edilebilir hale getiriyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# --- LangChain Kütüphaneleri ---
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain import hub

# --- Proje Ayarları ---
try:
    from config import settings
    print("Ajan için yapılandırma başarıyla yüklendi.")
except ImportError:
    print("Hata: Ajan, config.py dosyasını bulamadı.")
    sys.exit(1) # Yapılandırma olmadan ajan çalışamaz.


class ChiefAgent:
    """
    "Atölye Şefi" projesinin ana ajan sınıfı.

    Bu sınıf, LLM'i, hafızayı, araçları (tools) ve ajan mantığını (ReAct)
    bir araya getirerek bir AgentExecutor oluşturur ve yönetir.
    """
    def __init__(self):
        """
        ChiefAgent sınıfının kurucu metodu.
        Ajanı çalıştırmak için gerekli tüm bileşenleri başlatır.
        """
        # 1. Araçlar (Tools) - Faz 1: Simülasyon
        # Şimdilik boş bir liste. Gelecekte buraya RunPod'u yöneten,
        # dosya okuyan vb. sahte veya gerçek araçlarımızı ekleyeceğiz.
        self.tools: List[Any] = []

        # 2. LLM (Büyük Dil Modeli) - Ajanın Beyni
        # Groq API kullanarak yüksek hızlı bir LLM oluşturuyoruz.
        # 'temperature=0' ayarı, ajanın daha deterministik ve öngörülebilir
        # cevaplar vermesini sağlar, bu da otomasyon görevleri için idealdir.
        self.llm = ChatGroq(
            temperature=0,
            model_name=settings.AGENT_MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY
        )

        # 3. Prompt (Sistem Talimatı)
        # LangChain Hub'dan, ReAct ajanları için özel olarak tasarlanmış,
        # kanıtlanmış bir prompt şablonu çekiyoruz. Bu şablon, ajanın
        # "Düşünce -> Eylem -> Gözlem" döngüsünü nasıl kullanacağını tanımlar.
        # Not: LangChain'in kendi prompt'u, config dosyamızdaki sistem talimatını
        # doğrudan kullanmaz. Onu daha sonra entegre edeceğiz.
        self.prompt = hub.pull("hwchase17/react-chat")

        # 4. Hafıza (Memory)
        # Ajanın geçmiş konuşmaları hatırlamasını sağlar.
        # k=10, son 10 konuşma adımını (kullanıcı + ajan) hafızada tutar.
        # `memory_key="chat_history"`, prompt şablonuyla uyumlu olmalıdır.
        self.memory = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            return_messages=True # ReAct prompt'u mesaj nesneleriyle çalışır.
        )

        # 5. Ajan Mantığı (Agent Logic)
        # LLM, araçlar ve prompt'u birleştirerek temel ajan mantığını oluşturur.
        # Bu fonksiyon, LLM'in hangi aracı ne zaman kullanacağına karar vermesini sağlar.
        agent = create_react_agent(self.llm, self.tools, self.prompt)

        # 6. Ajan Yürütücüsü (Agent Executor)
        # Ajan mantığını, araçları ve hafızayı bir araya getiren son katmandır.
        # Gelen istekleri alır, ajanı adım adım çalıştırır, araçları tetikler
        # ve nihai cevabı üretir. `verbose=True` loglamayı kolaylaştırır.
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True, # Geliştirme sırasında ajanın düşüncelerini görmek için
            handle_parsing_errors=True, # LLM'in format hatalarını tolere et
        )

    def run(self, user_input: str, chat_history: List[Dict] = None) -> str:
        """
        Kullanıcı girdisini alır ve ajanı çalıştırarak bir cevap üretir.

        Args:
            user_input (str): Kullanıcının verdiği komut.
            chat_history (List[Dict], optional): Mevcut sohbet geçmişi.
                                                Genellikle hafıza tarafından yönetilir.

        Returns:
            str: Ajanın ürettiği nihai cevap.
        """
        print(f"Ajan çalıştırılıyor, Girdi: '{user_input}'")
        
        # AgentExecutor'ı çağırıyoruz. Girdi olarak bir sözlük alır.
        # Bu sözlükteki anahtarlar ('input', 'chat_history') prompt şablonu
        # tarafından beklenen değişken isimleriyle eşleşmelidir.
        response = self.executor.invoke({
            "input": user_input,
            # Hafıza bu geçmişi otomatik olarak yönetecektir.
            "chat_history": chat_history or [] 
        })
        
        # `invoke` metodu, birçok bilgi içeren bir sözlük döndürür.
        # Bizim için önemli olan, ajanın son kullanıcıya verdiği 'output'tur.
        return response.get("output", "Ajan bir cevap üretemedi.")

# --- Test Bloğu ---
if __name__ == '__main__':
    # Bu dosya doğrudan çalıştırıldığında basit bir test yapar.
    print("ChiefAgent test modu başlatılıyor...")
    
    # Bir ajan nesnesi oluştur
    chief_agent = ChiefAgent()
    
    # Basit bir komutla ajanı çalıştır
    # Not: Ajanın henüz bir aracı olmadığı için, sadece LLM ile sohbet edecektir.
    test_input = "Merhaba, adın ne?"
    response = chief_agent.run(user_input=test_input)
    
    print("\n--- Ajan Testi Tamamlandı ---")
    print(f"Kullanıcı Sorusu: {test_input}")
    print(f"Ajan Cevabı: {response}")

    print("\nİkinci Test:")
    test_input_2 = "Sana Atölye Şefi diyeceğim."
    response_2 = chief_agent.run(user_input=test_input_2)
    print(f"Kullanıcı Sorusu: {test_input_2}")
    print(f"Ajan Cevabı: {response_2}")
