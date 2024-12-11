import os
import json
import logging
from typing import List, Dict, Any
import tiktoken
from groq import Groq
from datetime import datetime, timedelta
import uuid
import asyncio

# Gelişmiş logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('advanced_memory.log', encoding='utf-8', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class AdvancedMemoryManager:
    def __init__(self, memory_dir: str = 'memory', max_memory_days: int = 365):
        """
        Gelişmiş hafıza yönetimi
        
        Args:
            memory_dir (str): Hafıza dizini
            max_memory_days (int): Hafızada tutulacak maksimum gün sayısı
        """
        self.memory_dir = memory_dir
        self.max_memory_days = max_memory_days
        
        # Kullanıcı bazında hafıza dizinleri
        self.user_memory_dir = os.path.join(memory_dir, 'users')
        os.makedirs(self.user_memory_dir, exist_ok=True)

    def save_user_message(self, user_id: str, message: str, is_bot: bool = False, context: Dict = None):
        """
        Kullanıcı mesajlarını kullanıcı bazında kaydet
        
        Args:
            user_id (str): Kullanıcı ID'si
            message (str): Mesaj içeriği
            is_bot (bool): Mesaj bota mı ait
            context (Dict, optional): Ek bağlam bilgisi
        """
        try:
            user_dir = os.path.join(self.user_memory_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            memory_entry = {
                "timestamp": timestamp,
                "is_bot": is_bot,
                "message": message,
                "context": context or {}
            }
            
            filename = f"msg_{timestamp.replace(':', '-')}.json"
            filepath = os.path.join(user_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(memory_entry, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Kullanıcı mesajı kaydedildi: {user_id} - {filename}")
            
            # Eski kayıtları temizle
            self.clean_old_memories(user_dir)
        except Exception as e:
            logger.error(f"Mesaj kaydetme hatası: {e}")

    def clean_old_memories(self, user_dir: str):
        """
        Belirli günden eski hafıza kayıtlarını temizle
        
        Args:
            user_dir (str): Kullanıcı hafıza dizini
        """
        try:
            now = datetime.utcnow()
            for filename in os.listdir(user_dir):
                filepath = os.path.join(user_dir, filename)
                file_time = datetime.fromisoformat(filename.split('_')[1].replace('-', ':').replace('.json', ''))
                
                if (now - file_time) > timedelta(days=self.max_memory_days):
                    os.remove(filepath)
                    logger.info(f"Eski hafıza kaydı silindi: {filename}")
        except Exception as e:
            logger.error(f"Hafıza temizleme hatası: {e}")

    def get_user_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Kullanıcının son mesaj geçmişini al
        
        Args:
            user_id (str): Kullanıcı ID'si
            limit (int): Getirilecek maksimum mesaj sayısı
        
        Returns:
            List[Dict]: Kullanıcı mesaj geçmişi
        """
        user_dir = os.path.join(self.user_memory_dir, user_id)
        
        if not os.path.exists(user_dir):
            return []
        
        # Dosyaları zamana göre sırala
        message_files = sorted(
            [f for f in os.listdir(user_dir) if f.startswith('msg_')],
            reverse=True
        )
        
        conversation_history = []
        for filename in message_files[:limit]:
            filepath = os.path.join(user_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation_history.append(json.load(f))
        
        return conversation_history

class GroqMemoryIntegrator:
    def __init__(self, groq_api_key: str, memory_manager: AdvancedMemoryManager):
        """
        Groq API ile hafıza entegrasyonu
        
        Args:
            groq_api_key (str): Groq API anahtarı
            memory_manager (AdvancedMemoryManager): Hafıza yöneticisi
        """
        self.client = Groq(api_key=groq_api_key)
        self.memory_manager = memory_manager
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def analyze_conversation_context(self, user_id: str) -> str:
        """
        Kullanıcı sohbet geçmişini analiz et
        
        Args:
            user_id (str): Kullanıcı ID'si
        
        Returns:
            str: Sohbet bağlamı analizi
        """
        try:
            conversation_history = self.memory_manager.get_user_conversation_history(user_id)
            
            if not conversation_history:
                return "Henüz bir sohbet geçmişi yok."
            
            # Sohbet geçmişini metne çevir
            history_text = "\n".join([
                f"{'Bot' if msg['is_bot'] else 'Kullanıcı'}: {msg['message']}" 
                for msg in conversation_history
            ])
            
            # Groq API ile analiz
            context_analysis_prompt = f"""
            Aşağıdaki sohbet geçmişini analiz et ve kullanıcının duygusal durumu, ilgi alanları ve konuşma eğilimleri hakkında detaylı bir özet çıkar:

            Sohbet Geçmişi:
            {history_text}

            Analiz:
            """
            
            response = self.client.chat.completions.create(
                messages=[{"role": "system", "content": context_analysis_prompt}],
                model="llama-3.3-70b-versatile"
            )
            
            analysis = response.choices[0].message.content
            logger.info(f"Kullanıcı {user_id} için sohbet analizi:\n{analysis}")
            
            return analysis
        
        except Exception as e:
            logger.error(f"Sohbet analizi hatası: {e}")
            return "Sohbet analizi sırasında bir hata oluştu."

# Örnek kullanım
def main():
    # Örnek kullanım senaryosu
    memory_manager = AdvancedMemoryManager()
    groq_key = os.getenv('GROQ_API_KEY', 'your_groq_api_key')
    memory_integrator = GroqMemoryIntegrator(groq_key, memory_manager)
    
    # Örnek kullanıcı ID'si
    user_id = "1234567890"
    
    # Mesaj kaydetme örneği
    memory_manager.save_user_message(user_id, "Merhaba, nasılsın?", is_bot=False)
    memory_manager.save_user_message(user_id, "İyiyim, teşekkür ederim!", is_bot=True)
    
    # Sohbet analizi
    analysis = asyncio.run(memory_integrator.analyze_conversation_context(user_id))
    print("Sohbet Analizi:", analysis)

if __name__ == "__main__":
    main()
