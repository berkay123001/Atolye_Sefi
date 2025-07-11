# app/dashboard.py

import gradio as gr
import json
from datetime import datetime

# --- Proje Bileşenleri ---
try:
    from config import settings
    from agents.graph_agent import GraphAgent
    from tools.pod_management_tools import prepare_environment_with_ssh
    print("Yapılandırma ve GraphAgent başarıyla yüklendi.")
except ImportError:
    print("Hata: Gerekli modüller yüklenemedi. Lütfen projenin bir paket olarak doğru kurulduğundan emin olun.")
    raise

# --- Tek Seferlik GraphAgent Başlatma ---
print("GraphAgent nesnesi oluşturuluyor...")
graph_agent = GraphAgent()
print("GraphAgent akış şeması derleniyor...")
# GraphAgent.__init__ içinde zaten build_graph() çağrılıyor, tekrar çağırmaya gerek yok
print("GraphAgent tamamen hazır ve operasyonel.")

def run_agent_interaction(user_message: str, history: list, logs: str):
    """
    Kullanıcı etkileşimini yönetir. Bu yeni versiyon GraphAgent ile
    doğrudan ve senkron şekilde çalışır - karmaşık Queue/threading yok!
    """
    # 1. Kullanıcının mesajını sohbete ekle (eski format - [user, bot] listesi)
    history.append([user_message, None])
    
    # 2. Zaman damgası ile yeni görev başlangıcını logla
    timestamp = datetime.now().strftime("%H:%M:%S")
    new_log_entry = f"\n=== GÖREV BAŞLADI [{timestamp}] ===\nKullanıcı: {user_message}\n"
    
    # Eğer bu ilk çalıştırmaysa, başlangıç metnini temizle
    if logs == "Ajan bir komut bekliyor...":
        current_logs = new_log_entry
    else:
        current_logs = logs + "\n" + new_log_entry
    
    try:
        # 3. GraphAgent'ı doğrudan çağır - tek satırda tüm işlem!
        print(f"GraphAgent'a gönderiliyor: {user_message}")
        final_state = graph_agent.run(user_message)
        
        # 4. Ajanın nihai cevabını al ve eski formatta ekle
        agent_response = final_state.get('result', 'Ajan bir cevap üretemedi.')
        history[-1][1] = agent_response  # Son mesajın bot kısmını doldur
        
        # 5. Intermediate steps'i logla (GraphAgent'ın düşünce süreci)
        intermediate_steps = final_state.get('intermediate_steps', [])
        
        current_logs += f"GraphAgent Düşünce Süreci:\n"
        if intermediate_steps:
            for i, step in enumerate(intermediate_steps, 1):
                current_logs += f"  Adım {i}: {str(step)}\n"
        else:
            current_logs += "  (Ajan doğrudan sonuca ulaştı)\n"
            
        current_logs += f"\nNihai Cevap: {agent_response}\n"
        current_logs += f"=== GÖREV TAMAMLANDI [{datetime.now().strftime('%H:%M:%S')}] ===\n"
        
        print("GraphAgent görevi başarıyla tamamladı.")
        
    except Exception as e:
        # 6. Hata durumunda kullanıcıya bilgi ver
        error_msg = f"**HATA OLUŞTU:**\n\n{str(e)}"
        history[-1][1] = error_msg  # Son mesajın bot kısmını hata ile doldur
        current_logs += f"HATA: {str(e)}\n"
        current_logs += f"=== GÖREV HATA İLE SONLANDI [{datetime.now().strftime('%H:%M:%S')}] ===\n"
        
        print(f"GraphAgent hatası: {e}")
    
    # 7. Güncellenmiş history, logs ve temizlenmiş input'u döndür
    return history, current_logs, ""

def create_gpu_pod():
    """GPU Pod oluşturma fonksiyonu"""
    try:
        result = prepare_environment_with_ssh.invoke({
            "gpu_type_id": "NVIDIA GeForce RTX 3070"
        })
        
        if result.get('status') == 'success':
            return f"""🎉 **Pod Başarıyla Oluşturuldu!**

🆔 **Pod ID:** {result.get('pod_id')}
🔗 **Jupyter URL:** {result.get('jupyter_url')}
🔐 **Şifre:** atolye123

✅ Pod artık kullanıma hazır!"""
        else:
            return f"❌ **Pod Oluşturma Hatası:** {result.get('message')}"
            
    except Exception as e:
        return f"❌ **Beklenmeyen Hata:** {str(e)}"

