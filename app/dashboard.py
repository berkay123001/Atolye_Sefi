# app/dashboard.py

import gradio as gr
from queue import Queue, Empty
import time

# --- Proje Bileşenleri ---
try:
    from config import settings
    from agents.chief_agent import ChiefAgent
    print("Yapılandırma ve ChiefAgent başarıyla yüklendi.")
except ImportError:
    print("Hata: Gerekli modüller yüklenemedi. Lütfen projenin bir paket olarak doğru kurulduğundan emin olun.")
    raise

# --- Tek Seferlik Ajan Başlatma ---
print("ChiefAgent nesnesi oluşturuluyor...")
chief_agent = ChiefAgent()
print("ChiefAgent hazır.")

def run_agent_interaction(user_message: str, history: list, logs: str):
    """
    Kullanıcı etkileşimini yönetir. Bu versiyon, logların durumunu
    korur ve her yeni görevin loglarını bir öncekinin altına ekler.
    """
    # 1. Kullanıcının mesajını sohbete ekle
    history.append([user_message, None])
    
    # 2. Mevcut logları temizlemek yerine, yeni oturumun başladığını belirt
    # Eğer bu ilk çalıştırmaysa, başlangıç metnini temizle.
    if logs == "Ajan bir komut bekliyor...":
        current_logs = "Ajan yeni bir görev için düşünmeye başlıyor..."
    else:
        # Değilse, mevcut logların altına bir ayırıcı ve yeni başlangıç metni ekle.
        current_logs = logs + "\n\n---\n\n" + "Ajan yeni bir görev için düşünmeye başlıyor..."
        
    yield history, current_logs, ""

    # 3. İletişim için kuyruğu oluştur ve ajanı arka planda başlat
    log_queue = Queue()
    chief_agent.run(user_input=user_message, q=log_queue)

    # 4. Kuyruktan gelen logları biriktir ve arayüzü güncelle
    while True:
        try:
            item = log_queue.get(timeout=0.1)

            if isinstance(item, dict):
                # Nihai cevap veya hata geldiyse döngüyü sonlandır
                if "final_answer" in item:
                    history[-1][1] = item["final_answer"]
                    break
                elif "error" in item:
                    history[-1][1] = f"**HATA OLUŞTU:**\n\n{item['error']}"
                    break
            else:
                # Yeni log metnini, mevcut logların üzerine ekle
                current_logs += f"\n\n{item}"
                yield history, current_logs, ""

        except Empty:
            time.sleep(0.1)
            continue
        except Exception as e:
            print(f"Arayüz döngüsünde bir hata oluştu: {e}")
            break

    # Döngü bittiğinde, son güncellemeyi arayüze gönder
    yield history, current_logs, ""


# --- Gradio Arayüzü ---
with gr.Blocks(title="Atölye Şefi", theme=gr.themes.Soft(primary_hue="sky", secondary_hue="slate")) as demo:
    gr.Markdown("# Atölye Şefi - MLOps Agent Kontrol Paneli")
    gr.Markdown(f"**Aktif Model:** `{settings.AGENT_MODEL_NAME}`")

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Diyalog Penceresi", height=600, avatar_images=(None, "https://placehold.co/100x100/2980b9/ffffff?text=Şef"))
            with gr.Row():
                user_input = gr.Textbox(show_label=False, placeholder="Ajan için bir komut girin...", scale=5, container=False)
                submit_button = gr.Button("Gönder", variant="primary", scale=1)
        with gr.Column(scale=1):
            # DÜZELTME: Log panelini, kaydırılabilir ve her zaman görünür
            # olan bir Textbox bileşeniyle değiştiriyoruz.
            agent_logs = gr.Textbox(
                label="Atölye Logları (Düşünce/Eylem/Gözlem)",
                value="Ajan bir komut bekliyor...",
                lines=28, # Chatbot ile benzer yükseklikte olmasını sağlar
                interactive=False, # Sadece okunabilir
                autoscroll=True  # Yeni log geldiğinde otomatik aşağı kaydır
            )

    # DÜZELTME: Log panelinin mevcut içeriğini ('agent_logs') fonksiyona
    # bir girdi olarak ekliyoruz. Bu, logların korunmasını sağlar.
    inputs = [user_input, chatbot, agent_logs]
    outputs = [chatbot, agent_logs, user_input]

    submit_button.click(fn=run_agent_interaction, inputs=inputs, outputs=outputs)
    user_input.submit(fn=run_agent_interaction, inputs=inputs, outputs=outputs)

if __name__ == "__main__":
    print("Gradio uygulaması başlatılıyor...")
    demo.launch()
