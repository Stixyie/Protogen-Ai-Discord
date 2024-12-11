import os
import json
import logging
from typing import List, Dict
try:
    import tiktoken
except ImportError:
    logging.error("Failed to import tiktoken. Please install tiktoken library.")
    exit(1)
from groq import Groq
from datetime import datetime
import uuid

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('memory_processor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, memory_dir: str = 'memory'):
        """
        Initialize MemoryManager with memory directory
        
        Args:
            memory_dir (str): Path to memory directory
        """
        self.memory_dir = memory_dir
        
        # Validate memory directory
        if not os.path.exists(memory_dir):
            logger.info(f"Creating memory directory: {memory_dir}")
            os.makedirs(memory_dir, exist_ok=True)

    def save_message(self, message: str, user_id: str = None, context: Dict = None):
        """
        Save a message to a memory file
        
        Args:
            message (str): The message to save
            user_id (str, optional): Unique identifier for the user
            context (Dict, optional): Additional context for the message
        """
        try:
            # Generate unique identifiers
            conversation_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Prepare memory entry
            memory_entry = {
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "context": context or {},
                "message": {
                    "user_id": user_id or "unknown",
                    "content": message,
                    "length": len(message)
                }
            }
            
            # Create filename with timestamp and conversation ID
            filename = f"memory_{timestamp.replace(':', '-')}_{conversation_id[:8]}.json"
            filepath = os.path.join(self.memory_dir, filename)
            
            # Write memory entry to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(memory_entry, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved message memory: {filename}")
        except Exception as e:
            logger.error(f"Error saving message memory: {e}")

class MemoryProcessor:
    def __init__(self, memory_dir: str, groq_api_key: str):
        """
        Initialize MemoryProcessor with memory directory and Groq API key
        
        Args:
            memory_dir (str): Path to memory directory
            groq_api_key (str): Groq API key for authentication
        """
        self.memory_dir = memory_dir
        self.client = Groq(api_key=groq_api_key)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.memory_manager = MemoryManager(memory_dir)
        
        # Validate memory directory
        if not os.path.exists(memory_dir):
            logger.error(f"Memory directory not found: {memory_dir}")
            os.makedirs(memory_dir, exist_ok=True)
            logger.info(f"Created memory directory: {memory_dir}")

    def read_memory_files(self) -> List[Dict]:
        """
        Read all memory files from the specified directory
        
        Returns:
            List of memory dictionaries
        """
        memories = []
        try:
            for filename in os.listdir(self.memory_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.memory_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            memory = json.load(f)
                            memories.append(memory)
                            logger.info(f"Loaded memory from {filename}")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in {filename}")
                    except Exception as e:
                        logger.error(f"Error reading {filename}: {e}")
        except Exception as e:
            logger.error(f"Error reading memory directory: {e}")
        
        return memories

    def chunk_memories(self, memories: List[Dict], max_tokens: int = 6000) -> List[str]:
        """
        Split memories into token-limited chunks
        
        Args:
            memories (List[Dict]): List of memory dictionaries
            max_tokens (int): Maximum tokens per chunk
        
        Returns:
            List of memory chunks
        """
        memory_text = json.dumps(memories, ensure_ascii=False, indent=2)
        tokens = self.tokenizer.encode(memory_text)
        
        chunks = []
        current_chunk = []
        current_token_count = 0
        
        for token in tokens:
            current_chunk.append(token)
            current_token_count += 1
            
            if current_token_count >= max_tokens:
                chunks.append(self.tokenizer.decode(current_chunk))
                current_chunk = []
                current_token_count = 0
        
        if current_chunk:
            chunks.append(self.tokenizer.decode(current_chunk))
        
        logger.info(f"Split memories into {len(chunks)} chunks")
        return chunks

    def send_to_groq(self, memory_chunks: List[str]):
        """
        Send memory chunks to Groq API
        
        Args:
            memory_chunks (List[str]): Chunks of memory text
        """
        for i, chunk in enumerate(memory_chunks, 1):
            try:
                logger.info(f"Sending memory chunk {i}/{len(memory_chunks)}")
                response = self.client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a memory processing assistant. The following is a chunk of memory data to be processed and remembered."
                        },
                        {
                            "role": "user", 
                            "content": chunk
                        }
                    ],
                    max_tokens=8192
                )
                logger.info(f"Chunk {i} processed successfully")
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")

    def save_user_message(self, message: str, user_id: str = None, context: Dict = None):
        """
        Convenience method to save user message and process memories
        
        Args:
            message (str): User's message
            user_id (str, optional): User identifier
            context (Dict, optional): Additional context
        """
        # Save the message to memory
        self.memory_manager.save_message(message, user_id, context)
        
        # Process memories (optional: you can choose to process immediately or later)
        self.process_memories()

    def process_memories(self):
        """
        Main method to read memories and send to Groq
        """
        logger.info("Starting memory processing...")
        memories = self.read_memory_files()
        
        if not memories:
            logger.warning("No memories found to process")
            return
        
        memory_chunks = self.chunk_memories(memories)
        self.send_to_groq(memory_chunks)
        
        logger.info("Memory processing completed")

def main():
    # Replace with your actual Groq API key
    GROQ_API_KEY = "your_groq_api_key_here"
    MEMORY_DIR = "g:/protogen bot geliştirme/Protogen-Ai-Discord-main/bot_memory"
    
    processor = MemoryProcessor(MEMORY_DIR, GROQ_API_KEY)
    processor.process_memories()

if __name__ == "__main__":
    main()