def get_current_pods():
    """Mevcut pod'ları listeler"""
    try:
        import sys
        import os
        
        # runpod_test_script.py'ı import et
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'runpod_test_script.py')
        
        if os.path.exists(script_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location("runpod_script", script_path)
            runpod_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runpod_script)
            
            # Output'u yakala
            import io
            from contextlib import redirect_stdout
            
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                runpod_script.list_all_pods()
            
            output = output_buffer.getvalue()
            
            if "Hiç pod bulunamadı" in output:
                return "📝 **Mevcut Pod Yok**\n\nHenüz aktif pod'unuz bulunmuyor."
            else:
                return f"📋 **Mevcut Pod'lar:**\n```\n{output}\n```"
        else:
            return "❌ **Script bulunamadı**"
            
    except Exception as e:
        return f"❌ **Pod Listesi Hatası:** {str(e)}"


# --- Gradio Arayüzü ---
with gr.Blocks(title="Atölye Şefi", theme=gr.themes.Soft(primary_hue="sky", secondary_hue="slate")) as demo:
    gr.Markdown("# Atölye Şefi - MLOps Agent Kontrol Paneli")
    gr.Markdown(f"**Aktif Model:** `{settings.AGENT_MODEL_NAME}` | **Ajan Tipi:** GraphAgent (LangGraph)")

    with gr.Tabs():
        # TAB 1: Agent Chat
        with gr.TabItem("🤖 Agent Chat"):
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="Diyalog Penceresi", 
                        height=600, 
                        # type="messages",  # Eski Gradio sürümü için geçici olarak kapatıldı
                        value=[],  # Boş liste ile başlat
                        avatar_images=(None, "https://placehold.co/100x100/2980b9/ffffff?text=Şef")
                    )
                    with gr.Row():
                        user_input = gr.Textbox(
                            show_label=False, 
                            placeholder="GraphAgent için bir komut girin (örn: 'Bana 16GB VRAM'li bir ortam hazırla')", 
                            scale=5, 
                            container=False
                        )
                        submit_button = gr.Button("Gönder", variant="primary", scale=1)
                with gr.Column(scale=1):
                    agent_logs = gr.Textbox(
                        label="GraphAgent Logları (LangGraph State Tracking)",
                        value="Ajan bir komut bekliyor...",
                        lines=28,
                        interactive=False,
                        autoscroll=True
                    )
        
        # TAB 2: Pod Management
        with gr.TabItem("🚀 Pod Yönetimi"):
            gr.Markdown("## RunPod GPU Pod Yönetimi")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🎮 Yeni Pod Oluştur")
                    create_pod_button = gr.Button("🚀 GPU Pod Oluştur (RTX 3070)", variant="primary", size="lg")
                    pod_creation_output = gr.Markdown("Pod oluşturmak için butona tıklayın.")
                    
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 Mevcut Pod'lar")
                    refresh_pods_button = gr.Button("🔄 Pod'ları Listele", variant="secondary")
                    pods_list_output = gr.Markdown("Pod listesini görmek için butona tıklayın.")
            
            gr.Markdown("""
            ### 📝 Kullanım Talimatları:
            1. **🚀 GPU Pod Oluştur**: Yeni bir RTX 3070 Pod'u oluşturur (30-60 saniye sürer)
            2. **📋 Pod'ları Listele**: Mevcut aktif pod'larınızı gösterir
            3. **Jupyter Erişimi**: Oluşturulan pod'un URL'ine tıklayarak Jupyter'a erişebilirsiniz
            4. **Şifre**: Tüm pod'lar için şifre `atolye123`'tür
            
            ⚠️ **Dikkat**: Pod oluşturma işlemi ücretlidir!
            """)

    # Event handlers
    # GraphAgent ile senkron çalışan event handler'lar  
    inputs = [user_input, chatbot, agent_logs]
    outputs = [chatbot, agent_logs, user_input]

    # Artık generator değil, normal fonksiyon kullanıyoruz
    submit_button.click(fn=run_agent_interaction, inputs=inputs, outputs=outputs)
    user_input.submit(fn=run_agent_interaction, inputs=inputs, outputs=outputs)
    
    # Pod management event handlers
    create_pod_button.click(fn=create_gpu_pod, outputs=pod_creation_output)
    refresh_pods_button.click(fn=get_current_pods, outputs=pods_list_output)

def health_check():
    """Health check endpoint for Docker containers"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("Gradio uygulaması başlatılıyor...")
    demo.launch()
