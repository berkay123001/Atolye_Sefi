# agents/chief_agent.py

import sys
import os
import threading
from queue import Queue
from typing import List, Dict, Any

# --- LangChain Kütüphaneleri ---
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain import hub

# --- Proje Bileşenleri ---
try:
    from config import settings
    from tools.architectural_tools import decide_architecture
    # YENİ EKLENDİ: Canlı loglama için callback handler'ımızı import ediyoruz.
    from tools.callback_handlers import StreamingGradioCallbackHandler
    print("Ajan için yapılandırma ve tüm araçlar/handler'lar başarıyla yüklendi.")
except ImportError as e:
    print(f"Hata: Ajan, gerekli modülleri bulamadı: {e}")
    sys.exit(1)


class ChiefAgent:
    """
    "Atölye Şefi" projesinin ana ajan sınıfı.
    Artık mimari karar verme yeteneğine sahip ve düşünce sürecini
    canlı olarak aktarabiliyor.
    """
    def __init__(self):
        """
        ChiefAgent sınıfının kurucu metodu.
        """
        self.tools: List[Any] = [decide_architecture]

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
            verbose=True,
            handle_parsing_errors=True,
        )

    def run(self, user_input: str, q: Queue):
        """
        Kullanıcı girdisini alır ve ajanı AYRI BİR THREAD'de çalıştırır.
        Bu, Gradio arayüzünün donmasını engeller. Ajanın tüm adımları (loglar)
        ve nihai cevabı, verilen kuyruğa (queue) yazılır.

        Args:
            user_input (str): Kullanıcının verdiği komut.
            q (Queue): Logların ve nihai cevabın yazılacağı thread-safe kuyruk.
        """
        
        # Ajanı arka planda çalıştıracak olan hedef fonksiyon
        def task():
            try:
                # AgentExecutor'ı, logları kuyruğa yazacak olan özel
                # callback handler'ımız ile birlikte çağırıyoruz.
                response = self.executor.invoke(
                    {"input": user_input},
                    config={"callbacks": [StreamingGradioCallbackHandler(q)]}
                )
                # Ajanın nihai cevabını da ayırt edici bir anahtarla kuyruğa ekliyoruz.
                # Arayüz bu anahtarı gördüğünde cevabı Chatbot'a yazdıracak.
                q.put({"final_answer": response.get("output", "Ajan bir cevap üretemedi.")})
            except Exception as e:
                error_message = f"Ajan çalışırken bir hata oluştu: {e}"
                q.put({"error": error_message})

        # Hedef fonksiyonu çalıştıracak olan thread'i oluştur ve başlat
        thread = threading.Thread(target=task)
        thread.start()


# --- Test Bloğu ---
if __name__ == '__main__':
    print("ChiefAgent'in canlı loglama (multi-threaded) test modu başlatılıyor...")
    chief_agent = ChiefAgent()
    
    # Test için bir kuyruk oluştur
    log_queue = Queue()

    # Test sorusu
    tool_test_input = "Elimde 500 sayfalık bir hukuk metinleri külliyatı var ve bu metinleri verimli bir şekilde analiz etmem gerekiyor. Hangi AI mimarisini önerirsin?"
    
    # Ajanı arka planda çalıştır
    chief_agent.run(user_input=tool_test_input, q=log_queue)

    print("\n--- Ajan Arka Planda Çalışıyor ---")
    print("Loglar ve nihai cevap kuyruktan okunuyor:\n")

    # Kuyruktan gelen verileri anlık olarak dinle
    while True:
        try:
            item = log_queue.get() # Kuyruktan bir eleman al
            
            if isinstance(item, dict) and "final_answer" in item:
                print("\n--- Nihai Cevap Alındı ---")
                print(item["final_answer"])
                break # Nihai cevap alındığında döngüyü kır
            elif isinstance(item, dict) and "error" in item:
                print("\n--- Hata Alındı ---")
                print(item["error"])
                break
            else:
                # Gelen logları yazdır (canlı akışı simüle eder)
                print(item, end="")

        except KeyboardInterrupt:
            break
