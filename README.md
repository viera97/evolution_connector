# evolution_connector

Connector between the Evolution API, Fastchat, and Supabase to store and analyze chatbot conversation history.

## Overview

This project integrates:
- **Evolution API**: Receives and sends WhatsApp messages via WebSocket.
- **Fastchat**: Handles chatbot logic and responses using LLMs (OpenAI integration).
- **Supabase**: Stores all conversation history for later analysis or automation.

## Project Structure

- `src/` - Main source code:
  - `chat_bot.py`: Fastchat bot initialization and query handling.
  - `evolution_ws.py`: Main connector. Manages WebSocket events, bot assignment, and message flow.
  - `handle_messages.py`: Formats, saves, and retrieves messages from Supabase.
  - `supabase_connector.py`: Supabase client setup and CRUD operations for conversation history.
- `prompts/` - System prompts and templates:
  - `initial_prompt.txt`: System prompt for bot initialization.
  - `fastchat.config.json`: Fastchat MCP configuration.
- `tests/` - Unit and integration tests.
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
python src/evolution_ws.py
```

## How It Works

1. The Evolution API WebSocket receives a new WhatsApp message.
2. The connector assigns a Fastchat bot instance to the sender (or reuses an existing one).
3. The bot processes the message using the system prompt and LLM.
4. The response is sent back via Evolution API and saved to Supabase.
5. All conversation history is available for analysis in Supabase.

## Example

```python
from src.chat_bot import initialize, chating, get_system_prompt
import asyncio

prompt = get_system_prompt("prompts/initial_prompt.txt")
bot = asyncio.run(initialize(prompt))
response = asyncio.run(chating(bot, "Quiero una cita"))
print(response)
```

## Main Dependencies

- `evolutionapi`: API client for WhatsApp messaging.
- `fastchat-mcp`: Chatbot logic and LLM integration.
- `supabase`: Database client for storing conversation history.
- `python-dotenv`: Loads environment variables from `.env`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
