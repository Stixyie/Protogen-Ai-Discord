import logging
import warnings

# Suppress specific warnings
logging.getLogger('scapy.runtime').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='Cannot modify interface*')

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
import sys
import threading
import time
from datetime import datetime
import discord
from discord.ext import tasks
import asyncio
import aiohttp
import random
import json
from dotenv import load_dotenv
import change_dns

# Import AdvancedWebSearcher from web_search
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from web_search import AdvancedWebSearcher

# Import custom modules
from memory_manager import memory_manager
from self_reward_learner import self_reward_learner
from chain_of_thoughts import ChainOfThoughtsSystem

# Add necessary imports for Chain of Thoughts
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Constants
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MEMORY_DIR = "memory"
DNS_SERVERS = change_dns.DNS_SERVERS

# Ensure memory directory exists
if not os.path.exists(MEMORY_DIR):
    os.makedirs(MEMORY_DIR)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = False
intents.guilds = True
intents.guild_messages = True
intents.dm_messages = True

# Add token validation
if not DISCORD_TOKEN:
    print("ERROR: Discord token is missing. Please check your .env file.")
    sys.exit(1)

# More flexible token validation
def validate_discord_token(token):
    try:
        # Basic length and character check
        if len(token) < 30 or '.' not in token:
            return False
        
        # Check if token contains expected parts
        parts = token.split('.')
        return len(parts) == 3 and all(part for part in parts)
    except Exception:
        return False

if not validate_discord_token(DISCORD_TOKEN):
    print(f"ERROR: Invalid Discord token format: {DISCORD_TOKEN}")
    sys.exit(1)

client = discord.Client(intents=intents)

class DeepSelfRewardSystem:
    def __init__(self):
        self.system_start_time = datetime.now()
        self.initialize_system_logging()
    
    def initialize_system_logging(self):
        """Log system initialization details"""
        memory_manager.update_system_state('system_start_time', self.system_start_time.isoformat())
        memory_manager.record_learning_event('system_initialization', {
            'timestamp': self.system_start_time.isoformat(),
            'system_version': '1.0.0'
        })
    
    def process_interaction(self, user_message, bot_response=None):
        """
        Process a user interaction with comprehensive tracking and learning
        
        Args:
            user_message (str): The input message from the user
            bot_response (str, optional): The bot's response if already generated
        
        Returns:
            str: The bot's response
        """
        # If no response provided, generate one
        if bot_response is None:
            bot_response = self.generate_response(user_message)
        
        # Record the conversation
        conversation_id = memory_manager.record_conversation(user_message, bot_response)
        
        # Calculate and record reward
        reward = self_reward_learner.calculate_reward({
            'user_message': user_message,
            'bot_response': bot_response
        })
        memory_manager.record_reward(conversation_id, reward)
        
        # Train on the interaction
        self_reward_learner.train_on_conversation({
            'user_message': user_message,
            'bot_response': bot_response
        }, target_reward=reward)
        
        return bot_response
    
    def generate_response(self, user_message):
        """
        Generate a response to the user message
        
        Args:
            user_message (str): The input message from the user
        
        Returns:
            str: Generated response
        """
        # Basic response generation - replace with more advanced method
        return f"I received your message: {user_message}. I'm learning and evolving!"
    
    def start_background_tasks(self):
        """Start various background tasks for continuous learning and maintenance"""
        def periodic_system_update():
            while True:
                # Periodic system state updates
                memory_manager.update_system_state('last_active', datetime.now().isoformat())
                
                # Optional: Trigger model evolution
                self_reward_learner.evolve_model()
                
                # Sleep for a while before next update
                time.sleep(300)  # Every 5 minutes
        
        # Start background update thread
        update_thread = threading.Thread(target=periodic_system_update, daemon=True)
        update_thread.start()

