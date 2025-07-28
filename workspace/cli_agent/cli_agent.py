#!/usr/bin/env python3
"""
CLI Agent - Claude Code tarzı terminal agent
Atölye Şefi'nin terminal versiyonu
"""

import sys
import os
import asyncio
import argparse
from typing import Dict, Any, Optional
import readline  # Terminal history için

# Proje root'unu sys.path'e ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from agents.graph_agent import GraphAgent
    from config import settings
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    print("Ana proje dosyalarına erişilemiyor. Lütfen proje root'undan çalıştırın.")
    sys.exit(1)


class CLIAgent:
    """Claude Code tarzı terminal agent"""
    
    def __init__(self):
        self.agent = None
        self.session_active = True
        self.command_history = []
        
        # Terminal styling
        self.colors = {
            'blue': '\033[94m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'end': '\033[0m'
        }
        
    def print_colored(self, text: str, color: str = 'white'):
        """Renkli terminal çıktısı"""
        print(f"{self.colors.get(color, '')}{text}{self.colors['end']}")
    
    def print_banner(self):
        """Başlangıç banner'ı"""
        banner = f"""
{self.colors['cyan']}{self.colors['bold']}
╔══════════════════════════════════════════════════════════════╗
║                        🔧 ATÖ L Y E  Ş E F İ                ║
║                      CLI Agent - Terminal Mode               ║
╚══════════════════════════════════════════════════════════════╝
{self.colors['end']}
{self.colors['yellow']}⚡ Ultra-fast AI kod çalıştırma sistemi{self.colors['end']}
{self.colors['blue']}📋 Komutlar: /help, /exit, /clear, /history{self.colors['end']}
{self.colors['green']}🚀 Hazır! Kod yazmaya başlayabilirsin...{self.colors['end']}
"""
        print(banner)
    
    def init_agent(self):
        """GraphAgent'ı başlat"""
        try:
            self.print_colored("🧠 Agent başlatılıyor...", 'yellow')
            self.agent = GraphAgent()
            self.print_colored("✅ Agent hazır!", 'green')
            return True
        except Exception as e:
            self.print_colored(f"❌ Agent başlatma hatası: {e}", 'red')
            return False
    
    def handle_special_commands(self, user_input: str) -> bool:
        """Özel komutları işle (/, ile başlayanlar)"""
        if not user_input.startswith('/'):
            return False
            
        command = user_input[1:].strip().lower()
        
        if command == 'help':
            self.show_help()
        elif command == 'exit' or command == 'quit':
            self.session_active = False
            self.print_colored("👋 Görüşmek üzere!", 'cyan')
        elif command == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            self.print_banner()
        elif command == 'history':
            self.show_history()
        elif command == 'status':
            self.show_status()
        else:
            self.print_colored(f"❓ Bilinmeyen komut: /{command}", 'red')
            self.print_colored("💡 /help yazarak mevcut komutları görebilirsin", 'yellow')
        
        return True
    
    def show_help(self):
        """Yardım menüsü"""
        help_text = f"""
{self.colors['bold']}{self.colors['cyan']}🆘 CLI Agent Yardım{self.colors['end']}

{self.colors['yellow']}📋 Özel Komutlar:{self.colors['end']}
  /help     - Bu yardım menüsünü göster
  /exit     - Agent'tan çık
  /clear    - Terminali temizle
  /history  - Komut geçmişini göster
  /status   - Agent durumunu göster

{self.colors['yellow']}🐍 Kod Örnekleri:{self.colors['end']}
  print('Hello World')
  2+2 hesapla
  hesap makinesi yaz
  Python version göster

{self.colors['yellow']}💬 Sohbet Örnekleri:{self.colors['end']}
  merhaba
  nasılsın
  neler yapabilirsin

{self.colors['green']}💡 İpucu: Herhangi bir Python kodu veya görev yazabilirsin!{self.colors['end']}
"""
        print(help_text)
    
    def show_history(self):
        """Komut geçmişini göster"""
        if not self.command_history:
            self.print_colored("📝 Henüz komut geçmişi yok", 'yellow')
            return
        
        self.print_colored("📝 Komut Geçmişi:", 'cyan')
        for i, cmd in enumerate(self.command_history[-10:], 1):  # Son 10 komut
            self.print_colored(f"  {i:2d}. {cmd}", 'white')
    
    def show_status(self):
        """Agent durumunu göster"""
        status = "🟢 Aktif" if self.agent else "🔴 Başlatılmamış"
        commands_count = len(self.command_history)
        
        self.print_colored(f"📊 Agent Durumu: {status}", 'cyan')
        self.print_colored(f"📈 Toplam Komut: {commands_count}", 'cyan')
        if hasattr(self.agent, 'llm'):
            self.print_colored(f"🤖 Model: {settings.AGENT_MODEL_NAME}", 'cyan')
    
    async def process_input(self, user_input: str) -> None:
        """Kullanıcı girdisini işle"""
        if not user_input.strip():
            return
        
        # Geçmişe ekle
        self.command_history.append(user_input)
        
        # Özel komutları kontrol et
        if self.handle_special_commands(user_input):
            return
        
        # Agent'a gönder
        if not self.agent:
            self.print_colored("❌ Agent başlatılmamış! Restart gerekiyor.", 'red')
            return
        
        try:
            self.print_colored("🔄 İşleniyor...", 'yellow')
            
            # Agent'ı çalıştır
            result = self.agent.run(user_input)
            
            # Sonucu göster
            if result and result.get('result'):
                self.print_colored("\n📤 Sonuç:", 'green')
                print(result['result'])
                
                # Debug bilgisi (isteğe bağlı)
                if result.get('intermediate_steps'):
                    step_count = len(result['intermediate_steps'])
                    self.print_colored(f"\n🔧 {step_count} adımda tamamlandı", 'blue')
            else:
                self.print_colored("❌ Sonuç alınamadı", 'red')
                
        except Exception as e:
            self.print_colored(f"❌ Hata: {e}", 'red')
            import traceback
            self.print_colored(f"🔍 Detay: {traceback.format_exc()}", 'red')
    
    def get_user_input(self) -> str:
        """Kullanıcıdan girdi al"""
        try:
            prompt = f"{self.colors['bold']}{self.colors['blue']}atölye-şefi>{self.colors['end']} "
            return input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            self.session_active = False
            self.print_colored("\n👋 Çıkılıyor...", 'cyan')
            return ""
    
    async def run_interactive(self):
        """İnteraktif mod"""
        self.print_banner()
        
        # Agent'ı başlat
        if not self.init_agent():
            self.print_colored("❌ Agent başlatılamadı. Çıkılıyor...", 'red')
            return
        
        # Ana döngü
        while self.session_active:
            try:
                user_input = self.get_user_input()
                if user_input:
                    await self.process_input(user_input)
                    
            except KeyboardInterrupt:
                self.print_colored("\n🛑 Ctrl+C ile çıkış... /exit yazarak düzgün çıkabilirsin", 'yellow')
                continue
            except Exception as e:
                self.print_colored(f"❌ Beklenmeyen hata: {e}", 'red')
                continue
    
    async def run_command(self, command: str):
        """Tek komut çalıştır (script mod)"""
        if not self.init_agent():
            return False
        
        await self.process_input(command)
        return True


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description='Atölye Şefi CLI Agent')
    parser.add_argument('-c', '--command', help='Tek komut çalıştır')
    parser.add_argument('--no-banner', action='store_true', help='Banner gösterme')
    
    args = parser.parse_args()
    
    cli_agent = CLIAgent()
    
    try:
        if args.command:
            # Script modu - tek komut
            asyncio.run(cli_agent.run_command(args.command))
        else:
            # İnteraktif mod
            asyncio.run(cli_agent.run_interactive())
    except KeyboardInterrupt:
        print("\n👋 Çıkış yapılıyor...")
    except Exception as e:
        print(f"❌ Fatal hata: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()