# tools/callback_handlers.py

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from typing import Any
from queue import Queue
import json

class StreamingGradioCallbackHandler(BaseCallbackHandler):
    """
    LangChain ajanın adımlarını yakalayan nihai callback handler.
    Artık basit sohbetleri (araçsız) ve araç kullanılan görevleri
    ayırt edip, her ikisini de şeffaf bir şekilde loglayabiliyor.
    """

    def __init__(self, q: Queue):
        """
        Handler'ı bir kuyruk nesnesi ile başlatır ve bir durum bayrağı ekler.
        """
        self.q = q
        # Ajanın bir araç kullanıp kullanmadığını takip etmek için bir bayrak.
        self.tool_used = False

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """
        Ajan bir "Eylem" aldığında (yani bir aracı kullanmaya karar verdiğinde) tetiklenir.
        """
        # Eylem gerçekleştiğinde, bir aracın kullanıldığını işaretliyoruz.
        self.tool_used = True
        
        # Ajanın düşüncesini ve eylemini formatlayıp kuyruğa ekliyoruz.
        log_message = f"🤔 **Düşünce & Eylem:**\n\n```text\n{action.log.strip()}\n```\n\n"
        self.q.put(log_message)

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """
        Bir araç çalışmasını bitirdiğinde ve bir "Gözlem" ürettiğinde tetiklenir.
        """
        # Gözlem sonucunu formatlayıp kuyruğa ekliyoruz.
        # Çıktının JSON olup olmadığını kontrol ederek daha güvenli hale getiriyoruz.
        try:
            # Çıktı bir JSON string ise, daha güzel formatlayalım.
            parsed_output = json.loads(output)
            formatted_output = json.dumps(parsed_output, indent=2, ensure_ascii=False)
            log_message = f"🔬 **Gözlem:**\n\n```json\n{formatted_output}\n```\n"
        except json.JSONDecodeError:
            # Eğer JSON değilse, düz metin olarak ekleyelim.
            log_message = f"🔬 **Gözlem:**\n\n```text\n{output}\n```\n"

        self.q.put(log_message)

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """
        Ajan görevini tamamladığında tetiklenir.
        """
        # Artık hem basit sohbetlerdeki son düşünceyi hem de araç kullanılan
        # görevlerin tamamlandığını logluyoruz.
        if self.tool_used:
            # Eğer bir araç kullanıldıysa, görevin tamamlandığını belirt.
            log_message = "\n✅ **Görev Tamamlandı.** Nihai cevap üretildi."
        else:
            # Eğer hiç araç kullanmadıysa (basit sohbet), sadece son düşüncesini logla.
            log_message = f"🤔 **Son Düşünce:**\n\n```text\n{finish.log.strip()}\n```"
        
        self.q.put(log_message)
        
        # Her görev bittiğinde, bir sonraki görev için bayrağı sıfırla.
        self.tool_used = False

