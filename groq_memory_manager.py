import os
import json
import time
import asyncio
import logging
import uuid
from typing import Dict, Any, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from groq import Groq
from dotenv import load_dotenv

class MemoryChunk:
    def __init__(self, content: str, timestamp: float = None, category: str = 'default'):
        self.id = str(uuid.uuid4())  # Unique identifier for each chunk
        self.content = content
        self.timestamp = timestamp or time.time()
        self.category = category
        self.size = len(content)
        self.metadata = {}  # Flexible metadata storage

class UserMemoryManager:
    def __init__(self, memory_dir: str = 'memory', storage_dir: str = 'memory_storage', max_total_memory_mb: float = 50.0):
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
        self.user_memories: Dict[str, List[MemoryChunk]] = {}
        
        # Enhanced memory tracking
        self.max_total_memory_mb = max_total_memory_mb
        self.memory_index: Dict[str, Dict[str, List[str]]] = {}
        
        # Load existing memory state
        self.load_memory_state()
        
        # Memory file watcher
        self.observer = Observer()
    
    def process_memory_file(self, file_path: str):
        """Process a memory file for a specific user with enhanced error handling"""
        try:
            # Extract user ID from filename
            user_id = os.path.splitext(os.path.basename(file_path))[0]
            
            # Read file contents
            with open(file_path, 'r', encoding='utf-8') as f:
                memory_content = f.read()
            
            # Split content into chunks
            memory_chunks = self.split_memory_content(memory_content)
            
            # Store memory chunks for the user
            self.user_memories[user_id] = memory_chunks
            
            logging.info(f"Processed memory file for user {user_id}")
            return memory_chunks
        
        except Exception as e:
            logging.error(f"Error processing memory file {file_path}: {e}")
            return []
    
    def split_memory_content(self, content: str, max_chunk_size: int = 4000) -> List[MemoryChunk]:
        """Split memory content into manageable chunks for Groq AI"""
        chunks = []
        words = content.split()
        current_chunk = []
        current_chunk_size = 0
        
        for word in words:
            if current_chunk_size + len(word) > max_chunk_size:
                chunks.append(MemoryChunk(' '.join(current_chunk)))
                current_chunk = []
                current_chunk_size = 0
            
            current_chunk.append(word)
            current_chunk_size += len(word) + 1  # +1 for space
        
        if current_chunk:
            chunks.append(MemoryChunk(' '.join(current_chunk)))
        
        return chunks
    
    async def send_memory_to_groq(self, user_id: str, message: str):
        """Send user-specific memory chunks to Groq AI"""
        if user_id not in self.user_memories:
            # Try to load memory file if not already loaded
            memory_file_path = os.path.join(self.memory_dir, f"{user_id}.txt")
            if os.path.exists(memory_file_path):
                self.process_memory_file(memory_file_path)
            else:
                logging.warning(f"No memory file found for user {user_id}")
                return None
        
        memory_chunks = self.user_memories.get(user_id, [])
        
        if not memory_chunks:
            logging.warning(f"No memory chunks available for user {user_id}")
            return None
        
        try:
            # Combine memory chunks with the current message
            full_context = " ".join([chunk.content for chunk in memory_chunks] + [message])
            
            # Send to Groq AI
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an AI assistant with persistent memory. Use the provided context to enhance your responses."},
                    {"role": "user", "content": full_context}
                ]
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logging.error(f"Error sending memory to Groq for user {user_id}: {e}")
            return None
    
    def add_memory_chunk(self, user_id: str, content: str, category: str = 'default', metadata: dict = None):
        """
        Add a memory chunk with advanced tracking and size management
        """
        chunk = MemoryChunk(
            content=content, 
            timestamp=time.time(), 
            category=category
        )
        
        if metadata:
            chunk.metadata = metadata
        
        # Size management
        current_memory_size = sum(chunk.size for chunk in self.user_memories.get(user_id, []))
        max_bytes = self.max_total_memory_mb * 1024 * 1024
        
        if current_memory_size + chunk.size > max_bytes:
            # Implement intelligent chunk removal strategy
            self.prune_memory_chunks(user_id, chunk.size)
        
        if user_id not in self.user_memories:
            self.user_memories[user_id] = []
        
        self.user_memories[user_id].append(chunk)
        
        # Update memory index
        if user_id not in self.memory_index:
            self.memory_index[user_id] = {}
        
        if category not in self.memory_index[user_id]:
            self.memory_index[user_id][category] = []
        
        self.memory_index[user_id][category].append(chunk.id)
        
        # Log the addition
        logging.info(f"Added memory chunk for user {user_id} in category {category}")
        
        return chunk.id

    def prune_memory_chunks(self, user_id: str, required_space: int):
        """
        Intelligently remove memory chunks to make space
        """
        if user_id not in self.user_memories:
            return
        
        # Sort chunks by timestamp (oldest first)
        sorted_chunks = sorted(
            self.user_memories[user_id], 
            key=lambda x: x.timestamp
        )
        
        pruned_chunks = []
        freed_space = 0
        
        for chunk in sorted_chunks:
            if freed_space >= required_space:
                break
            
            pruned_chunks.append(chunk)
            freed_space += chunk.size
        
        # Remove pruned chunks
        for chunk in pruned_chunks:
            self.user_memories[user_id].remove(chunk)
            
            # Clean up index
            for category, chunk_ids in self.memory_index[user_id].items():
                if chunk.id in chunk_ids:
                    chunk_ids.remove(chunk.id)
        
        logging.info(f"Pruned {len(pruned_chunks)} memory chunks for user {user_id}")

    def retrieve_memory_chunks(
        self, 
        user_id: str, 
        category: str = None, 
        max_chunks: int = 10, 
        min_timestamp: float = None
    ):
        """
        Retrieve memory chunks with advanced filtering
        """
        if user_id not in self.user_memories:
            return []
        
        chunks = self.user_memories[user_id]
        
        # Apply filters
        if category:
            chunks = [
                chunk for chunk in chunks 
                if chunk.category == category
            ]
        
        if min_timestamp:
            chunks = [
                chunk for chunk in chunks 
                if chunk.timestamp >= min_timestamp
            ]
        
        # Sort by timestamp, most recent first
        chunks.sort(key=lambda x: x.timestamp, reverse=True)
        
        return chunks[:max_chunks]

    def save_memory_state(self):
        """Save entire memory state to persistent storage"""
        for user_id, chunks in self.user_memories.items():
            user_memory_file = os.path.join(
                self.storage_dir, 
                f"{user_id}_memory_state.json"
            )
            
            serialized_chunks = [
                {
                    'id': chunk.id,
                    'content': chunk.content,
                    'timestamp': chunk.timestamp,
                    'category': chunk.category,
                    'metadata': chunk.metadata
                } for chunk in chunks
            ]
            
            with open(user_memory_file, 'w', encoding='utf-8') as f:
                json.dump(serialized_chunks, f, ensure_ascii=False, indent=2)
        
        logging.info("Memory state saved successfully")

    def load_memory_state(self):
        """Load memory state from persistent storage"""
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('_memory_state.json'):
                user_id = filename.split('_')[0]
                file_path = os.path.join(self.storage_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        serialized_chunks = json.load(f)
                    
                    self.user_memories[user_id] = [
                        MemoryChunk(
                            content=chunk['content'],
                            timestamp=chunk['timestamp'],
                            category=chunk['category']
                        ) for chunk in serialized_chunks
                    ]
                    
                    logging.info(f"Loaded memory state for user {user_id}")
                except Exception as e:
                    logging.error(f"Error loading memory state for user {user_id}: {e}")

    def start_memory_watcher(self):
        """Start watching the memory directory for new or modified files"""
        class MemoryFileHandler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    self.process_memory_file(event.src_path)
            
            def on_modified(self, event):
                if not event.is_directory:
                    self.process_memory_file(event.src_path)
        
        event_handler = MemoryFileHandler()
        self.observer.schedule(event_handler, self.memory_dir, recursive=False)
        self.observer.start()
    
    def stop_memory_watcher(self):
        """Stop the memory file watcher"""
        self.observer.stop()
        self.observer.join()

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
