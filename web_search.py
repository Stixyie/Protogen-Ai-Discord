import requests
import random
import json
import os
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

class AdvancedWebSearcher:
    def __init__(self, 
                 log_file='advanced_web_search.log', 
                 results_dir='comprehensive_search_results',
                 search_interval=300,
                 max_queue_size=100):
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

    def web_search(self, query: str, max_results: int = 5) -> Optional[List[Dict]]:
        """
        Perform web search with DuckDuckGo and adaptive DNS handling
        """
        print(f"🔍 Initiating Web Search for: {query}")
        return self.duckduckgo_search(query, max_results)

    def save_search_results(self, query: str, results: List[Dict]) -> Optional[str]:
        """
        Save search results to a timestamped JSON file
        
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
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'query': query,
                    'timestamp': timestamp,
                    'results': results
                }, f, ensure_ascii=False, indent=4)
            
            logging.info(f"Search results saved to {filename}")
            return filename
        
        except Exception as e:
            logging.error(f"Error saving search results: {e}")
            return None

    @classmethod
    def run_as_admin(cls):
        """
        Attempt to run the script with administrative privileges
        """
        try:
            if sys.platform.startswith('win'):
                # Windows-specific admin elevation
                import ctypes
                if ctypes.windll.shell32.IsUserAnAdmin():
                    return True
                else:
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                    sys.exit(0)
            elif sys.platform.startswith('linux'):
                # Linux sudo method
                subprocess.run(['sudo', sys.executable] + sys.argv)
                sys.exit(0)
            elif sys.platform.startswith('darwin'):
                # macOS sudo method
                subprocess.run(['sudo', sys.executable] + sys.argv)
                sys.exit(0)
        except Exception as e:
            logging.error(f"Could not elevate privileges: {e}")
            return False

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
    
    # Ensure admin privileges
    # searcher.run_as_admin()
    
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
