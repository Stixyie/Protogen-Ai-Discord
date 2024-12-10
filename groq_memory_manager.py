import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from groq import Groq
from dotenv import load_dotenv

class UserMemoryManager:
    def __init__(self, memory_dir: str = 'memory', storage_dir: str = 'memory_storage'):
        load_dotenv()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename=os.path.join(storage_dir, 'memory_manager.log')
        )
        
        # Initialize Groq client
        try:
            self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        except Exception as e:
            logging.error(f"Failed to initialize Groq client: {e}")
            self.groq_client = None
        
        # Memory directories
        self.memory_dir = memory_dir
        self.storage_dir = storage_dir
        
        # Create directories if they don't exist
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # User memory tracking
        self.user_memories: Dict[str, List[Dict[str, Any]]] = {}
        
        # Memory file watcher
        self.observer = Observer()
    
    def process_memory_file(self, file_path: str):
        """Process a memory file for a specific user with enhanced error handling"""
        try:
            # Extract user ID from filename
            user_id = os.path.splitext(os.path.basename(file_path))[0]
            
            # Read file contents
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip processing if content is empty
            if not content.strip():
                logging.warning(f"Empty memory file: {file_path}")
                return
            
            # Validate Groq client
            if not self.groq_client:
                logging.error("Groq client not initialized. Cannot process memory.")
                return
            
            # Process memory with Groq
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": "You are a memory processing assistant. Analyze and summarize the memory content concisely."},
                        {"role": "user", "content": content}
                    ],
                    max_tokens=1024,  # Limit response size
                    temperature=0.5   # Balanced creativity
                )
                processed_content = response.choices[0].message.content
            except Exception as api_error:
                logging.error(f"Groq API error processing {file_path}: {api_error}")
                processed_content = "Memory processing failed"
            
            # Store processed memory
            processed_memory = {
                'timestamp': time.time(),
                'original_content': content,
                'processed_content': processed_content
            }
            
            # Save to user-specific storage
            user_storage_path = os.path.join(self.storage_dir, f"{user_id}_memories.json")
            
            # Load existing memories or create new list
            try:
                with open(user_storage_path, 'r', encoding='utf-8') as f:
                    user_memories = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                user_memories = []
            
            user_memories.append(processed_memory)
            
            # Save updated memories
            with open(user_storage_path, 'w', encoding='utf-8') as f:
                json.dump(user_memories, f, indent=2)
            
            logging.info(f"Processed memory for user {user_id}")
            
        except Exception as e:
            logging.error(f"Comprehensive error processing memory file {file_path}: {e}")
    
    def start_memory_watcher(self):
        """Start watching the memory directory for new files"""
        class MemoryHandler(FileSystemEventHandler):
            def __init__(self, memory_manager):
                self.memory_manager = memory_manager
            
            def on_created(self, event):
                if not event.is_directory:
                    self.memory_manager.process_memory_file(event.src_path)
        
        event_handler = MemoryHandler(self)
        self.observer.schedule(event_handler, self.memory_dir, recursive=False)
        self.observer.start()
    
    def stop_memory_watcher(self):
        """Stop the memory file watcher"""
        self.observer.stop()
        self.observer.join()
    
    def retrieve_user_memories(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent memories for a specific user"""
        user_storage_path = os.path.join(self.storage_dir, f"{user_id}_memories.json")
        
        if not os.path.exists(user_storage_path):
            logging.info(f"No memories found for user {user_id}")
            return []
        
        try:
            with open(user_storage_path, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            
            # Return most recent memories
            return memories[-limit:]
        except Exception as e:
            logging.error(f"Error retrieving memories for user {user_id}: {e}")
            return []

# Example usage
async def main():
    memory_manager = UserMemoryManager()
    memory_manager.start_memory_watcher()
    
    try:
        # Keep the script running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        memory_manager.stop_memory_watcher()

if __name__ == "__main__":
    asyncio.run(main())
