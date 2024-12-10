import os
import requests
import random
import json
import sys
import time
import logging
import re
import socket
import ipaddress
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import urllib.parse
import subprocess
import change_dns
import threading
from datetime import datetime, timedelta

class AdvancedWebSearcher:
    def __init__(self, 
                 log_file='advanced_web_search.log', 
                 results_dir='comprehensive_search_results',
                 search_interval=300,
                 max_queue_size=100,
                 memory_size=1_000_000,  # 1 milyon konu
                 memory_retention_days=30):  # 30 gün sonra yenileme
        """
        Advanced Web Searcher with DuckDuckGo and adaptive DNS management
        """
        self.dns_servers = change_dns.DNS_SERVERS
        self.setup_logging(log_file)
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        self.search_interval = search_interval
        self.max_queue_size = max_queue_size
        
        # User-Agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        # Predefined search topics
        self.default_topics = [
            "latest AI advancements",
            "global technology trends",
            "cybersecurity updates",
            "machine learning breakthroughs",
            "renewable energy innovations"
        ]
        
        # Araştırma hafızası
        self.research_memory = []
        self.memory_size = memory_size

        # Gelişmiş araştırma hafızası
        self.comprehensive_research_memory = {
            'topics': {},  # {topic_hash: topic_data}
            'last_updated': {}  # Son güncellenme zamanları
        }
        self.memory_retention_days = memory_retention_days

    def setup_logging(self, log_file: str):
        """Configure logging with console output"""
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)  # Add console output
            ]
        )

    def duckduckgo_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Perform web search using DuckDuckGo with adaptive DNS handling
        """
        print(f"🔍 Searching DuckDuckGo for: {query}")
        
        try:
            # DuckDuckGo search URL
            search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            
            # Headers to mimic browser request
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # Perform search request
            response = requests.get(search_url, headers=headers, timeout=10)
            
            # Check for DNS or connection issues (202 error)
            if response.status_code == 202:
                print("⚠️ DNS Resolution Issue Detected. Changing DNS...")
                self.adaptive_dns_change()
                # Retry search after DNS change
                response = requests.get(search_url, headers=headers, timeout=10)
            
            # Parse search results
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.find_all('div', class_='result__body')[:max_results]:
                title_elem = result.find('h2', class_='result__title')
                link_elem = result.find('a', class_='result__url')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and link_elem and snippet_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'link': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True)
                    })
            
            print(f"✅ Found {len(results)} search results")
            return results
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Search Error: {e}")
            return []

    def adaptive_dns_change(self):
        """
        Dynamically change DNS when connection issues are detected
        """
        print("🔄 Attempting Adaptive DNS Change...")
        
        try:
            # Randomly select a new DNS server
            new_dns = random.choice(self.dns_servers)
            print(f"🌐 Selected DNS Server: {new_dns}")
            
            # Use change_dns script to modify DNS
            if change_dns.change_dns_without_admin([new_dns]):
                print(f"✅ DNS Successfully Changed to {new_dns}")
                
                # Optional: Small delay to allow DNS propagation
                time.sleep(2)
                return True
            else:
                print("❌ Failed to Change DNS")
                return False
        
        except Exception as e:
            print(f"❌ DNS Change Error: {e}")
            return False

    def web_search(self, query: str, max_results: int = 300) -> Optional[List[Dict]]:
        """
        Perform comprehensive web search across multiple sources
        
        :param query: Search query
        :param max_results: Maximum number of search results to retrieve
        :return: List of search results
        """
        print(f"🌐 Initiating Comprehensive Web Search for: {query}")
        
        # List to store aggregated results
        all_results = []
        
        # Multiple search strategies
        search_strategies = [
            # DuckDuckGo search
            lambda q, max_r: self.duckduckgo_search(q, max_r // 3),
            
            # Additional search methods can be added here
            # For example, you could integrate other search APIs or web scraping techniques
        ]
        
        # Distribute max results across search strategies
        results_per_strategy = max_results // len(search_strategies)
        
        # Perform searches using different strategies
        for strategy in search_strategies:
            try:
                strategy_results = strategy(query, results_per_strategy)
                all_results.extend(strategy_results)
            except Exception as e:
                print(f"❌ Search strategy failed: {e}")
        
        # Deduplicate results based on link
        unique_results = []
        seen_links = set()
        for result in all_results:
            if result['link'] not in seen_links:
                unique_results.append(result)
                seen_links.add(result['link'])
                
                # Break if we've reached max results
                if len(unique_results) >= max_results:
                    break
        
        print(f"✅ Found {len(unique_results)} unique search results")
        return unique_results

    def save_search_results(self, query: str, results: List[Dict]) -> Optional[str]:
        """
        Save search results to a timestamped JSON file and update research memory
        
        :param query: Original search query
        :param results: Search results to save
        :return: Path to saved results file
        """
        try:
            timestamp = int(time.time())
            filename = os.path.join(
                self.results_dir, 
                f"search_results_{timestamp}.json"
            )
            
            # Araştırma kaydı oluştur
            research_entry = {
                'timestamp': timestamp,
                'query': query,
                'results_file': filename,
                'results_count': len(results)
            }
            
            # Hafızaya ekle
            self.research_memory.append(research_entry)
            
            # Hafıza boyutunu kontrol et
            if len(self.research_memory) > self.memory_size:
                # En eski araştırmayı sil
                oldest_research = self.research_memory.pop(0)
                
                # İlgili dosyayı da silebilirsiniz (opsiyonel)
                try:
                    os.remove(oldest_research['results_file'])
                except Exception as e:
                    print(f"❌ Eski araştırmaya ait dosya silinemedi: {e}")
            
            # Sonuçları JSON'a kaydet
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'query': query,
                    'timestamp': timestamp,
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            
            return filename
        
        except Exception as e:
            logging.error(f"Error saving search results: {e}")
            return None

    def get_research_memory(self, last_n=None):
        """
        Kayıtlı araştırmaları döndür
        
        :param last_n: Son n araştırmayı getir (opsiyonel)
        :return: Araştırma hafızası listesi
        """
        if last_n is not None:
            return self.research_memory[-last_n:]
        return self.research_memory

    def search_research_memory(self, keyword):
        """
        Hafızadaki araştırmalarda anahtar kelimeye göre arama yap
        
        :param keyword: Aranacak anahtar kelime
        :return: Eşleşen araştırmalar
        """
        matched_researches = []
        for research in self.research_memory:
            if keyword.lower() in research['query'].lower():
                # Detaylı sonuçları yükle
                try:
                    with open(research['results_file'], 'r', encoding='utf-8') as f:
                        full_research = json.load(f)
                        matched_researches.append(full_research)
                except Exception as e:
                    print(f"❌ Araştırma dosyası okunamadı: {e}")
        
        return matched_researches

    def generate_topic_hash(self, query):
        """
        Benzersiz bir konu hash'i oluştur
        
        :param query: Araştırma konusu
        :return: Hash değeri
        """
        import hashlib
        return hashlib.md5(query.lower().encode()).hexdigest()

    def is_topic_expired(self, topic_hash):
        """
        Konunun süresinin dolup dolmadığını kontrol et
        
        :param topic_hash: Konu hash'i
        :return: Süre dolmuşsa True, aksi halde False
        """
        # datetime ve timedelta zaten import edildi
        
        if topic_hash not in self.comprehensive_research_memory['last_updated']:
            return True
        
        last_updated = self.comprehensive_research_memory['last_updated'][topic_hash]
        expiration_time = last_updated + timedelta(days=self.memory_retention_days)
        
        return datetime.now() > expiration_time

    def save_comprehensive_research(self, query, results):
        """
        Kapsamlı araştırmaları kaydet
        
        :param query: Araştırma konusu
        :param results: Araştırma sonuçları
        :return: Kaydedilen dosyanın yolu
        """
        try:
            # Konu için benzersiz hash oluştur
            topic_hash = self.generate_topic_hash(query)
            
            # Mevcut hafızadaki konu sayısını kontrol et
            if len(self.comprehensive_research_memory['topics']) >= self.memory_size:
                # En eski konuyu sil
                oldest_topic = min(
                    self.comprehensive_research_memory['last_updated'], 
                    key=self.comprehensive_research_memory['last_updated'].get
                )
                del self.comprehensive_research_memory['topics'][oldest_topic]
                del self.comprehensive_research_memory['last_updated'][oldest_topic]
            
            # Araştırma sonuçlarını kaydet
            timestamp = int(time.time())
            filename = os.path.join(
                self.results_dir, 
                f"comprehensive_research_{topic_hash}_{timestamp}.json"
            )
            
            research_entry = {
                'query': query,
                'timestamp': timestamp,
                'results': results
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(research_entry, f, ensure_ascii=False, indent=2)
            
            # Hafızaya ekle
            self.comprehensive_research_memory['topics'][topic_hash] = filename
            self.comprehensive_research_memory['last_updated'][topic_hash] = datetime.now()
            
            return filename
        
        except Exception as e:
            logging.error(f"Kapsamlı araştırmakaydedilemedi: {e}")
            return None

    def find_relevant_research(self, user_query, max_results=10):
        """
        Kullanıcı sorusuna en ilgili araştırmaları bul
        
        :param user_query: Kullanıcı sorusu
        :param max_results: Maksimum sonuç sayısı
        :return: İlgili araştırmasonuçları
        """
        relevant_researches = []
        
        # Tüm konuları kontrol et
        for topic_hash, filename in self.comprehensive_research_memory['topics'].items():
            # Süre dolmuş mu kontrol et
            if self.is_topic_expired(topic_hash):
                # Süre dolmuş konuyu sil
                del self.comprehensive_research_memory['topics'][topic_hash]
                del self.comprehensive_research_memory['last_updated'][topic_hash]
                continue
            
            try:
                # Araştırma dosyasını yükle
                with open(filename, 'r', encoding='utf-8') as f:
                    research = json.load(f)
                
                # Kullanıcı sorusuyla ilgili mi kontrol et
                similarity_score = self.calculate_query_similarity(user_query, research['query'])
                
                if similarity_score > 0.5:  # Benzerlik eşiği
                    relevant_researches.append({
                        'query': research['query'],
                        'results': research['results'],
                        'similarity_score': similarity_score
                    })
            
            except Exception as e:
                print(f"Araştırma yüklenirken hata: {e}")
        
        # Benzerlik puanına göre sırala
        relevant_researches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return relevant_researches[:max_results]

    def calculate_query_similarity(self, query1, query2):
        """
        İki sorgu arasındaki benzerliği hesapla
        
        :param query1: İlk sorgu
        :param query2: İkinci sorgu
        :return: Benzerlik skoru (0-1 arası)
        """
        import difflib
        
        # Kelimeleri küçük harfe çevir ve ayır
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        # Ortak kelimelerin oranını hesapla
        common_words = words1.intersection(words2)
        similarity = len(common_words) / max(len(words1), len(words2))
        
        return similarity

    def background_research_loop(self, interval=3600):
        """
        Arka planda sürekli araştırmayap
        
        :param interval: Araştırmalar arası süre (saniye)
        """
        while True:
            try:
                # Güncel ve çeşitli konularda araştırmayap
                topics = [
                    "Yapay Zeka Teknolojileri",
                    "Küresel Teknoloji Trendleri",
                    "Bilişim Güvenliği Güncel Gelişmeleri",
                    "Makine Öğrenmesi Son Yenilikler",
                    "Sürdürülebilir Teknoloji",
                    "Dijital Dönüşüm",
                    "Kripto Para ve Blockchain",
                    "Biyoteknoloji Araştırmaları",
                    "Uzay Teknolojileri",
                    "Çevre ve Yeşil Teknolojiler"
                ]
                
                # Rastgele bir konu seç
                topic = random.choice(topics)
                
                print(f"🔬 Arka Plan Araştırması Başlatılıyor: {topic}")
                
                # Kapsamlı web araması yap
                results = self.web_search(topic, max_results=50)
                
                # Araştırma sonuçlarını kaydet
                if results:
                    saved_file = self.save_comprehensive_research(topic, results)
                    print(f"💾 Araştırma Sonuçları Kaydedildi: {saved_file}")
                
                # Belirli aralıklarla araştırma yap
                time.sleep(interval)
            
            except Exception as e:
                print(f"❌ Arka plan araştırmaları hatası: {e}")
                time.sleep(interval)

    def start_background_research(self, interval=3600):
        """
        Arka plan araştırmaları thread'ini başlat
        
        :param interval: Araştırmalar arası süre (saniye)
        """
        import threading
        
        research_thread = threading.Thread(
            target=self.background_research_loop, 
            args=(interval,), 
            daemon=True
        )
        research_thread.start()
        print("🌐 Arka Plan Araştırma Thread'i Başlatıldı")

    def generate_research_prompt(self, last_n=5):
        """
        Araştırma hafızasından prompt oluştur
        
        :param last_n: Son n araştırmayı prompt'a ekle
        :return: Araştırma bilgilerini içeren prompt metni
        """
        research_prompt = "🌐 BACKGROUND RESEARCH MEMORY:\n\n"
        
        # Son n araştırmayı al
        recent_researches = self.get_research_memory(last_n=last_n)
        
        if not recent_researches:
            return "No recent research found."
        
        for idx, research in enumerate(recent_researches, 1):
            try:
                # Tam araştırmayı yükle
                with open(research['results_file'], 'r', encoding='utf-8') as f:
                    full_research = json.load(f)
                
                research_prompt += f"Research {idx}:\n"
                research_prompt += f"- Topic: {full_research['query']}\n"
                research_prompt += f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(research['timestamp']))}\n"
                research_prompt += f"- Results Count: {len(full_research['results'])}\n"
                
                # İlk 3 sonucu özet olarak ekle
                research_prompt += "- Top Insights:\n"
                for result in full_research['results'][:3]:
                    research_prompt += f"  * {result['title']}: {result['snippet'][:100]}...\n"
                
                research_prompt += "\n"
            
            except Exception as e:
                print(f"❌ Araştırma detayları yüklenemedi: {e}")
        
        return research_prompt

    def get_research_context(self, last_n=5):
        """
        Araştırma hafızasını bir sözlük olarak döndür
        
        :param last_n: Son n araştırmayı context'e ekle
        :return: Araştırma bilgilerini içeren sözlük
        """
        research_context = {
            'research_memory': []
        }
        
        # Son n araştırmayı al
        recent_researches = self.get_research_memory(last_n=last_n)
        
        for research in recent_researches:
            try:
                # Tam araştırmayı yükle
                with open(research['results_file'], 'r', encoding='utf-8') as f:
                    full_research = json.load(f)
                
                research_entry = {
                    'query': full_research['query'],
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(research['timestamp'])),
                    'results_count': len(full_research['results']),
                    'top_results': full_research['results'][:3]
                }
                
                research_context['research_memory'].append(research_entry)
            
            except Exception as e:
                print(f"❌ Araştırma detayları yüklenemedi: {e}")
        
        return research_context

def main():
    """Test the web search functionality"""
    searcher = AdvancedWebSearcher()
    test_queries = [
        "latest AI technologies",
        "global technology trends",
        "machine learning breakthroughs"
    ]
    
    for query in test_queries:
        results = searcher.web_search(query)
        print("\n" + "="*50)

    # Initialize advanced web searcher
    searcher = AdvancedWebSearcher()
    
    # Continuous search loop
    while True:
        try:
            # Get user input or use default topics
            query = input("Enter search query (or 'quit' to exit): ").strip()
            
            if query.lower() == 'quit':
                break
            
            if not query:
                query = random.choice(searcher.default_topics)
            
            # Perform web search
            results = searcher.web_search(query)
            
            if results:
                # Display and save results
                print("\nSearch Results:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['title']}")
                    print(f"   Link: {result['link']}")
                    print(f"   Snippet: {result['snippet']}")
                
                # Save results
                saved_file = searcher.save_search_results(query, results)
                print(f"\nResults saved to {saved_file}")
            else:
                print("No results found.")
        
        except KeyboardInterrupt:
            print("\nSearch interrupted.")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()
