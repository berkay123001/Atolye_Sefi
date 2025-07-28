# CLI Agent - Terminal Atölye Şefi

Claude Code tarzı terminal agent. Atölye Şefi'nin komut satırı versiyonu.

## Özellikler

- 🎨 Renkli terminal arayüzü
- ⚡ Ultra-hızlı intent classification 
- 🐍 Python kod çalıştırma (Modal.com)
- 💬 Doğal dil sohbet
- 📝 Komut geçmişi
- 🔄 İnteraktif ve script modları

## Kullanım

### İnteraktif Mod
```bash
python cli_agent.py
```

### Script Mod (Tek Komut)
```bash
python cli_agent.py -c "print('Hello World')"
python cli_agent.py -c "2+2 hesapla"
```

## Özel Komutlar

- `/help` - Yardım menüsü
- `/exit` - Çıkış
- `/clear` - Ekranı temizle  
- `/history` - Komut geçmişi
- `/status` - Agent durumu

## Örnek Komutlar

### Kod Çalıştırma
```
print('Hello World')
2+2 hesapla
hesap makinesi yaz
Python version göster
```

### Sohbet
```
merhaba
nasılsın  
neler yapabilirsin
```

## Gereksinimler

- Ana Atölye Şefi projesi kurulu olmalı
- GraphAgent ve dependencies hazır olmalı
- Modal.com API anahtarları yapılandırılmış olmalı