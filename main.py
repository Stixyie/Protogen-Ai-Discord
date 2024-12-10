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
        
        # Initialize Deep Self-Reward Learning System
        self.deep_self_reward_system = DeepSelfRewardSystem()
        self.deep_self_reward_system.start_background_tasks()

    def load_memory(self):
        for filename in os.listdir(MEMORY_DIR):
            if filename.endswith(".json"):
                user_id = filename[:-5]
                with open(os.path.join(MEMORY_DIR, filename), "r", encoding="utf-8") as f:
                    self.user_memory[user_id] = json.load(f)

    def save_memory(self, user_id):
        with open(os.path.join(MEMORY_DIR, f"{user_id}.json"), "w", encoding="utf-8") as f:
            json.dump(self.user_memory[user_id], f, ensure_ascii=False, indent=4)

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
        """Perform web search and return comprehensive results"""
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
                return f"🔍 No results found for '{query}'. Try a different search term."
        except Exception as e:
            return f"❌ Web search error: {str(e)}"

    async def generate_response(self, user_id, user_message):
        try:
            # Load user's memory, creating a copy to prevent modification during iteration
            memory = self.user_memory.get(user_id, []).copy()
            
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
            
            # Add user message to memory
            memory.append({"role": "user", "content": user_message})

            # Prepare prompt with maker's name and web context
            prompt = "You are a sophisticated Protogen chatbot created by Stixyie with unlimited memory and web search capabilities.\n"
            prompt += "You can seamlessly integrate web search results into your responses to provide up-to-date and relevant information.\n"
            
            # Add memory context to prompt
            for msg in memory[-10:]:  # Limit to last 10 messages to prevent context overflow
                prompt += f"{msg['role']}: {msg['content']}\n"

            # Integrate with Groq API and Llama-3.3-70b-Versatile
            response = await self.call_groq_ai(prompt)

            # Add bot's response to memory
            memory.append({"role": "bot", "content": response})
            # Update the user's memory in the dictionary
            self.user_memory[user_id] = memory
            self.save_memory(user_id)

            # Process interaction with Deep Self-Reward Learning System
            self.deep_self_reward_system.process_interaction(user_message, response)

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
                    "max_tokens": 300,  # Limit token count
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

    # Check if bot is mentioned or in a direct message
    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # Start typing indicator
        async with message.channel.typing():
            try:
                # Generate bot's response using the global bot instance
                response = await bot.generate_response(str(message.author.id), message.content)
                
                # Send the response
                await message.reply(response)
            
            except BaseException as e:
                # Error handling
                print(f"Error in on_message: {e}")
                await message.reply("Oops! Something went wrong while processing your message. 🤖❌")

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
    bot = DiscordBot(client)
    main()
