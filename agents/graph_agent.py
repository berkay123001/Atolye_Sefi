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
from tools.operational_tools import find_and_prepare_gpu, start_task_on_pod
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
            "start_task_on_pod": start_task_on_pod,  # Jupyter notebook komut hazırlama
            "execute_command_on_pod": execute_command_on_pod,  # Eski versiyon (fallback)
            "get_pod_status": get_pod_status,
            # SSH araçlarını ekle
            "execute_ssh_command": self._execute_ssh_command_wrapper,
        }
        
        # Grafiği oluştur
        self.graph = self.build_graph()
        print("🧠 GraphAgent: Çok adımlı hafıza sistemi aktif!")

    def _execute_ssh_command_wrapper(self, **kwargs) -> Dict:
        """SSH komut çalıştırma wrapper'ı."""
        try:
            from tools.ssh_pod_tools import execute_ssh_command
            pod_id = kwargs.get("pod_id", "")
            command = kwargs.get("command", "")
            
            if not pod_id or not command:
                return {"status": "error", "message": "Pod ID ve komut gerekli"}
            
            return execute_ssh_command(pod_id, command)
        except Exception as e:
            return {"status": "error", "message": f"SSH hatası: {str(e)}"}

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
- Eğer girdi sadece selamlama ise -> "chat" 
- DİĞER HER ŞEY -> "task" (Pod, kod, ortam, oluştur, çalıştır, yaz içeren tüm istekler)

ÖRNEKLERİ:
- "merhaba" -> chat
- "nasılsın" -> chat  
- "pod oluştur" -> task
- "kod yaz" -> task
- "ortam hazırla" -> task
- "çalıştır" -> task
- "GPU" -> task
- "RunPod" -> task
- "hesap makinesi" -> task

