# tools/callback_handlers.py

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from typing import Any, Dict, List, Union
from queue import Queue
import json

class StreamingGradioCallbackHandler(BaseCallbackHandler):
    """
    LangChain ajanın adımlarını yakalayan nihai callback handler.
    Artık her türlü araç çıktısını (metin veya sözlük) işleyebilir.
    """

    def __init__(self, q: Queue):
        self.q = q
        self.tool_used = False

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        self.tool_used = True
        log_message = f"🤔 **Düşünce & Eylem:**\n\n```text\n{action.log.strip()}\n```\n\n"
        self.q.put(log_message)

    def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
        """
        Bir araç çalışmasını bitirdiğinde tetiklenir.
        Artık hem metin hem de sözlük formatındaki çıktıları işleyebilir.
        """
        log_message = "🔬 **Gözlem:**\n\n"
        
        # DÜZELTME: Gelen çıktının tipini kontrol ediyoruz.
        if isinstance(output, (dict, list)):
            # Eğer bir sözlük veya liste ise, doğrudan JSON olarak formatla.
            formatted_output = json.dumps(output, indent=2, ensure_ascii=False)
            log_message += f"```json\n{formatted_output}\n```\n"
        elif isinstance(output, str):
            # Eğer metin ise, JSON olup olmadığını kontrol et.
            try:
                parsed_output = json.loads(output)
                formatted_output = json.dumps(parsed_output, indent=2, ensure_ascii=False)
                log_message += f"```json\n{formatted_output}\n```\n"
            except json.JSONDecodeError:
                log_message += f"```text\n{output}\n```\n"
        else:
            # Diğer beklenmedik durumlar için, metne çevir.
            log_message += f"```text\n{str(output)}\n```\n"

        self.q.put(log_message)

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        if self.tool_used:
            log_message = "\n✅ **Görev Tamamlandı.** Nihai cevap üretildi."
        else:
            log_message = f"🤔 **Son Düşünce:**\n\n```text\n{finish.log.strip()}\n```"
        
        self.q.put(log_message)
        self.tool_used = False
