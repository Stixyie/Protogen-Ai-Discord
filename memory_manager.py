import os
import json
import pickle
import uuid
from datetime import datetime
import threading
import numpy as np
import time
import logging
from groq import Client as Groq
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MemoryManager')

def json_numpy_serializer(obj):
    """
    Custom JSON serializer to handle NumPy types
    
    :param obj: Object to serialize
    :return: Serializable representation of the object
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        # Let the base JSON serializer handle other types
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class PersistentMemoryManager:
    def __init__(self, storage_path='memory_storage'):
        self.storage_path = storage_path
        
        # Ensure memory directories exist
        self.ensure_memory_directories()
        
        # Groq API Client with secure key retrieval
        try:
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise ValueError("Groq API Key not found in environment variables")
            self.groq_client = Groq(api_key=groq_api_key)
        except Exception as e:
            logger.error(f"Groq API Client Initialization Error: {e}")
            self.groq_client = None
        
        # Comprehensive memory storage structures
        self.conversations = {}
        self.rewards = {}
        self.learning_history = {}
        self.system_state = {}
        
        # Persistent storage files and directories
        self.memory_dir = os.path.join(os.getcwd(), 'memory')
        self.conversations_file = os.path.join(storage_path, 'conversations.pkl')
        self.rewards_file = os.path.join(storage_path, 'rewards.pkl')
        self.learning_history_file = os.path.join(storage_path, 'learning_history.pkl')
        self.system_state_file = os.path.join(storage_path, 'system_state.pkl')
        
        # Load existing data or initialize
        self.load_memory()
        
        logger.info("Memory Manager initialized successfully")
    
    def ensure_memory_directories(self):
        """
        Ensure all necessary memory directories exist
        """
        directories = [
            'memory',  # Main memory directory
            'memory_storage',  # Persistent storage directory
            'logs'  # Logging directory
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Error creating directory {directory}: {e}")
    
    def create_user_memory_file(self, user_id):
        """
        Create a memory file for a specific user
        
        :param user_id: User's unique identifier
        :return: Path to the created memory file
        """
        try:
            # Ensure memory directory exists
            os.makedirs(self.memory_dir, exist_ok=True)
            
            # Create user memory file path
            user_memory_file = os.path.join(self.memory_dir, f"{user_id}.json")
            
            # Create the file if it doesn't exist
            if not os.path.exists(user_memory_file):
                with open(user_memory_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                logger.info(f"Created memory file for user {user_id}")
            
            return user_memory_file
        except Exception as e:
            logger.error(f"Error creating memory file for user {user_id}: {e}")
            return None
    
    def save_user_memory(self, user_id, memory_data):
        """
        Save memory data for a specific user
        
        :param user_id: User's unique identifier
        :param memory_data: Memory data to save
        """
        try:
            # Create user memory file if it doesn't exist
            user_memory_file = self.create_user_memory_file(user_id)
            
            if user_memory_file:
                with open(user_memory_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, indent=2, default=json_numpy_serializer)
                logger.info(f"Saved memory for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving memory for user {user_id}: {e}")
    
    def load_user_memory(self, user_id):
        """
        Load memory data for a specific user
        
        :param user_id: User's unique identifier
        :return: Loaded memory data
        """
        try:
            user_memory_file = os.path.join(self.memory_dir, f"{user_id}.json")
            
            # Create file if it doesn't exist
            if not os.path.exists(user_memory_file):
                self.create_user_memory_file(user_id)
                return {}
            
            with open(user_memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
                logger.info(f"Loaded memory for user {user_id}")
                return memory_data
        except Exception as e:
            logger.error(f"Error loading memory for user {user_id}: {e}")
            return {}

    def truncate_memory_context(self, memory_context, max_tokens=3000):
        """
        Truncate memory context to fit within token limits
        
        :param memory_context: Dictionary of memory context
        :param max_tokens: Maximum number of tokens to allow
        :return: Truncated memory context
        """
        # Create a deep copy to avoid modifying original data
        context_copy = json.loads(json.dumps(memory_context, default=json_numpy_serializer))
        
        # Convert to JSON and truncate
        full_json = json.dumps(context_copy, indent=2, default=json_numpy_serializer)
        
        # If full JSON is too large, progressively reduce
        while len(full_json.encode('utf-8')) > max_tokens * 4:  # Rough token estimation
            # Remove oldest or least important entries
            if isinstance(context_copy, dict):
                if context_copy:
                    # Remove the first/oldest key
                    oldest_key = list(context_copy.keys())[0]
                    del context_copy[oldest_key]
                else:
                    break
            elif isinstance(context_copy, list):
                if context_copy:
                    context_copy.pop(0)
                else:
                    break
            
            # Regenerate JSON
            full_json = json.dumps(context_copy, indent=2, default=json_numpy_serializer)
        
        return context_copy
    
    async def send_memory_to_groq(self, context_type='conversations'):
        """
        Send memory context to Groq API for processing
        
        :param context_type: Type of memory to send (conversations, rewards, learning_history)
        :return: Groq API response
        """
        if not self.groq_client:
            logger.error("Groq API Client not initialized")
            return None
        
        try:
            # Select appropriate memory context
            memory_context = getattr(self, context_type, {})
            
            if not memory_context:
                logger.warning(f"No memory found in {context_type}")
                return None
            
            # Truncate memory context to avoid rate limits
            truncated_memory = self.truncate_memory_context(memory_context)
            
            # Convert memory to a comprehensive prompt
            memory_prompt = json.dumps(
                truncated_memory, 
                indent=2, 
                default=json_numpy_serializer
            )
            
            logger.info(f"Preparing to send {context_type} to Groq API")
            
            # Send to Groq API
            response = self.groq_client.chat.completions.create(
                model="Llama-3.3-70B-Versatile",  # Exclusively using Llama-3.3-70B-Versatile
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are an advanced memory processing AI. Analyze and understand the following {context_type} memory context:"
                    },
                    {
                        "role": "user", 
                        "content": f"Memory Context ({context_type}):\n{memory_prompt}"
                    }
                ],
                max_tokens=4096
            )
            
            # Log the response
            logger.info(f"Groq API Response for {context_type}: {response.choices[0].message.content}")
            
            return response
        
        except Exception as e:
            logger.error(f"Error sending memory to Groq API: {e}")
            return None
    
    def process_all_memories(self):
        """
        Process all memory types with Groq API
        """
        memory_types = ['system_state', 'conversations', 'rewards', 'learning_history']
        
        for memory_type in memory_types:
            try:
                asyncio.run(self.send_memory_to_groq(memory_type))
            except Exception as e:
                logger.error(f"Error processing {memory_type} memory: {e}")
    
    def log_memory_interaction(self, interaction_type, details):
        """
        Log detailed memory interactions
        
        :param interaction_type: Type of interaction (read, write, update)
        :param details: Detailed information about the interaction
        """
        logger.info(f"Memory Interaction - Type: {interaction_type}, Details: {details}")
    
    def generate_unique_id(self):
        return str(uuid.uuid4())
    
    def save_memory(self):
        """Save all memory components persistently"""
        try:
            # Create deep copies to prevent modification during iteration
            conversations_copy = self.conversations.copy()
            rewards_copy = self.rewards.copy()
            learning_history_copy = self.learning_history.copy()
            system_state_copy = self.system_state.copy()
            
            with open(self.conversations_file, 'wb') as f:
                pickle.dump(conversations_copy, f)
            
            with open(self.rewards_file, 'wb') as f:
                pickle.dump(rewards_copy, f)
            
            with open(self.learning_history_file, 'wb') as f:
                pickle.dump(learning_history_copy, f)
            
            with open(self.system_state_file, 'wb') as f:
                pickle.dump(system_state_copy, f)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            # Optional: Add logging or error handling mechanism
    
    def load_memory(self):
        """Load existing memory or initialize if not exists"""
        try:
            with open(self.conversations_file, 'rb') as f:
                self.conversations = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.conversations = {}
        
        try:
            with open(self.rewards_file, 'rb') as f:
                self.rewards = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.rewards = {}
        
        try:
            with open(self.learning_history_file, 'rb') as f:
                self.learning_history = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.learning_history = {}
        
        try:
            with open(self.system_state_file, 'rb') as f:
                self.system_state = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.system_state = {}
    
    def record_conversation(self, user_message, bot_response):
        """Record comprehensive conversation details"""
        conversation_id = self.generate_unique_id()
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': bot_response,
            'metadata': {}
        }
        
        self.conversations[conversation_id] = conversation_entry
        self.save_memory()
        self.log_memory_interaction('write', f"Conversation ID: {conversation_id}")
        return conversation_id
    
    def record_reward(self, conversation_id, reward_value):
        """Record reward for a specific conversation"""
        self.rewards[conversation_id] = {
            'timestamp': datetime.now().isoformat(),
            'reward_value': reward_value
        }
        self.save_memory()
        self.log_memory_interaction('write', f"Conversation ID: {conversation_id}, Reward Value: {reward_value}")
    
    def record_learning_event(self, event_type, details):
        """Record learning and evolution events"""
        event_id = self.generate_unique_id()
        learning_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        self.learning_history[event_id] = learning_entry
        self.save_memory()
        self.log_memory_interaction('write', f"Event ID: {event_id}, Event Type: {event_type}")
    
    def update_system_state(self, key, value):
        """Update and persist system state"""
        self.system_state[key] = value
        self.save_memory()
        self.log_memory_interaction('update', f"Key: {key}, Value: {value}")
    
    def periodic_backup(self, interval=300):
        """Periodically backup memory"""
        def backup():
            while True:
                time.sleep(interval)
                self.save_memory()
        
        backup_thread = threading.Thread(target=backup, daemon=True)
        backup_thread.start()

    def get_user_ids(self):
        """
        Retrieve all user IDs from memory files
        
        :return: List of user IDs
        """
        try:
            # Ensure memory directory exists
            os.makedirs(self.memory_dir, exist_ok=True)
            
            # Get all JSON files in the memory directory
            user_ids = []
            for filename in os.listdir(self.memory_dir):
                if filename.endswith('.json'):
                    # Remove .json extension to get user ID
                    user_id = filename[:-5]
                    user_ids.append(user_id)
            
            logger.info(f"Retrieved {len(user_ids)} user IDs")
            return user_ids
        except Exception as e:
            logger.error(f"Error retrieving user IDs: {e}")
            return []

# Instantiate memory manager
memory_manager = PersistentMemoryManager()

# Optional: Periodically process memories
def periodic_memory_processing():
    """
    Periodically process and send memories to Groq API
    """
    while True:
        try:
            logger.info("Starting periodic memory processing...")
            memory_manager.process_all_memories()
            time.sleep(3600)  # Process memories every hour
        except Exception as e:
            logger.error(f"Error in periodic memory processing: {e}")
            time.sleep(3600)  # Wait an hour before retrying

# Start periodic memory processing in a separate thread
memory_processing_thread = threading.Thread(target=periodic_memory_processing, daemon=True)
memory_processing_thread.start()
