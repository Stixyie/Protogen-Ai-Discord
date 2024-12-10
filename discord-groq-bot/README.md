# Stixyie Discord AI Bot

## 🦊 About Stixyie
A sophisticated AI Discord bot powered by Groq and Llama 3, with a dynamic furry fox personality!

## 🛡️ Security Warning
**IMPORTANT**: Never share your `.env` file or commit API keys to version control!

## ✨ Features
- AI-powered conversational responses
- Dynamic personality status
- User memory management
- Secure web search with DNS fallback
- Personalized interactions

## 🚀 Setup Instructions

1. Clone the repository
2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with:
   ```
   DISCORD_TOKEN=your_discord_token_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

## 🤖 Commands
- `!search <query>`: Perform a web search
- Mention the bot to get an AI-powered response

## 📋 Memory Management
- User conversations are stored locally in `user_memories/`
- Memories are limited to the last 100 messages per user

## 🔒 Security Practices
- Environment variable-based API key management
- DNS fallback mechanism for web searches
- Limited memory storage
- Error handling and logging

## 👥 Contributing
Feel free to open issues or submit pull requests!
