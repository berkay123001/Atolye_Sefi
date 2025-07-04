# agents/graph_agent.py

import sys
import os
import operator
from typing import TypedDict, Annotated, List

# Projenin ana dizinini Python'un yoluna ekliyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# --- LangChain ve LangGraph Kütüphaneleri ---
from langgraph.graph import StateGraph, END
from langchain_core.agents import AgentFinish
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain_groq import ChatGroq

# --- Proje Bileşenleri ---
from config import settings
from tools.architectural_tools import decide_architecture
# NİHAİ DÜZELTME: Henüz eklemediğimiz 'start_task_on_pod' import'unu kaldırıyoruz.
# Ajanın alet çantası, sadece mevcut ve çalışan araçları içermelidir.
from tools.operational_tools import find_and_prepare_gpu


# 1. Adım: Ajanın "Beyaz Tahtası" (State)
# NİHAİ DÜZELTME: State'i, sadece gerekli olanları içerecek şekilde basitleştiriyoruz.
class AgentState(TypedDict):
    input: str
    intermediate_steps: Annotated[list, operator.add]
    result: str


# 2. Adım: Yeni Proje Yöneticisi Sınıfı
class GraphAgent:
    """
    LangGraph kullanarak, karmaşık görevleri adım adım, koşullu bir mantıkla
    yürütebilen gelişmiş proje yöneticisi ajanı.
    """
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name=settings.AGENT_MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY
        )
        # NİHAİ DÜZELTME: Alet çantasını, şu anda mevcut olan araçlarla güncelliyoruz.
        self.tools = [decide_architecture, find_and_prepare_gpu]
        
        # Chat history gerektirmeyen standart ReAct prompt'unu kullanıyoruz
        prompt = hub.pull("hwchase17/react")
        agent_runnable = create_react_agent(self.llm, self.tools, prompt)
        # NİHAİ DÜZELTME: AgentExecutor'a artık hafıza vermiyoruz, çünkü hafızayı
        # LangGraph'ın kendisi yönetecek.
        self.tool_executor = AgentExecutor(agent=agent_runnable, tools=self.tools, verbose=True)
        
        self.graph = self.build_graph()
        print("GraphAgent ve iş akışı başarıyla oluşturuldu.")

    def agent_node(self, state: AgentState) -> dict:
        """
        Mevcut duruma göre, bir sonraki adımı düşünür ve uygun aracı çalıştırır.
        """
        print("\n--- DÜĞÜM: DÜŞÜN VE UYGULA ---")
        
        # AgentExecutor'a sadece input gönderiyoruz
        # intermediate_steps LangGraph tarafından yönetiliyor
        agent_input = {"input": state["input"]}
        
        try:
            response = self.tool_executor.invoke(agent_input)
            
            # AgentExecutor her zaman bir dict döndürür
            if "output" in response:
                # Ajan işini bitirdi, nihai sonucu dön
                return {"result": response["output"]}
            else:
                # Bu durumda bir hata var, varsayılan bir sonuç dön
                return {"result": "Ajan bir sonuç üretemedi."}
                
        except Exception as e:
            print(f"Agent node hatası: {e}")
            return {"result": f"Hata oluştu: {str(e)}"}
    
    def should_continue(self, state: AgentState) -> str:
        """
        Ajanın durumuna bakarak görevin bitip bitmediğine karar verir.
        """
        print("\n--- KARAR ANI ---")
        
        # Eğer bir sonuç varsa, görev tamamlanmış demektir
        if "result" in state and state["result"]:
            print("Karar: Görev tamamlandı.")
            return "end"
        else:
            print("Karar: Göreve devam et.")
            return "continue"

    def build_graph(self):
        """
        Ajanın "akış şeması"nı (grafiğini) oluşturur.
        """
        workflow = StateGraph(AgentState)
        
        # NİHAİ DÜZELTME: Artık karmaşık planlama adımı yok, doğrudan aksiyona geçiyoruz.
        workflow.add_node("agent", self.agent_node)
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "agent",
                "end": END
            }
        )

        return workflow.compile()

    def run(self, query: str):
        """
        Verilen bir görevle iş akışını başlatır.
        """
        initial_state = {"input": query, "intermediate_steps": []}
        final_state = self.graph.invoke(initial_state, {"recursion_limit": 15})
        return final_state


# --- Test Bloğu ---
if __name__ == '__main__':
    print("--- Nihai ve Onarılmış GraphAgent Testi ---")
    
    graph_agent = GraphAgent()
    
    test_query = (
        "Bana en az 16GB VRAM'i olan bir ortam bul ve kur."
    )
    
    result_state = graph_agent.run(test_query)
    
    print("\n\n--- GÖREV TAMAMLANDI ---")
    print("Nihai Ajan Durumu (Hafızası):")
    print(result_state)

