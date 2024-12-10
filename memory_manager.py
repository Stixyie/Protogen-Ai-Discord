import os
import json
import pickle
import uuid
from datetime import datetime
import threading
import numpy as np
import time

class PersistentMemoryManager:
    def __init__(self, storage_path='memory_storage'):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # Comprehensive memory storage structures
        self.conversations = {}
        self.rewards = {}
        self.learning_history = {}
        self.system_state = {}
        
        # Persistent storage files
        self.conversations_file = os.path.join(storage_path, 'conversations.pkl')
        self.rewards_file = os.path.join(storage_path, 'rewards.pkl')
        self.learning_history_file = os.path.join(storage_path, 'learning_history.pkl')
        self.system_state_file = os.path.join(storage_path, 'system_state.pkl')
        
        # Load existing data or initialize
        self.load_memory()
        
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
            print(f"Error saving memory: {e}")
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
        return conversation_id
    
    def record_reward(self, conversation_id, reward_value):
        """Record reward for a specific conversation"""
        self.rewards[conversation_id] = {
            'timestamp': datetime.now().isoformat(),
            'reward_value': reward_value
        }
        self.save_memory()
    
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
    
    def update_system_state(self, key, value):
        """Update and persist system state"""
        self.system_state[key] = value
        self.save_memory()
    
    def periodic_backup(self, interval=300):
        """Periodically backup memory"""
        def backup():
            while True:
                time.sleep(interval)
                self.save_memory()
        
        backup_thread = threading.Thread(target=backup, daemon=True)
        backup_thread.start()

# Instantiate memory manager
memory_manager = PersistentMemoryManager()
