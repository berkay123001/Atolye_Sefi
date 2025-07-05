# tools/architectural_tools.py

import sys
import os
import json
from typing import Literal, Dict

# --- Proje Yapılandırması ve Kütüphaneler ---
# Projeyi ana dizinden `python -m ...` ile çalıştırdığımız varsayılarak,
# üst dizinlerdeki modüllere erişim sağlanır.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from config import settings
except ImportError:
    print("Hata: config.py bulunamadı. Lütfen projenin ana dizininde olduğunuzdan emin olun.")
    sys.exit(1)

# LangChain ve diğer gerekli kütüphaneler
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_groq import ChatGroq


# --- Profesyonel Tavsiye #2: Yapısal Çıktı (Structured Output) ---
# LLM'den sadece bir metin istemek yerine, cevabını Pydantic kullanarak
# belirli bir şemaya (schema) uymaya zorluyoruz. Bu, cevabın her zaman
# beklediğimiz formatta (JSON) olmasını garanti eder ve kodumuzu daha
# güvenilir ve hataya dayanıklı hale getirir.
class ArchitectureInput(BaseModel):
    """decide_architecture tool'u için input schema."""
    problem_description: str = Field(
        ..., description="Analiz edilecek problemin açıklaması."
    )

class ArchitectureDecision(BaseModel):
    """LLM'in mimari kararını yapılandırmak için veri modeli."""
    selected_architecture: Literal["Transformer", "SSM (Mamba)"] = Field(
        ..., description="Verilen problem için seçilen AI mimarisi."
    )
    reasoning: str = Field(
        ..., description="Bu mimarinin neden seçildiğini açıklayan kısa bir gerekçe."
    )
    confidence_score: float = Field(
        ..., description="Bu karara olan güven (0.0 ile 1.0 arasında).", ge=0.0, le=1.0
    )


@tool(args_schema=ArchitectureInput)
def decide_architecture(problem_description: str) -> Dict:
    """
    Verilen bir probleme en uygun AI mimarisini (Transformer veya SSM) seçer.
    Bu araç, bir AI Başmimarısı gibi davranarak, problemin tanımını analiz eder
    ve en uygun mimari seçeneğini bir gerekçe ile birlikte JSON formatında döndürür.
    """
    
    # 1. LLM'e verilecek olan detaylı sistem talimatı (System Prompt)
    system_prompt = """Sen, bir AI Başmimarısısın. Görevin, sana verilen bir probleme en uygun AI mimarisini seçmektir. 
Kararını ve gerekçeni, sana verilen JSON şemasına tam olarak uyacak şekilde vermelisin. Başka hiçbir metin ekleme.

İşte karar verirken kullanacağın seçeneklerin ve kuralların:

1.  **Transformer Mimarisi:**
    - **Güçlü Yönleri:** Genel amaçlı görevler, dil anlama, sohbet, metin sınıflandırma ve çoğu standart problem için endüstri standardı ve mükemmel bir seçimdir.
    - **Zayıf Yönleri:** Çok uzun metin dizileriyle (örneğin 100,000 token'dan uzun) çalışırken hesaplama karmaşıklığı karesel olarak artar (O(n²)), bu da onu yavaş ve pahalı hale getirir.

2.  **SSM (State Space Model) Mimarisi (Örn: Mamba):**
    - **Güçlü Yönleri:** Özellikle çok uzun metin dizilerini (tüm bir kod tabanı, kitaplar, genom dizileri, yüksek frekanslı zaman serileri) analiz etmede inanılmaz hızlı ve verimlidir. Hesaplama karmaşıklığı neredeyse lineerdir (O(n)), bu da onu uzun bağlam gerektiren görevler için ideal kılar. Daha az bellek (VRAM) kullanır.
    - **Zayıf Yönleri:** Genel amaçlı, kısa metinli görevlerde Transformer kadar iyi ayarlanmamış veya yaygın olarak test edilmemiş olabilir.

Senin görevin, kullanıcının problemini dikkatlice analiz edip bu iki seçenekten hangisinin daha mantıklı olduğuna karar vermektir."""

    # 2. LLM Nesnesini Oluşturma
    # `with_structured_output` metodu, LLM'in cevabını ArchitectureDecision şemamıza zorlar.
    llm = ChatGroq(
        temperature=0, 
        model_name=settings.AGENT_MODEL_NAME, 
        groq_api_key=settings.GROQ_API_KEY
    ).with_structured_output(ArchitectureDecision)

    # 3. Prompt Şablonunu Oluşturma
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Lütfen aşağıdaki problemi analiz et ve en uygun mimariye karar ver:\n\n{problem}")
    ])

    # 4. Zinciri (Chain) Oluşturma ve Çağırma
    chain = prompt | llm
    
    print(f"\n[Architect Tool] Mimari kararı için LLM çağrılıyor...\nProblem: {problem_description}")
    
    try:
        decision = chain.invoke({"problem": problem_description})
        print(f"[Architect Tool] LLM'den cevap alındı: {decision}")
        # Pydantic modelini Python sözlüğüne çevirerek döndür
        return decision.dict()
    except Exception as e:
        print(f"[Architect Tool] Hata: LLM'den yapısal cevap alınamadı. Hata: {e}")
        return {
            "error": "Mimari kararı verilirken bir hata oluştu.",
            "details": str(e)
        }


# --- Test Bloğu ---
if __name__ == '__main__':
    print("--- Mimari Karar Aracı Testi Başlatıldı ---")

    # Test Senaryosu 1: Uzun metin analizi (SSM/Mamba bekleniyor)
    long_text_problem = "Elimde 500 sayfalık bir hukuk metinleri külliyatı var. Bu metinlerin tamamını tek bir bağlamda analiz edip, içindeki tüm referansları ve ana temaları çıkarmam gerekiyor. Hız ve bellek verimliliği çok önemli."
    decision_1 = decide_architecture(long_text_problem)
    print("\n--- Test 1 Sonucu ---")
    print(json.dumps(decision_1, indent=2, ensure_ascii=False))

    print("\n" + "="*30 + "\n")

    # Test Senaryosu 2: Genel amaçlı sohbet botu (Transformer bekleniyor)
    chatbot_problem = "Müşteri hizmetleri için bir sohbet botu geliştirmek istiyorum. Kullanıcıların genel sorularını anlayıp standart cevaplar vermeli."
    decision_2 = decide_architecture(chatbot_problem)
    print("\n--- Test 2 Sonucu ---")
    print(json.dumps(decision_2, indent=2, ensure_ascii=False))
