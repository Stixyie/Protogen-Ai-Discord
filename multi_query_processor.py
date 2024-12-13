import os
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class MultiQueryProcessor:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    def web_search(self, query):
        """Simulate a web search (replace with actual web search API if available)"""
        try:
            response = requests.get(f"https://www.google.com/search?q={query}")
            return response.text[:500]  # Limit response for demonstration
        except Exception as e:
            return f"Web search error: {str(e)}"
    
    def generate_chain_of_thought(self, queries):
        """Process multiple queries using chain of thought"""
        results = {}
        
        for query in queries:
            # Step 1: Web Search
            web_result = self.web_search(query)
            
            # Step 2: LLM Analysis
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert at extracting precise information from web search results."},
                    {"role": "user", "content": f"Analyze this web search result for the query '{query}': {web_result}. Extract the most relevant numerical information."}
                ],
                model="llama3-70b-8192"
            )
            
            # Store result
            results[query] = chat_completion.choices[0].message.content
        
        return results
    
    def process_queries(self, queries):
        """Main method to process multiple queries"""
        print("🔍 Starting Multi-Query Processing...")
        results = self.generate_chain_of_thought(queries)
        
        for query, result in results.items():
            print(f"\n📌 Query: {query}")
            print(f"📊 Result: {result}")
        
        return results

# Example Usage
if __name__ == "__main__":
    processor = MultiQueryProcessor()
    currency_queries = [
        "1 dolar kaç tl",
        "1 euro kaç tl", 
        "1 sterlin kaç tl"
    ]
    processor.process_queries(currency_queries)