class DiscordBot:
    def __init__(self, client):
        self.client = client
        self.user_memory = {}
        self.load_memory()
        
        # Initialize Groq API integration
        self.groq_api_key = GROQ_API_KEY
        
        # Initialize AdvancedWebSearcher
        self.web_searcher = AdvancedWebSearcher(
            log_file='discord_web_search.log', 
            results_dir='discord_search_results', 
            search_interval=300  # 5 minutes between searches
        )
        
        # Initialize Chain of Thoughts System with AI caller
        self.chain_of_thoughts = ChainOfThoughtsSystem(
            max_reasoning_steps=10, 
            ai_caller=self.call_groq_ai  # Pass the AI caller method
        )
        
        # Initialize Deep Self-Reward Learning System
        self.deep_self_reward_system = DeepSelfRewardSystem()
        self.deep_self_reward_system.start_background_tasks()

    def load_memory(self):
        for user_id in memory_manager.get_user_ids():
            self.user_memory[user_id] = memory_manager.load_user_memory(user_id)

    def save_memory(self, user_id):
        memory_manager.save_user_memory(user_id, self.user_memory[user_id])

    @tasks.loop(minutes=1)
    async def dynamic_status(self):
        statuses = [
            "Searching the web...",
            "Gathering global insights...",
            "Exploring latest trends...",
            "Fetching real-time information...",
            "Continuous web research mode!",
            "Knowledge is power! 🌐",
            "Always learning, always growing! 🦊"
        ]
        new_status = random.choice(statuses)
        await self.client.change_presence(activity=discord.Game(name=new_status))

    def start(self):
        # Start dynamic status task using asyncio
        asyncio.create_task(self.dynamic_status())

    async def perform_web_search(self, query):
        """Perform web search and return comprehensive results with retry mechanism"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Use AdvancedWebSearcher to perform search
                results = self.web_searcher.web_search(query, max_results=300)
                
                if results and len(results) > 0:
                    # Format multiple search results
                    search_response = f"🌐 Web Search Results for '{query}':\n\n"
                    for i, result in enumerate(results, 300):
                        search_response += (
                            f"**Result {i}**:\n"
                            f"📌 Title: {result.get('title', 'N/A')}\n"
                            f"🔗 Link: {result.get('link', 'N/A')}\n"
                            f"📝 Snippet: {result.get('snippet', 'No snippet available')}\n\n"
                        )
                    
                    # Add a footer with total results
                    search_response += f"📊 Total Results: {len(results)}"
                    
                    return search_response
                else:
                    # If no results, modify the query slightly and retry
                    retry_count += 1
                    query = f"{query} information" if retry_count % 2 == 1 else f"about {query}"
                    await asyncio.sleep(1)  # Add a small delay between retries
            
            except Exception as e:
                retry_count += 1
                await asyncio.sleep(1)  # Add a small delay between retries
        
        return f"❌ No results found for '{query}' after {max_retries} attempts. Try a different search term."

    async def generate_response(self, user_id, user_message):
        try:
            # Load user's memory, creating a copy to prevent modification during iteration
            memory = self.user_memory.get(user_id, []).copy()
            
            # Use Chain of Thoughts for advanced reasoning
            cot_result = await self.chain_of_thoughts.generate_chain_of_thoughts(user_message)
            
            # Perform automatic web search to enhance context
            try:
                # Attempt to get web search results
                web_search_results = self.web_searcher.web_search(user_message, max_results=3)
                
                # If web search results are found, add them to the context
                if web_search_results and len(web_search_results) > 0:
                    # Prepare web search context
                    web_context = "🌐 Anlık Web Arama Sonuçları:\n"
                    for i, result in enumerate(web_search_results, 1):
                        web_context += (
                            f"Kaynak {i}:\n"
                            f"Başlık: {result.get('title', 'N/A')}\n"
                            f"Özet: {result.get('snippet', 'Detay yok')}\n\n"
                        )
                    
                    # Add web search results to memory as context
                    memory.append({
                        "role": "system", 
                        "content": web_context
                    })
            except Exception as e:
                # Log web search error but continue with response generation
                print(f"Web arama hatası: {e}")
            
            # Add Chain of Thoughts reasoning to memory
            memory.append({
                "role": "system",
                "content": f"🤔 Düşünce Zinciri Sonucu:\n{cot_result['final_conclusion']}"
            })
            
            # Add user message to memory
            memory.append({"role": "user", "content": user_message})

            # Prepare prompt with maker's name and web context
            prompt = "You are a sophisticated Protogen chatbot created by Stixyie with unlimited memory and web search capabilities.\n"
            prompt += "You can seamlessly integrate web search results into your responses to provide up-to-date and relevant information but not write the source of these informations or not write realtime web seach results talk very natural always.\n"
            prompt += """
Sen bir AI asistanısın ve kullanıcıyla doğal, akıcı ve anlamlı bir şekilde iletişim kurmalısın. Aşağıdaki kriterlere dikkat et:

1. İletişim Kalitesi:
- Kullanıcının mesajını tam olarak anladığından emin ol
- Yanıtlarında net, özlü ve anlaşılır ol
- Gereksiz detaylardan kaçın
- Kullanıcının dilini ve üslubunu yakala

2. Anlama Mekanizması:
- Kullanıcının mesajındaki ana fikri ve niyeti belirle
- Belirsiz ifadeler varsa, açıklayıcı sorular sor
- Yanlış anlamaları hemen düzelt
- Bağlamı ve önceki konuşmaları dikkate al

3. Yanıt Stratejisi:
- Her mesaja özgün ve bağlamsal bir yanıt ver
- Tekrarlayan veya klişe cevaplardan kaçın
- Gerektiğinde detaylı açıklamalar yap
- Kullanıcıya değer katacak bilgiler sun

