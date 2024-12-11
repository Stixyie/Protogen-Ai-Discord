# 🧠 Protogen AI Gelişmiş Hafıza İşlemcisi

## 🌟 Genel Bakış
Protogen AI'nın gelişmiş hafıza yönetim sistemi, kullanıcı etkileşimlerini akıllıca işleyen ve analiz eden bir bellek işlemcisidir.

## ✨ Özellikler
- 👤 Kullanıcı bazında dinamik hafıza gruplandırması
- 💾 Sınırsız ve kalıcı sohbet geçmişi depolama
- 🤖 Groq AI ile otomatik sohbet bağlamı analizi
- 🕰️ Otomatik hafıza temizleme ve yönetme
- 📊 Detaylı konuşma geçmişi ve kullanıcı eğilimi çıkarma

## 🛠️ Kurulum
1. Gerekli bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

2. Groq API anahtarınızı ortam değişkenine ekleyin:
   ```bash
   export GROQ_API_KEY='your_api_key_here'
   ```

## 💬 Kullanım Örneği
```python
# Hafıza yöneticisini başlatma
memory_manager = AdvancedMemoryManager()
memory_integrator = GroqMemoryIntegrator(groq_key, memory_manager)

# Kullanıcı mesajını kaydetme
memory_manager.save_user_message(
    user_id="discord_user_123", 
    message="Merhaba, nasılsın?", 
    is_bot=False
)

# Sohbet bağlamını analiz etme
conversation_analysis = await memory_integrator.analyze_conversation_context("discord_user_123")
print(conversation_analysis)
```

## 📂 Hafıza Dosyası Yapısı
Her kullanıcı için ayrı bir dizinde JSON formatında hafıza dosyaları:
```json
{
    "timestamp": "2024-01-01T12:34:56Z",
    "is_bot": false,
    "message": "Kullanıcı mesajı",
    "context": {
        "ek_bilgiler": "varsa_buraya_eklenebilir"
    }
}
```

## 🔍 Detaylı Analiz
Groq AI ile her kullanıcı için:
- Duygusal durum analizi
- Konuşma eğilimleri
- İlgi alanları tespiti

## 🚨 Günlükleme
Tüm işlemler `advanced_memory.log` dosyasında detaylı olarak kaydedilir.

## 🔒 Güvenlik
- Kullanıcı verileri güvenli ve ayrı dizinlerde saklanır
- Maksimum hafıza günü ayarlanabilir
- Hassas bilgiler loglanmaz