UYARI: Şüpheli durumlarda "task" seç! Pod/kod/çalıştır kelimelerini gören her şey "task"!

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

    # === İŞ İSTASYONU 2: YENİ PLANLAMA DÜĞÜMÜ ===
    def plan_step(self, state: AgentState) -> Dict:
        """
        Kullanıcının görevini analiz eder ve her biri tek bir bash komutu olan adımlar oluşturur.
        """
        print("\n🎯 [PLANLAMA DÜĞÜMÜ] Görev bash komutlarına dönüştürülüyor...")
        
        planning_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen, bir DevOps otomasyon uzmanısın. Sana verilen görevi, uzak bir sunucuda, 
            bash terminalinde çalıştırılacak, TEKİL VE SIRALI KOMUTLARIN bir listesine dönüştür.

            KURALLAR:
            - Her adım, SADECE TEK BİR KOMUT içermelidir
            - Karmaşık && zincirleri KURMA 
            - Her komutu AYRI BİR ADIM olarak yaz
            - Plan, doğrudan bir betik gibi çalıştırılabilir olmalı

            Kullanılabilir araçlar:
            - find_and_prepare_gpu: Yeni pod oluşturmak için
            - execute_ssh_command: Tek bash komutu çalıştırmak için
            - get_pod_status: Pod durumunu kontrol etmek için

            Format:
            1. [execute_ssh_command] pwd
            2. [execute_ssh_command] ls -la
            3. [execute_ssh_command] mkdir /workspace/proje
            4. [execute_ssh_command] cd /workspace/proje
            5. [execute_ssh_command] echo "print('hello')" > test.py
            6. [execute_ssh_command] python test.py

            ÖNEMLİ: Her komut ayrı satır, tek işlem, bash uyumlu!"""),
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

    # === İŞ İSTASYONU 3: YENİ İCRA DÜĞÜMÜ ===
    def execute_step(self, state: AgentState) -> Dict:
        """
        Plandaki sıradaki bash komutunu analiz eder ve çalıştırır.
        Her adım tek bir bash komutu içerir.
        """
        current_index = state["current_step_index"]
        plan = state["plan"]
        
        if current_index >= len(plan):
            print("✅ [İCRA DÜĞÜMÜ] Tüm adımlar tamamlandı!")
            return {"current_step_index": current_index}
        
        current_step = plan[current_index]
        print(f"\n⚡ [İCRA DÜĞÜMÜ] Adım {current_index + 1}/{len(plan)}: {current_step}")
        
        try:
            # 1. Sıradaki komutu al ve ayrıştır
            tool_name, bash_command = self._parse_bash_command(current_step, state)
            
            # 2. Doğru aracı çağır
            if tool_name in self.tools_dict:
                print(f"🔧 Araç '{tool_name}' çalıştırılıyor...")
                print(f"📋 Bash komutu: {bash_command}")
                
                # Pod ID'sini önceki adımlardan al
                pod_id = self._extract_pod_id_from_context(state)
                
                # Parametreleri hazırla
                if tool_name == "execute_ssh_command":
                    tool_params = {"pod_id": pod_id, "command": bash_command}
                elif tool_name == "find_and_prepare_gpu":
                    tool_params = {"min_memory_gb": 16}  # default
                elif tool_name == "get_pod_status":
                    tool_params = {"pod_id": pod_id}
                else:
                    tool_params = {}
                
                # Aracı çalıştır
                try:
                    result = self.tools_dict[tool_name].invoke(tool_params)
                except:
                    # Fallback: Direct function call
                    result = self.tools_dict[tool_name](**tool_params)
                
                # 3. Sonucu kaydet
                step_result = {
                    "step_number": current_index + 1,
                    "step_description": current_step,
                    "tool_used": tool_name,
                    "bash_command": bash_command,
                    "result": result,
                    "status": "success" if result.get("status") == "success" else "error"
                }
                
                print(f"✅ Adım {current_index + 1} tamamlandı!")
                if result.get("output"):
                    print(f"📤 Çıktı: {result.get('output', '')[:100]}...")
                
            else:
                step_result = {
                    "step_number": current_index + 1,
                    "step_description": current_step,
                    "tool_used": tool_name,
                    "bash_command": bash_command,
                    "result": f"Bilinmeyen araç: {tool_name}",
                    "status": "error"
                }
                print(f"❌ Bilinmeyen araç: {tool_name}")
            
            # 4. Bir sonraki adıma geç
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

    def _parse_bash_command(self, step: str, state: AgentState) -> tuple:
        """
        Adım metninden araç adını ve bash komutunu çıkarır.
        Format: "[tool_name] bash_command"
        """
        # [ARAÇ_ADI] formatını ara
        if '[' in step and ']' in step:
            start = step.index('[') + 1
            end = step.index(']')
            tool_name = step[start:end]
            bash_command = step[end+1:].strip()
        else:
            # Fallback
            tool_name = "execute_ssh_command"
            bash_command = step.strip()
        
        return tool_name, bash_command

    def _extract_pod_id_from_context(self, state: AgentState) -> str:
        """
        User input'tan veya önceki adımlardan pod ID'sini çıkarır.
        """
        # Önce user input'tan ara
        user_input = state.get("input", "")
        import re
        match = re.search(r'\b[a-z0-9]{14}\b', user_input)
        if match:
            return match.group()
        
        # Sonra executed_steps'ten ara
        for step in state.get("executed_steps", []):
            if step.get("tool_used") == "find_and_prepare_gpu":
                result = step.get("result", {})
                if isinstance(result, dict):
                    if "pod_id" in result:
                        return result["pod_id"]
                    if "pod_info" in result:
                        return result["pod_info"].get("id", "")
        
        return "unknown_pod"

    def _extract_pod_id_from_history(self, executed_steps: List[Dict]) -> str:
        """
        Önceki adımlardan Pod ID'sini bulur.
        """
        for step in executed_steps:
            if step.get("tool_used") == "find_and_prepare_gpu":
                result = step.get("result", {})
                if isinstance(result, dict):
                    # Önce direkt pod_id'yi kontrol et
                    if "pod_id" in result:
                        return result["pod_id"]
                    # Sonra pod_info içinde ara
                    if "pod_info" in result:
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


# === FACTORY FUNCTION ===
def create_graph_agent():
    """GraphAgent instance oluşturur."""
    return GraphAgent()


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

