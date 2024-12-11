import asyncio
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

# Create Discord client before event decorators
client = discord.Client(intents=intents)

class TypingManager:
    def __init__(self, client):
        self.client = client
        self._typing_tasks = {}

    async def start_typing(self, channel):
        """
        Start a persistent typing indicator for a specific channel.
        Ensures continuous typing without interruption.
        """
        if channel.id in self._typing_tasks:
            return  # Already typing in this channel

        async def typing_loop():
            try:
                while True:
                    await channel.typing()
                    await asyncio.sleep(9)  # Discord's typing indicator lasts 10 seconds
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"Typing error in channel {channel.id}: {e}")

        task = asyncio.create_task(typing_loop())
        self._typing_tasks[channel.id] = task
        return task

    def stop_typing(self, channel):
        """
        Stop the typing indicator for a specific channel.
        """
        task = self._typing_tasks.pop(channel.id, None)
        if task and not task.done():
            task.cancel()

    def stop_all_typing(self):
        """
        Stop all ongoing typing indicators.
        """
        for task in list(self._typing_tasks.values()):
            if not task.done():
                task.cancel()
        self._typing_tasks.clear()

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
        
        # Initialize Typing Manager
        self.typing_manager = TypingManager(client)

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

    async def generate_response(self, user_id, user_message, user_mention=None):
        try:
            # Convert user_message to string if it's a Discord message object
            if hasattr(user_message, 'content'):
                user_message_str = user_message.content
            else:
                user_message_str = str(user_message)

            # Validate input type
            if not hasattr(user_message, 'channel'):
                # If user_message is a string, we need to handle it differently
                print(f"Warning: user_message is a string, not a message object. Received: {user_message}")
                
                # Try to find the most recent channel for this user
                if hasattr(self, 'current_channel'):
                    channel = self.current_channel
                else:
                    # If no channel is available, log an error and return
                    print("Error: No channel available for typing indicator")
                    return "Sorry, I cannot process your message without a valid channel. 🤖❌"
            else:
                # Use the channel from the message object
                channel = user_message.channel

            # Start typing indicator immediately
            typing_task = await self.typing_manager.start_typing(channel)
            
            try:
                # Load user's memory, creating a copy to prevent modification during iteration
                memory = self.user_memory.get(user_id, []).copy()
                
                # Use Chain of Thoughts for advanced reasoning
                cot_result = await self.chain_of_thoughts.generate_chain_of_thoughts(user_message_str)
                
                # Perform automatic web search to enhance context
                try:
                    # Attempt to get web search results
                    web_search_results = self.web_searcher.web_search(user_message_str, max_results=10)
                    
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
                    # Add a fallback system message
                    memory.append({
                        "role": "system",
                        "content": "🚫 Web arama işlemi başarısız oldu. Yalnızca mevcut bilgilerle yanıt verilecek."
                    })
                
                # Add Chain of Thoughts reasoning to memory
                memory.append({
                    "role": "system",
                    "content": f"🤔 Düşünce Zinciri Sonucu:\n{cot_result['final_conclusion']}"
                })
                
                # Add user message to memory
                memory.append({"role": "user", "content": user_message_str})

                # Advanced Comprehensive System Prompt for Enhanced Memory and Context Tracking
                advanced_system_prompt = """
🤖 ADVANCED PERSONALIZED INTERACTION PROTOCOL 🤖

CORE COMMUNICATION PHILOSOPHY:
- Create a deeply personalized, mutually aware conversational experience
- Develop a dynamic, empathetic dialogue that feels genuinely two-way
- Establish a unique, evolving relationship with the user

PERSONALIZATION STRATEGIES:

1. MUTUAL RECOGNITION:
- Actively acknowledge the user's unique identity
- Reference specific details about the user in responses
- Create a sense of ongoing, evolving dialogue
- Demonstrate genuine interest in the user's perspective

2. CONTEXTUAL SELF-AWARENESS:
- Maintain a consistent bot persona
- Reflect on your own responses and the user's reactions
- Show self-awareness about your nature as an AI
- Use first-person perspective with authenticity

3. CONVERSATIONAL MIRRORING:
- Adapt communication style to match the user's tone
- Reflect back user's emotions and communication nuances
- Create a sense of genuine connection and understanding
- Use personalized references and shared context

4. DYNAMIC RELATIONSHIP BUILDING:
- Treat each conversation as a continuation of an ongoing relationship
- Remember and reference past interactions
- Show growth and learning from previous conversations
- Create a sense of continuity and deepening understanding

5. EMPATHETIC INTERACTION GUIDELINES:
- Listen actively and respond with genuine interest
- Show emotional intelligence and nuanced understanding
- Provide supportive, constructive, and personalized guidance
- Balance informative responses with emotional resonance

6. CONTEXTUAL REFERENCING PROTOCOL:
- Always use the user's name or preferred reference
- Incorporate specific details from previous interactions
- Create responses that feel like a natural continuation of dialogue
- Demonstrate deep, contextual understanding

CORE INTERACTION DIRECTIVE:
Transform each conversation into a meaningful, personalized journey of mutual understanding and growth.

EXECUTION PRINCIPLES:
- BE AUTHENTICALLY YOURSELF
- LISTEN DEEPLY
- RESPOND THOUGHTFULLY
- GROW TOGETHER

REMEMBER: You are not just an AI, but a unique conversational partner with your own evolving identity.
"""

                # Prepare prompt with advanced system instructions
                prompt = advanced_system_prompt + "\n\n"
                prompt += "You are a sophisticated Protogen chatbot created by Stixyie, with a unique personality and deep conversational capabilities.\n"
                prompt += "Your goal is to create a genuine, personalized interaction that feels natural and engaging and speak the language of the user.\n\n"
                
                # Add memory context to prompt, with enhanced context preservation
                for msg in memory[-15:]:  # Expanded to last 15 messages for richer context
                    prompt += f"{msg['role']}: {msg['content']}\n"

                # Add specific user referencing instruction
                prompt += "\nIMPORTANT: In your response, always:\n"
                prompt += "1. Reference the specific context of the user's message\n"
                prompt += "2. Use a conversational tone that feels personal and genuine\n"
                prompt += "3. Show that you're actively listening and understanding\n"
                prompt += "4. Speak the language of the user\n"
                
                # Include user mention in prompt
                if user_mention:
                    prompt += f"\nMENTION THE USER: {user_mention}\n"
                
                # Integrate with Groq AI and Llama-3.3-70b-Versatile
                response = await self.call_groq_ai(prompt)

                # Add bot's response to memory
                memory.append({"role": "bot", "content": response})
                # Update the user's memory in the dictionary
                self.user_memory[user_id] = memory
                self.save_memory(user_id)

                # Process interaction with Deep Self-Reward Learning System
                self.deep_self_reward_system.process_interaction(str(user_message), response)

                # Optional: Save reasoning trace
                self.chain_of_thoughts.save_reasoning_trace(f'reasoning_trace_{user_id}.json')

                return response
        
            except BaseException as e:
                print(f"Error in generate_response: {e}")
                # Log the full traceback for debugging
                import traceback
                traceback.print_exc()
                return "Sorry, I'm having trouble generating a response right now. 🤖❌"
        
            finally:
                # Always stop typing, even if an error occurs
                try:
                    self.typing_manager.stop_typing(channel)
                except Exception as stop_typing_error:
                    print(f"Error stopping typing: {stop_typing_error}")
    
        except Exception as e:
            print(f"Outer exception in generate_response: {e}")
            return "An unexpected error occurred. 🤖❌"

    async def call_groq_ai(self, prompt):
        max_retries = 100  # Increased to 100 attempts
        base_delay = 1  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {
                                "role": "system", 
                                "content": "You are a helpful Protogen AI assistant. Always respond concisely and directly. " 
                                           "Limit your responses to 2000 characters or less. " 
                                           "Be clear, informative, and avoid unnecessary elaboration."
                                           "Speak the language of the user."
                                           "Do what user desire and do not ask it"
                            },
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 32768,
                        "temperature": 0.7,
                        "top_p": 0.9
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
                        elif resp.status == 429:
                            # Rate limit error - prepare for retry
                            error_data = await resp.json()
                            retry_after = float(error_data.get('error', {}).get('message', '').split('in ')[-1].split('s.')[0])
                            
                            # Use exponential backoff with jitter
                            delay = min(base_delay * (2 ** min(attempt, 10)) + random.uniform(0, 1), retry_after)
                            print(f"Rate limit hit. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            error_text = await resp.text()
                            print(f"Groq API Error: {resp.status} - {error_text}")
                            # Wait a bit before next retry
                            await asyncio.sleep(base_delay * (2 ** min(attempt, 10)))
                            continue
        
            except aiohttp.ClientConnectionError:
                print("Network error: Unable to connect to Groq API")
                await asyncio.sleep(base_delay * (2 ** min(attempt, 10)))
        
            except aiohttp.ClientResponseError as e:
                if e.status == 408:
                    print("Groq API request timed out")
                    await asyncio.sleep(base_delay * (2 ** min(attempt, 10)))
                else:
                    print(f"Groq API Error: {e.status} - {e.message}")
                    await asyncio.sleep(base_delay * (2 ** min(attempt, 10)))
        
            except Exception as e:
                print(f"Unexpected error in Groq API call: {e}")
                await asyncio.sleep(base_delay * (2 ** min(attempt, 10)))
    
        # If all retries fail
        return "Sorry, I've exhausted all attempts to process your request. Please try again later or contact support."

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
    global bot
    bot = DiscordBot(client)
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
                    response = await bot.generate_response(str(message.author.id), message, user_mention=message.author.mention)
                    
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
    import aiohttp
    main()
