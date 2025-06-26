# app/dashboard.py

import gradio as gr
import time
import sys
import os

# Proje ana dizinini Python yoluna ekleyerek config.py'yi import edilebilir hale getiriyoruz.
# Bu, app/ klasöründen çalıştırıldığında bir üst dizine ('..') erişmemizi sağlar.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    # Yapılandırma ayarlarımızı import ediyoruz.
    from config import settings
    print("Yapılandırma başarıyla yüklendi.")
    print(f"Kullanılacak LLM Modeli: {settings.AGENT_MODEL_NAME}")
except ImportError:
    print("Hata: config.py bulunamadı veya 'settings' nesnesi export edilmemiş.")
    # Uygulamanın çökmemesi için sahte bir settings nesnesi oluşturulabilir
    # ancak en doğrusu yapılandırma dosyasının doğru yerde olmasıdır.
    class MockSettings:
        AGENT_MODEL_NAME = "Ayarlanmadı"
    settings = MockSettings()


def run_agent_interaction(user_message, history):
    """
    Kullanıcıdan gelen mesajı işler ve ajan ile etkileşimi simüle eder.

    Args:
        user_message (str): Kullanıcının metin kutusuna girdiği mesaj.
        history (list): gr.Chatbot bileşeninin tuttuğu sohbet geçmişi.

    Returns:
        tuple: Güncellenmiş sohbet geçmişi, atölye log çıktısı ve boş bir string (metin kutusunu temizlemek için).
    """
    # 1. Kullanıcının mesajını sohbet geçmişine ekle
    history.append([user_message, None])

    # 2. Atölye Logları için sahte bir log oluştur (Simülasyon)
    # Gerçek ajan entegre edildiğinde burası ajanın "Düşünce -> Eylem -> Gözlem" döngüsünden gelen gerçek loglarla dolacak.
    log_output = (
        "Düşünce: Kullanıcı bir komut verdi. Komutu analiz etmeliyim.\n"
        f"Plan: '{user_message}' komutunu işlemek için sahte bir eylem başlat.\n"
        "Eylem: Simülasyon aracını çalıştır.\n"
        "Gözlem: Simülasyon aracı 'İşlem tamamlandı.' mesajını döndürdü."
    )
    
    # 3. Chatbot'a anında cevap veriyormuş gibi görünmesi için geçmişi ve logları güncelle
    # Bu, kullanıcıya sistemin çalıştığını anında gösterir.
    yield history, log_output, ""

    # 4. Ajanın "cevap üretme" sürecini simüle et
    time.sleep(2) # Ajanın düşündüğünü hissettirmek için küçük bir bekleme

    # 5. Sahte bir ajan cevabı oluştur
    bot_response = f"Atölye Şefi (Simülasyon): Komutunuz '{user_message}' alındı ve ilgili sahte işlem başarıyla tamamlandı."
    
    # Sohbet geçmişindeki son girdiyi (bizim None olarak eklediğimiz yeri) botun cevabıyla güncelle
    history[-1][1] = bot_response

    # 6. Son halini tekrar arayüze gönder
    yield history, log_output, ""


# --- Gradio Arayüzü ---
with gr.Blocks(
    title="Atölye Şefi",
    theme=gr.themes.Soft(primary_hue="sky", secondary_hue="light")
) as demo:
    gr.Markdown("# Atölye Şefi - MLOps Agent Kontrol Paneli")
    gr.Markdown("Bu arayüz, otonom MLOps asistanı 'Atölye Şefi' ile etkileşim kurmanızı sağlar. Komutlarınızı girin ve ajanın adımlarını loglardan takip edin.")
    gr.Markdown(f"**Aktif Model:** `{settings.AGENT_MODEL_NAME}` | **Sistem Talimatı:** `{settings.AGENT_SYSTEM_PROMPT}`")

    with gr.Row():
        with gr.Column(scale=2):
            # Sol taraf: Sohbet ve kullanıcı girdisi
            chatbot = gr.Chatbot(
                label="Diyalog Penceresi",
                bubble_full_width=False,
                avatar_images=(None, "https://placehold.co/100x100/2980b9/ffffff?text=Şef"), # Basit bir avatar
                height=500
            )
            
            with gr.Row():
                user_input = gr.Textbox(
                    show_label=False,
                    placeholder="Ajan için bir komut yazın (örn: 'Modeli eğit ve en iyisini bul')...",
                    scale=5,
                    container=False, # Kenarlıkları kaldırmak için
                )
                submit_button = gr.Button("Gönder", variant="primary", scale=1)

        with gr.Column(scale=1):
            # Sağ taraf: Ajanın içsel logları
            agent_logs = gr.Textbox(
                label="Atölye Logları (Düşünce/Eylem/Gözlem)",
                interactive=False, # Sadece okunabilir
                lines=25,
                max_lines=25,
            )

    # --- Olayları Bağlama (Event Handling) ---
    
    # Hem "Gönder" butonuna tıklandığında hem de metin kutusundayken Enter'a basıldığında fonksiyonu tetikle
    action_event = submit_button.click(
        fn=run_agent_interaction,
        inputs=[user_input, chatbot],
        outputs=[chatbot, agent_logs, user_input]
    )
    
    user_input.submit(
        fn=run_agent_interaction,
        inputs=[user_input, chatbot],
        outputs=[chatbot, agent_logs, user_input]
    )


if __name__ == "__main__":
    print("Gradio uygulaması başlatılıyor...")
    # Uygulamayı lokal ağda paylaşmak için share=True yapabilirsiniz.
    demo.launch()

