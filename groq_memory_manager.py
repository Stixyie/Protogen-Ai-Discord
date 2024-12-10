import os
import json
import glob
import logging
from typing import List, Dict, Optional
import groq
from dotenv import load_dotenv
import time

class GroqMemoryManager:
    def __init__(self, memory_dir: str = 'memory_files'):
        """
        Initialize Groq Memory Manager for comprehensive memory management
        
        :param memory_dir: Directory to store memory files
        """
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Memory management settings
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
        # User memory tracking
        self.user_memories = {}
        
        # Chunk size for transmission
        self.max_chunk_size = 4096
    
    def save_memory_file(self, content: str, user_id: str, file_prefix: str = 'memory') -> str:
        """
        Save memory content for a specific user
        
        :param content: Memory content to save
        :param user_id: Unique identifier for the user
        :param file_prefix: Prefix for memory file name
        :return: Path to saved memory file
        """
        # Generate unique filename
        timestamp = int(time.time())
        filename = os.path.join(
            self.memory_dir, 
            f"{file_prefix}_{user_id}_{timestamp}.txt"
        )
        
        # Save memory file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Memory file saved: {filename}")
        return filename
    
    def load_all_memory_files(self, user_id: str) -> List[str]:
        """
        Load all memory files for a specific user
        
        :param user_id: Unique identifier for the user
        :return: List of memory file contents
        """
        # Find all memory files for the user
        memory_files = glob.glob(
            os.path.join(self.memory_dir, f"*{user_id}*.txt")
        )
        
        # Sort files by timestamp (newest first)
        memory_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # Read and return contents
        memory_contents = []
        for file_path in memory_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                memory_contents.append(f.read())
        
        return memory_contents
    
    def segment_memory(self, memory_content: str) -> List[str]:
        """
        Segment memory content into chunks
        
        :param memory_content: Full memory content
        :return: List of memory chunks
        """
        return [
            memory_content[i:i+self.max_chunk_size] 
            for i in range(0, len(memory_content), self.max_chunk_size)
        ]
    
    def transmit_memory_to_groq(self, user_id: str, user_message: str, max_memory_chunks: int = 5) -> Optional[str]:
        """
        Transmit user memories and current message to Groq with improved memory management
        
        :param user_id: Unique identifier for the user
        :param user_message: Current user message
        :param max_memory_chunks: Maximum number of memory chunks to send
        :return: Groq API response
        """
        try:
            # Load all memory files for the user
            memory_contents = self.load_all_memory_files(user_id)
            
            if not memory_contents:
                logging.info(f"No memory files found for user {user_id}. Starting fresh conversation.")
                memory_contents = ["Initial conversation start"]
            
            # Combine and segment memories, limit to max chunks
            full_memory = "\n\n".join(memory_contents[:max_memory_chunks])
            memory_chunks = self.segment_memory(full_memory)
            
            # Prepare comprehensive prompt with multiple memory segments
            comprehensive_prompt = f"""
            User Memories (Segmented and Limited to {max_memory_chunks} most recent):
            {memory_chunks[0] if memory_chunks else 'No previous memories'}
            
            Current User Message:
            {user_message}
            
            Please provide a contextually aware and coherent response considering the user's memory context.
            If no significant context is found, treat this as a new conversation.
            """
            
            # Send to Groq API with enhanced error handling
            try:
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant with access to user's memory context. Adapt your responses based on available memory."},
                        {"role": "user", "content": comprehensive_prompt}
                    ],
                    max_tokens=4096,  # Limit response size
                    temperature=0.7,  # Balanced creativity
                    top_p=0.9  # Diverse token selection
                )
                
                # Save the current interaction as a new memory
                new_memory_content = f"User: {user_message}\nAssistant: {response.choices[0].message.content}"
                self.save_memory_file(new_memory_content, user_id, file_prefix='interaction')
                
                return response.choices[0].message.content
            
            except groq.APIError as api_err:
                logging.error(f"Groq API Error: {api_err}")
                return f"Sorry, there was an API error: {api_err}"
            
        except Exception as e:
            logging.error(f"Comprehensive error in memory transmission: {e}")
            return None
        
    def clean_old_memories(self, user_id: str, max_memories: int = 10):
        """
        Clean up old memory files, keeping only the most recent ones
        
        :param user_id: Unique identifier for the user
        :param max_memories: Maximum number of memory files to keep
        """
        memory_files = glob.glob(
            os.path.join(self.memory_dir, f"*{user_id}*.txt")
        )
        
        # Sort files by creation time
        memory_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # Delete old memory files
        for file_path in memory_files[max_memories:]:
            try:
                os.remove(file_path)
                logging.info(f"Deleted old memory file: {file_path}")
            except Exception as e:
                logging.error(f"Error deleting memory file {file_path}: {e}")

# Example usage
if __name__ == "__main__":
    memory_manager = GroqMemoryManager()
    
    # Example: Save a memory file
    memory_manager.save_memory_file(
        "This is a sample memory for user123", 
        "user123"
    )
    
    # Example: Transmit memory to Groq
    response = memory_manager.transmit_memory_to_groq(
        "user123", 
        "Tell me about my previous memories"
    )
    print(response)
