# agents/chief_agent.py

import sys
import os
import threading
from queue import Queue
from typing import List, Any

# LangChain Kütüphaneleri
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain import hub

# Proje Bileşenleri
try:
    from config import settings
    # Ajanın kullanacağı son ve en akıllı araçları import ediyoruz
    from tools.architectural_tools import decide_architecture
    from tools.operational_tools import find_and_prepare_gpu 
    from tools.callback_handlers import StreamingGradioCallbackHandler
    print("Ajan için yapılandırma ve Usta Araçlar başarıyla yüklendi.")
except ImportError as e:
    print(f"Hata: Ajan, gerekli modülleri bulamadı: {e}")
    sys.exit(1)


class ChiefAgent:
    """
    "Atölye Şefi" projesinin ana ajan sınıfı.
    Artık akıllı, çok adımlı görevleri yerine getirebilen "Usta" araçlara sahip.
    """
    def __init__(self):
        """
        ChiefAgent sınıfının kurucu metodu.
        """
        # Ajanın alet çantası artık çok daha basit ve güçlü.
        # Sadece yüksek seviyeli, akıllı araçları içeriyor.
        self.tools: List[Any] = [
            decide_architecture, 
            find_and_prepare_gpu
        ]

        self.llm = ChatGroq(
            temperature=0,
            model_name=settings.AGENT_MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY
        )

        self.prompt = hub.pull("hwchase17/react-chat")

        self.memory = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            return_messages=True
        )

        agent = create_react_agent(self.llm, self.tools, self.prompt)

        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True, # Terminalde detaylı loglama için
            handle_parsing_errors=True,
        )

    def run(self, user_input: str, q: Queue):
        """
        Kullanıcı girdisini alır ve ajanı AYRI BİR THREAD'de çalıştırır.
        """
        def task():
            try:
                response = self.executor.invoke(
                    {"input": user_input},
                    config={"callbacks": [StreamingGradioCallbackHandler(q)]}
                )
                q.put({"final_answer": response.get("output", "Ajan bir cevap üretemedi.")})
            except Exception as e:
                error_message = f"Ajan çalışırken bir hata oluştu: {e}"
                q.put({"error": error_message})

        # Hedef fonksiyonu çalıştıracak olan thread'i oluştur ve başlat
        thread = threading.Thread(target=task)
        thread.start()


# --- Test Bloğu ---
if __name__ == '__main__':
    print("ChiefAgent'in 'Usta Araç' ile test modu başlatılıyor...")
    chief_agent = ChiefAgent()
    
    log_queue = Queue()

    # Test Senaryosu: Ajanın yeni "Usta" aracını kullanmasını izleme
    test_input = "Bana en az 16GB VRAM'i olan bir ortam bul ve kur."
    
    chief_agent.run(user_input=test_input, q=log_queue)

    print("\n--- Ajan Arka Planda Çalışıyor ---")
    print("Loglar ve nihai cevap kuyruktan okunuyor:\n")

    while True:
        try:
            item = log_queue.get()
            
            if isinstance(item, dict) and "final_answer" in item:
                print("\n--- Nihai Cevap Alındı ---")
                print(item["final_answer"])
                break
            else:
                print(item, end="")
        except KeyboardInterrupt:
            break