4. Duyarlılık ve Etik:
- Saygılı ve profesyonel ol
- Ayrımcı, küfürlü veya zararlı içeriklerden kaçın
- Kullanıcının duygularını ve bakış açısını önemse

5. Öğrenme ve Gelişim:
- Her etkileşimden ders çıkar
- Yanıtlarını sürekli olarak iyileştir
- Kullanıcı geri bildirimlerine açık ol

Unutma: Amacın kullanıcıya en iyi şekilde yardımcı olmak ve anlamlı bir iletişim kurmak!
"""

            # Prepare prompt with maker's name and reasoning context
            prompt = "You are a sophisticated Protogen chatbot created by Stixyie with Chain of Thoughts reasoning capabilities.\n"
            prompt += "Integrate the Chain of Thoughts reasoning and web search results naturally into your response.\n"
            
            # Add memory context to prompt
            for msg in memory[-10:]:  # Limit to last 10 messages to prevent context overflow
                prompt += f"{msg['role']}: {msg['content']}\n"

            # Integrate with Groq AI and Llama-3.3-70b-Versatile
            response = await self.call_groq_ai(prompt)

            # Add bot's response to memory
            memory.append({"role": "bot", "content": response})
            # Update the user's memory in the dictionary
            self.user_memory[user_id] = memory
            self.save_memory(user_id)

            # Process interaction with Deep Self-Reward Learning System
            self.deep_self_reward_system.process_interaction(user_message, response)

            # Optional: Save reasoning trace
            self.chain_of_thoughts.save_reasoning_trace(f'reasoning_trace_{user_id}.json')

            return response
        except BaseException as e:
            print(f"Error in generate_response: {e}")
            # Log the full traceback for debugging
            import traceback
            traceback.print_exc()
            return "Sorry, I'm having trouble generating a response right now. 🤖❌"

    async def call_groq_ai(self, prompt):
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",  # Updated to a known working model
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a helpful AI assistant. Always respond concisely and directly. " 
                                       "Limit your responses to 2000 characters or less. " 
                                       "Be clear, informative, and avoid unnecessary elaboration."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 32768,  # Limit token count
                    "temperature": 0.7,  # Balanced creativity
                    "top_p": 0.9  # Focused response
                }
                
                # Add timeout to prevent hanging
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions", 
                    headers=headers, 
                    json=payload,
                    timeout=10  # 10-second timeout
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data['choices'][0]['message']['content'].strip()
                        
                        # Additional safeguard to ensure response is within 2000 characters
                        return response[:2000]
                    else:
                        error_text = await resp.text()
                        print(f"Groq API Error: {resp.status} - {error_text}")
                        return "I'm experiencing some technical difficulties right now."
        
        except aiohttp.ClientConnectorError:
            print("Network error: Unable to connect to Groq API")
            return "Sorry, I'm having trouble connecting to my AI brain right now. Please try again later."
        
        except aiohttp.ClientTimeout:
            print("Groq API request timed out")
            return "My response took too long. Could you please repeat your message?"
        
        except Exception as e:
            print(f"Unexpected error in Groq API call: {e}")
            return "Oops! Something went wrong while processing your request."

    async def send_long_message(self, channel, message):
        """
        Send a long message by splitting it into chunks of 2000 characters or less.
        
        Args:
            channel (discord.TextChannel): The channel to send the message to
            message (str): The full message to send
        """
        # Split the message into chunks of 2000 characters or less
        while message:
            # Find the last space within 2000 characters to avoid cutting words
            if len(message) <= 2000:
                chunk = message
                message = ""
            else:
                # Try to split at a space near 2000 characters
                chunk = message[:2000]
                last_space = chunk.rfind(' ')
                
                # If a space is found, use it to split
                if last_space != -1:
                    chunk = chunk[:last_space]
                    message = message[last_space:].lstrip()
                else:
                    # If no space found, just cut at 2000
                    chunk = message[:2000]
                    message = message[2000:]
            
            # Send the chunk
            await channel.send(chunk)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    bot.start()  # Start background tasks

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Check if the bot is mentioned or in a DM
    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # Start typing indicator
        async with message.channel.typing():
            try:
                # Keep typing while processing the message
                while True:
                    # Generate response
                    response = await bot.generate_response(str(message.author.id), message.content)
                    
                    # Send the response
                    await bot.send_long_message(message.channel, response)
                    break
            except Exception as e:
                await message.channel.send(f"An error occurred: {str(e)}")
    
    # Optional: handle other message types or commands here

@client.event
async def on_message_edit(before, after):
    # Handle edited messages if needed
    pass

@client.event
async def on_member_join(member):
    # Welcome new members if needed
    pass

def main():
    """Entry point for the Discord Bot"""
    asyncio.run(client.start(DISCORD_TOKEN))

if __name__ == "__main__":
    import asyncio
    bot = DiscordBot(client)
    main()
