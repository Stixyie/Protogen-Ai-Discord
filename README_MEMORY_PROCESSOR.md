# Memory Processor for Protogen AI

## Overview
This system processes and saves memory files, sending them to the Groq API for context retention and advanced processing.

## Features
- Automatically save user messages as memory files
- Reads JSON memory files from `memory` directory
- Chunks memory content into 6000-token segments
- Sends memory chunks to Groq API
- Provides detailed logging of processing steps

## Setup
1. Ensure all dependencies are installed:
   ```
   pip install -r requirements.txt
   ```

2. Set your Groq API key in `memory_processor.py`

3. Place memory JSON files in the `bot_memory` directory

## Memory Saving
Use `save_user_message()` to save messages:

```python
memory_processor = MemoryProcessor(memory_dir, groq_api_key)
memory_processor.save_user_message(
    message="Hello, how are you?", 
    user_id="user123", 
    context={"language": "Turkish", "mood": "friendly"}
)
```

## Memory File Structure
Memory files are saved with a unique filename and JSON structure:
```json
{
    "conversation_id": "unique_uuid",
    "timestamp": "ISO8601_timestamp",
    "context": {...},
    "message": {
        "user_id": "optional_user_id",
        "content": "message_text",
        "length": message_length
    }
}
```

## Logging
Detailed logs are saved in `memory_processor.log`

## Usage
Run the script directly:
```
python memory_processor.py
```

## Dependencies
- groq
- tiktoken
- python-dotenv
