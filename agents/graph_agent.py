# agents/graph_agent.py

import sys
import os
import operator
from typing import TypedDict, Annotated, List, Dict, Any

# Projenin ana dizinini Python'un yoluna ekliyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# --- LangChain ve LangGraph Kütüphaneleri ---
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# --- Proje Bileşenleri ---
from config import settings
from tools.architectural_tools import decide_architecture
from tools.operational_tools import find_and_prepare_gpu
from tools.pod_management_tools import execute_command_on_pod, get_pod_status


# 1. Yeni "Beyaz Tahta" (AgentState) - Çok Adımlı Hafıza + Akıllı Yönlendirme
class AgentState(TypedDict):
    input: str                          # Kullanıcının orijinal görevi
    route_decision: str                 # Yönlendirme kararı: "chat" veya "task"
    plan: List[str]                     # Adımların planı (string listesi)
    executed_steps: Annotated[List[Dict], operator.add]  # Tamamlanan adımların sonuçları
    current_step_index: int             # Şu anki adım numarası
    final_result: str                   # Nihai cevap


# 2. Çok Adımlı Proje Yöneticisi Sınıfı
class GraphAgent:
    """
    LangGraph kullanarak, çok adımlı görevleri planlayan, adım adım uygulayan
    ve hafızasını koruyan gelişmiş proje yöneticisi ajanı.
    """
    def __init__(self):
        # LLM'i başlat
        self.llm = ChatGroq(
            temperature=0.1,  # Biraz yaratıcılık için artırdık
            model_name=settings.AGENT_MODEL_NAME,
            groq_api_key=settings.GROQ_API_KEY
        )
        
        # Alet çantasını sözlük olarak tanımla (kolay erişim için)
        self.tools_dict = {
            "decide_architecture": decide_architecture,
            "find_and_prepare_gpu": find_and_prepare_gpu,
            "execute_command_on_pod": execute_command_on_pod,
            "get_pod_status": get_pod_status,
            # Simülasyon aracı (gerçek implementasyon için hazır)
            "start_task_on_pod": self._simulate_task_execution
        }
        
        # Grafiği oluştur
        self.graph = self.build_graph()
        print("🧠 GraphAgent: Çok adımlı hafıza sistemi aktif!")

    def _simulate_task_execution(self, **kwargs) -> Dict:
        """
        Geçici simülasyon aracı - gerçek implementasyon gelene kadar
        """
        return {
            "status": "success",
            "message": "Task simulation completed successfully",
            "details": f"Simulated execution with parameters: {kwargs}"
        }

    # === YENİ İŞ İSTASYONU 0: AKILLI YÖNLENDİRİCİ DÜĞÜMÜ ===
    def route_query(self, state: AgentState) -> Dict:
        """
        Kullanıcının girdisini analiz eder ve "chat" mi "task" mı olduğuna karar verir.
        Bu, grafiğin "kapıdaki güvenlik görevlisi"sidir.
        """
        print("\n🚪 [YÖNLENDİRİCİ] Kullanıcı girdisi analiz ediliyor...")
        
        routing_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen, kullanıcı girdilerini kategorize eden uzman bir analiz sistemisin.
            
Görevin: Verilen girdiyi analiz edip, sadece "chat" veya "task" kelimelerinden birini döndürmek.

KURALLAR:
- Eğer girdi selamlama, sohbet, basit soru ise -> "chat" 
- Eğer girdi eylem, komut, plan gerektiriyorsa -> "task"

ÖRNEKLERİ:
- "merhaba" -> chat
- "nasılsın" -> chat  
- "GPU bul" -> task
- "model eğit" -> task
- "16GB VRAM ortam hazırla" -> task

