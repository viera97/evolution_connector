

# evolution_connector

Connector between the Evolution API, Fastchat, and Supabase to store and analyze chatbot conversation history.

## Overview

This project integrates:
- **Evolution API**: Receives and sends WhatsApp messages via WebSocket.
- **Fastchat**: Handles chatbot logic and responses using LLMs (OpenAI integration).
- **Supabase**: Stores all conversation history for later analysis or automation.

## Project Structure

- `evolution_ws.py`: Main connector. Manages WebSocket events, bot assignment, and message flow.
- `chat_bot.py`: Fastchat bot initialization and query handling.
- `handle_messages.py`: Formats, saves, and retrieves messages from Supabase.
- `supabase_connector.py`: Supabase client setup and CRUD operations for conversation history.
- `Clinica_prompt.txt`: System prompt for bot initialization.
- `.env`: Environment variables for API keys and configuration.
- `requirements.txt`: Python dependencies.

## Installation

1. Clone the repository.
2. Install dependencies:
   ```fish
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   SUPABASE_URL=...
   SUPABASE_ANON_KEY=...
   EVOLUTION_API_URL=...
   EVOLUTION_API_KEY=...
   EVOLUTION_API_INSTANCE=...
   OPENAI_API_KEY=...
   CRIPTOGRAFY_KEY=...
   ```

## Usage

Start the connector to listen for incoming messages and store conversations:
```fish
python evolution_ws.py
```

## How It Works

1. The Evolution API WebSocket receives a new WhatsApp message.
2. The connector assigns a Fastchat bot instance to the sender (or reuses an existing one).
3. The bot processes the message using the system prompt and LLM.
4. The response is sent back via Evolution API and saved to Supabase.
5. All conversation history is available for analysis in Supabase.

## Main Dependencies

- `evolutionapi`: API client for WhatsApp messaging.
- `fastchat-mcp`: Chatbot logic and LLM integration.
- `supabase`: Database client for storing conversation history.
- `python-dotenv`: Loads environment variables from `.env`.

## Example

```python
from chat_bot import initialize, chating, get_system_prompt
prompt = get_system_prompt("Clinica_prompt.txt")
bot = asyncio.run(initialize(prompt))
response = asyncio.run(chating(bot, "Quiero una cita"))
print(response)
```

## Notes

- Ensure all environment variables are set correctly in `.env`.
- The connector is designed to run as a daemon/service.
- You can customize the system prompt in `initial_prompt.txt`.
- Conversation history is stored in the `chatbot.conversation_history` table in Supabase.

## License

MIT
