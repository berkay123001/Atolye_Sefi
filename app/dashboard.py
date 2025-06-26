# app/dashboard.py

import gradio as gr
import sys
import os

# --- Proje Bileşenlerini Import Etme ---

# Proje ana dizinini Python yoluna ekleyerek diğer modülleri import edilebilir hale getiriyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from config import settings
    from agents.chief_agent import ChiefAgent # Ajanımızın ana sınıfını import ediyoruz.
    print("Yapılandırma ve ChiefAgent başarıyla yüklendi.")
except ImportError as e:
    print(f"Hata: Gerekli modüller yüklenemedi: {e}")
    # Gerekli bileşenler olmadan uygulama çalışamaz.
    sys.exit(1)


# --- Tek Seferlik Ajan Başlatma ---
# Uygulama başladığında SADECE BİR KERE çalışacak şekilde ajan nesnesini oluşturuyoruz.
# Bu, ajanın hafızasının ve durumunun tüm kullanıcı etkileşimleri boyunca korunmasını sağlar.
print("ChiefAgent nesnesi oluşturuluyor... Bu işlem birkaç saniye sürebilir.")
chief_agent = ChiefAgent()
print("ChiefAgent hazır.")


def run_agent_interaction(user_message, history):
    """
    Kullanıcıdan gelen mesajı alır, ChiefAgent'i çalıştırır ve arayüzü günceller.

    Args:
        user_message (str): Kullanıcının metin kutusuna girdiği mesaj.
        history (list): gr.Chatbot bileşeninin tuttuğu sohbet geçmişi.

    Returns:
        tuple: Güncellenmiş sohbet geçmişi, atölye log çıktısı ve boş bir string.
    """
    # 1. Kullanıcının mesajını anında arayüze ekle
    history.append([user_message, None])
    
    # Statik log mesajını ayarla ve arayüzü anında güncelle
    log_output = "Gerçek zamanlı loglar yakında eklenecek..."
    yield history, log_output, ""

    # 2. Arka planda ajanı çalıştır ve cevabını al
    # Bu, LLM'e yapılan gerçek bir çağrıdır ve biraz zaman alabilir.
    bot_response = chief_agent.run(user_input=user_message)
    
    # 3. Ajanın cevabını sohbet geçmişine ekle
    history[-1][1] = bot_response

    # 4. Arayüzün son halini tekrar gönder
    yield history, log_output, ""


# --- Gradio Arayüzü ---
with gr.Blocks(
    title="Atölye Şefi",
    theme=gr.themes.Soft(primary_hue="sky", secondary_hue="slate")
) as demo:
    gr.Markdown("# Atölye Şefi - MLOps Agent Kontrol Paneli")
    gr.Markdown("Bu arayüz, otonom MLOps asistanı 'Atölye Şefi' ile etkileşim kurmanızı sağlar. Komutlarınızı girin ve ajanın adımlarını loglardan takip edin.")
    gr.Markdown(f"**Aktif Model:** `{settings.AGENT_MODEL_NAME}` | **Sistem Talimatı:** `LangChain ReAct Prompt`")

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Diyalog Penceresi",
                bubble_full_width=False,
                avatar_images=(None, "https://placehold.co/100x100/2980b9/ffffff?text=Şef"),
                height=500
            )
            
            with gr.Row():
                user_input = gr.Textbox(
                    show_label=False,
                    placeholder="Ajan için bir komut yazın (örn: 'Merhaba, kendini tanıtır mısın?')...",
                    scale=5,
                    container=False,
                )
                submit_button = gr.Button("Gönder", variant="primary", scale=1)

        with gr.Column(scale=1):
            agent_logs = gr.Textbox(
                label="Atölye Logları (Düşünce/Eylem/Gözlem)",
                interactive=False,
                lines=25,
                max_lines=25,
            )

    # --- Olayları Bağlama ---
    submit_button.click(
        fn=run_agent_interaction,
        inputs=[user_input, chatbot],
        outputs=[chatbot, agent_logs, user_input]
    )
    
    user_input.submit(
        fn=run_agent_interaction,
        inputs=[user_input, chatbot],
        outputs=[chatbot, agent_logs, user_input]
    )

# --- GERİ EKLENDİ: Başlatma Bloğu ---
# Bu blok, bu dosyanın hem `python -m app.dashboard` komutuyla bir modül olarak,
# hem de doğrudan `python app/dashboard.py` komutuyla (eğer gerekirse)
# çalıştırılabilmesini sağlar.
if __name__ == "__main__":
    print("Gradio uygulaması başlatılıyor...")
    demo.launch()