SADECE "chat" veya "task" kelimesini döndür, başka hiçbir şey yazma!"""),
            ("user", "{input}")
        ])
        
        try:
            response = self.llm.invoke(routing_prompt.format_messages(input=state["input"]))
            decision = response.content.strip().lower()
            
            # Güvenlik kontrolü - sadece geçerli değerler
            if decision not in ["chat", "task"]:
                decision = "chat"  # Şüpheli durumlarda güvenli tarafta kal
                
            print(f"📋 Yönlendirme Kararı: '{decision}' (Girdi: '{state['input']}')")
            
            return {"route_decision": decision}
            
        except Exception as e:
            print(f"❌ Yönlendirici hatası: {e}")
            return {"route_decision": "chat"}  # Hata durumunda güvenli mod

    # === YENİ İŞ İSTASYONU 1: SOHBET DÜĞÜMÜ ===
    def chatbot_step(self, state: AgentState) -> Dict:
        """
        Basit sohbet işlemlerini halleder. Hiçbir araç kullanmaz, sadece doğal sohbet.
        """
        print("\n💬 [SOHBET DÜĞÜMÜ] Doğal sohbet cevabı oluşturuluyor...")
        
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen, Atölye Şefi isimli, yardımsever ve dostane bir AI asistanısın.
            
Özelliklerin:
- MLOps ve AI konularında uzman
- Docker, GPU, model eğitimi konularında bilgili
- Sıcak ve samimi bir konuşma tarzın var
- Türkçe konuşuyorsun

Kullanıcıyla doğal bir sohbet yap. Kısa, net ve dostane cevaplar ver."""),
            ("user", "{input}")
        ])
        
        try:
            response = self.llm.invoke(chat_prompt.format_messages(input=state["input"]))
            result = response.content.strip()
            
            print(f"💭 Sohbet Cevabı: {result[:100]}...")
            
            return {"final_result": result}
            
        except Exception as e:
            print(f"❌ Sohbet hatası: {e}")
            return {"final_result": "Üzgünüm, şu anda bir sorun yaşıyorum. Tekrar dener misin?"}

    # === İŞ İSTASYONU 2: PLANLAMA DÜĞÜMÜ ===
    def plan_step(self, state: AgentState) -> Dict:
        """
        Kullanıcının görevini analiz eder ve adım adım plan oluşturur.
        """
        print("\n🎯 [PLANLAMA DÜĞÜMÜ] Görev analiz ediliyor ve plan oluşturuluyor...")
        
        planning_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen bir MLOps proje yöneticisisin. Kullanıcının görevini analiz et ve 
            adım adım bir plan oluştur. Her adım, hangi aracın çağrılacağını net olarak belirtmeli.

            Kullanılabilir araçlar:
            - decide_architecture: Mimari kararları almak için
            - find_and_prepare_gpu: GPU ortamı bulmak ve hazırlamak için  
            - execute_command_on_pod: Pod'da komut çalıştırmak için
            - get_pod_status: Pod durumunu kontrol etmek için
            - start_task_on_pod: Pod'da özel görev başlatmak için

            Planı, her satırda bir adım olacak şekilde, şu formatta yaz:
            1. [ARAÇ_ADI] açıklama
            2. [ARAÇ_ADI] açıklama
            ...

            Örnek:
            1. [find_and_prepare_gpu] 16GB VRAM'li GPU ortamı bul ve hazırla
            2. [execute_command_on_pod] Git repository'sini clone et
            3. [execute_command_on_pod] Gerekli kütüphaneleri yükle"""),
            ("user", "Görev: {task}")
        ])
        
        try:
            response = self.llm.invoke(planning_prompt.format_messages(task=state["input"]))
            plan_text = response.content
            
            # Plan metnini parse et
            plan_steps = []
            for line in plan_text.split('\n'):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") for i in range(1, 20)):
                    plan_steps.append(line)
            
            print(f"📋 Plan oluşturuldu: {len(plan_steps)} adım")
            for i, step in enumerate(plan_steps, 1):
                print(f"   {i}. {step}")
            
            return {
                "plan": plan_steps,
                "current_step_index": 0,
                "executed_steps": []
            }
            
        except Exception as e:
            print(f"❌ Planlama hatası: {e}")
            return {
                "plan": ["[HATA] Plan oluşturulamadı"],
                "current_step_index": 0,
                "executed_steps": [],
                "final_result": f"Planlama hatası: {str(e)}"
            }

    # === İŞ İSTASYONU 2: İCRA DÜĞÜMÜ ===
    def execute_step(self, state: AgentState) -> Dict:
        """
        Plandaki sıradaki adımı analiz eder ve ilgili aracı çalıştırır.
        """
        current_index = state["current_step_index"]
        plan = state["plan"]
        
        if current_index >= len(plan):
            print("✅ [İCRA DÜĞÜMÜ] Tüm adımlar tamamlandı!")
            return {"current_step_index": current_index}
        
        current_step = plan[current_index]
        print(f"\n⚡ [İCRA DÜĞÜMÜ] Adım {current_index + 1}/{len(plan)}: {current_step}")
        
        try:
            # Adımdan araç adını ve parametreleri çıkar
            tool_name, tool_params = self._parse_step(current_step, state)
            
            if tool_name in self.tools_dict:
                print(f"🔧 Araç '{tool_name}' çalıştırılıyor...")
                
                # Aracı çalıştır
                if tool_name in ["find_and_prepare_gpu"]:
                    result = self.tools_dict[tool_name].invoke(tool_params)
                elif tool_name in ["execute_command_on_pod"]:
                    result = self.tools_dict[tool_name].invoke(tool_params)
                else:
                    result = self.tools_dict[tool_name](**tool_params)
                
                step_result = {
                    "step_number": current_index + 1,
                    "step_description": current_step,
                    "tool_used": tool_name,
                    "result": result,
                    "status": "success"
                }
                print(f"✅ Adım {current_index + 1} başarıyla tamamlandı")
                
            else:
                step_result = {
                    "step_number": current_index + 1,
                    "step_description": current_step,
                    "tool_used": tool_name,
                    "result": f"Bilinmeyen araç: {tool_name}",
                    "status": "error"
                }
                print(f"❌ Bilinmeyen araç: {tool_name}")
            
            return {
                "executed_steps": [step_result],
                "current_step_index": current_index + 1
            }
            
        except Exception as e:
            print(f"❌ Adım {current_index + 1} hatası: {e}")
            error_result = {
                "step_number": current_index + 1,
                "step_description": current_step,
                "result": f"Hata: {str(e)}",
                "status": "error"
            }
            
            return {
                "executed_steps": [error_result],
                "current_step_index": current_index + 1
            }

    def _parse_step(self, step: str, state: AgentState) -> tuple:
        """
        Adım metninden araç adını ve parametreleri çıkarır.
        """
        # [ARAÇ_ADI] formatını ara
        if '[' in step and ']' in step:
            start = step.index('[') + 1
            end = step.index(']')
            tool_name = step[start:end]
            description = step[end+1:].strip()
        else:
            # Fallback
            tool_name = "decide_architecture"
            description = step
        
        # Parametreleri akıllıca belirle
        tool_params = {}
        
        if tool_name == "find_and_prepare_gpu":
            # VRAM miktarını metinden çıkar
            if "16GB" in description or "16 GB" in description:
                tool_params = {"min_memory_gb": 16}
            elif "32GB" in description or "32 GB" in description:
                tool_params = {"min_memory_gb": 32}
            else:
                tool_params = {"min_memory_gb": 16}  # varsayılan
                
        elif tool_name == "execute_command_on_pod":
            # Önceki adımlardan Pod ID'sini bul
            pod_id = self._extract_pod_id_from_history(state["executed_steps"])
            
            if "git clone" in description.lower():
                command = "git clone https://github.com/pytorch/pytorch.git"
            elif "python" in description.lower() and "main" in description.lower():
                command = "cd pytorch && python setup.py install"
            else:
                command = "echo 'Command execution simulation'"
            
            tool_params = f"{pod_id},{command}" if pod_id else "unknown_pod,echo 'No pod found'"
            
        return tool_name, tool_params

    def _extract_pod_id_from_history(self, executed_steps: List[Dict]) -> str:
        """
        Önceki adımlardan Pod ID'sini bulur.
        """
        for step in executed_steps:
            if step.get("tool_used") == "find_and_prepare_gpu":
                result = step.get("result", {})
                if isinstance(result, dict) and "pod_info" in result:
                    return result["pod_info"].get("id", "")
        return ""

    # === İŞ İSTASYONU 3: RAPORLAMA DÜĞÜMÜ ===
    def generate_response(self, state: AgentState) -> Dict:
        """
        Tüm adımların sonuçlarını özetleyerek nihai cevap oluşturur.
        """
        print("\n📊 [RAPORLAMA DÜĞÜMÜ] Nihai rapor hazırlanıyor...")
        
        executed_steps = state["executed_steps"]
        original_task = state["input"]
        
        # Özet oluştur
        summary_parts = [f"**Görev:** {original_task}\n"]
        
        success_count = 0
        error_count = 0
        
        for step in executed_steps:
            step_num = step.get("step_number", "?")
            status = step.get("status", "unknown")
            description = step.get("step_description", "")
            
            if status == "success":
                success_count += 1
                summary_parts.append(f"✅ **Adım {step_num}:** {description}")
            else:
                error_count += 1
                summary_parts.append(f"❌ **Adım {step_num}:** {description}")
        
        # Genel durum
        if error_count == 0:
            final_status = f"🎉 **BAŞARILI!** Tüm {success_count} adım başarıyla tamamlandı."
        else:
            final_status = f"⚠️ **KISMİ BAŞARILI:** {success_count} adım başarılı, {error_count} adım hatalı."
        
        summary_parts.insert(1, final_status + "\n")
        
        final_result = "\n".join(summary_parts)
        
        print("📋 Nihai rapor oluşturuldu!")
        return {"final_result": final_result}

    # === KARAR VERİCİ ===
    def should_continue_execution(self, state: AgentState) -> str:
        """
        Planda daha adım var mı kontrol eder.
        """
        current_index = state["current_step_index"]
        total_steps = len(state["plan"])
        
        if current_index < total_steps:
            print(f"🔄 [KARAR] Devam: {current_index}/{total_steps} adım tamamlandı")
            return "continue"
        else:
            print(f"🏁 [KARAR] Bitiş: Tüm {total_steps} adım tamamlandı")
            return "generate_response"

    # === YENİ ŞEHIR HARİTASI (Akıllı Yönlendirmeli Graf Oluşturucu) ===
    def build_graph(self):
        """
        Akıllı yönlendirme sistemi ile çok adımlı iş akışının grafiğini oluşturur.
        """
        print("🗺️ GraphAgent haritası çiziliyor...")
        
        workflow = StateGraph(AgentState)
        
        # YENİ İŞ İSTASYONLARI: Akıllı yönlendirme sistemi
        workflow.add_node("route_query", self.route_query)      # Güvenlik görevlisi
        workflow.add_node("chatbot_step", self.chatbot_step)    # Sohbet masası
        
        # ESKİ İŞ İSTASYONLARI: Karmaşık görev işleme sistemi  
        workflow.add_node("plan_step", self.plan_step)
        workflow.add_node("execute_step", self.execute_step) 
        workflow.add_node("generate_response", self.generate_response)
        
        # YENİ BAŞLANGIÇ NOKTASI: Artık güvenlik görevlisi kapıda!
        workflow.set_entry_point("route_query")
        
        # YENİ AKILLI YOLLAR: Koşullu yönlendirme sistemi
        workflow.add_conditional_edges(
            "route_query",
            lambda state: state["route_decision"],
            {
                "chat": "chatbot_step",        # Basit sohbet → Sohbet masası
                "task": "plan_step"           # Karmaşık görev → Planlama bölümü  
            }
        )
        
        # SOHBET YOLU: Direkt bitişe gidiyor (hiç araç kullanmıyor)
        workflow.add_edge("chatbot_step", END)
        
        # GÖREV YOLU: Eskiden olduğu gibi karmaşık süreç
        workflow.add_edge("plan_step", "execute_step")
        
        workflow.add_conditional_edges(
            "execute_step",
            self.should_continue_execution,
            {
                "continue": "execute_step",              # Döngü: Bir sonraki adıma
                "generate_response": "generate_response" # Bitirme: Raporlama
            }
        )
        
        workflow.add_edge("generate_response", END)
        
        print("✅ Graf başarıyla oluşturuldu!")
        return workflow.compile()

    def run(self, query: str) -> Dict:
        """
        Akıllı yönlendirmeli görev yürütücüsü.
        """
        print(f"\n🚀 [GÖREV BAŞLADI] {query}")
        
        initial_state = {
            "input": query,
            "route_decision": "",     # YENİ: Yönlendirme kararı
            "plan": [],
            "executed_steps": [], 
            "current_step_index": 0,
            "final_result": ""
        }
        
        final_state = self.graph.invoke(initial_state, {"recursion_limit": 50})
        
        print("\n🎯 [GÖREV TAMAMLANDI]")
        return {
            "result": final_state.get("final_result", "Sonuç oluşturulamadı"),
            "intermediate_steps": final_state.get("executed_steps", []),
            "plan": final_state.get("plan", [])
        }


# --- Test Bloğu ---
if __name__ == '__main__':
    print("🧪 === ÇOK ADIMLI GRAPH AGENT TESLİMİ ===")
    
    graph_agent = GraphAgent()
    
    # Karmaşık test görevi
    test_query = (
        "Bana 16GB VRAM'li bir GPU ortamı hazırla, "
        "ardından PyTorch repository'sini clone et ve kurulumunu yap."
    )
    
    print(f"\n📝 Test Görevi: {test_query}")
    result_state = graph_agent.run(test_query)
    
    print("\n" + "="*80)
    print("🎯 SONUÇ:")
    print(result_state.get("result", "Sonuç bulunamadı"))
    print("="*80)
    
    # Plan ve adımları da göster
    if "plan" in result_state:
        print(f"\n📋 Oluşturulan Plan ({len(result_state['plan'])} adım):")
        for i, step in enumerate(result_state["plan"], 1):
            print(f"  {i}. {step}")
    
    if "intermediate_steps" in result_state:
        print(f"\n⚡ Gerçekleştirilen Adımlar ({len(result_state['intermediate_steps'])}):")
        for step in result_state["intermediate_steps"]:
            status = "✅" if step.get("status") == "success" else "❌"
            print(f"  {status} Adım {step.get('step_number', '?')}: {step.get('step_description', 'N/A')}")

