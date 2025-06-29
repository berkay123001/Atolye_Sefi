# agents/chief_agent.py

import sys
import os
import threading
from queue import Queue
from typing import List, Dict, Any

# Proje ana dizinini Python yoluna ekleyerek diğer modülleri import edilebilir hale getiriyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# --- LangChain Kütüphaneleri ---
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain import hub

# --- Proje Bileşenleri ---
try:
    from config import settings
    # Ajanın kullanacağı tüm araçları import ediyoruz
    from tools.architectural_tools import decide_architecture
    # 1. YENİ DEĞİŞİKLİK: Yeni operasyonel aracı import ediyoruz.
    from tools.operational_tools import prepare_environment 
    from tools.callback_handlers import StreamingGradioCallbackHandler
    print("Ajan için yapılandırma ve tüm araçlar/handler'lar başarıyla yüklendi.")
except ImportError as e:
    print(f"Hata: Ajan, gerekli modülleri bulamadı: {e}")
    sys.exit(1)


class ChiefAgent:
    """
    "Atölye Şefi" projesinin ana ajan sınıfı.
    Artık birden fazla yeteneğe sahip ve düşünce sürecini canlı olarak aktarabiliyor.
    """
    def __init__(self):
        """
        ChiefAgent sınıfının kurucu metodu.
        """
        # 2. YENİ DEĞİŞİKLİK: Ajanın alet çantasını, her iki aracı da içerecek şekilde güncelliyoruz.
        self.tools: List[Any] = [decide_architecture, prepare_environment]

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
# Bu dosya doğrudan `python agents/chief_agent.py` komutuyla çalıştırıldığında,
# ajanın yeni araçları doğru kullanıp kullanmadığını test eder.
if __name__ == '__main__':
    print("ChiefAgent'in çoklu araç test modu başlatılıyor...")
    chief_agent = ChiefAgent()
    
    log_queue = Queue()

    # Test Senaryosu: Ajanın yeni 'prepare_environment' aracını kullanmasını tetikleme
    test_input = "Bana bir Transformer modeli için A100 GPU'lu bir ortam hazırla."
    
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
            elif isinstance(item, dict) and "error" in item:
                print("\n--- Hata Alındı ---")
                print(item["error"])
                break
            else:
                print(item, end="")
        except KeyboardInterrupt:
            break
