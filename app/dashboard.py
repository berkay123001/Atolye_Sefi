# app/dashboard.py

import gradio as gr
import json
from datetime import datetime

# --- Proje Bileşenleri ---
try:
    from config import settings
    from agents.graph_agent import GraphAgent
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


# --- Gradio Arayüzü ---
with gr.Blocks(title="Atölye Şefi", theme=gr.themes.Soft(primary_hue="sky", secondary_hue="slate")) as demo:
    gr.Markdown("# Atölye Şefi - MLOps Agent Kontrol Paneli")
    gr.Markdown(f"**Aktif Model:** `{settings.AGENT_MODEL_NAME}` | **Ajan Tipi:** GraphAgent (LangGraph)")

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

    # GraphAgent ile senkron çalışan event handler'lar
    inputs = [user_input, chatbot, agent_logs]
    outputs = [chatbot, agent_logs, user_input]

    # Artık generator değil, normal fonksiyon kullanıyoruz
    submit_button.click(fn=run_agent_interaction, inputs=inputs, outputs=outputs)
    user_input.submit(fn=run_agent_interaction, inputs=inputs, outputs=outputs)

def health_check():
    """Health check endpoint for Docker containers"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("Gradio uygulaması başlatılıyor...")
    demo.launch()
