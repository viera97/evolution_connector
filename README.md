# evolution_connector

Connector between the Evolution API, Fastchat, and Supabase to store and analyze chatbot conversation history.

## Overview

This project integrates:
- **Evolution API**: Receives and sends WhatsApp messages via WebSocket.
- **Fastchat**: Handles chatbot logic and responses using LLMs (OpenAI integration).
- **Supabase**: Stores all conversation history for later analysis or automation.

## Project Structure

- `src/` - Main source code:
  - `main.py`: Application entry point and orchestration.
  - `evolution_ws.py`: Evolution API WebSocket connector and messaging.
  - `bot_manager.py`: Bot lifecycle management, assignment, and monitoring.
  - `chat_bot.py`: Fastchat bot initialization and query handling.
  - `handle_messages.py`: Message formatting and Supabase operations.
  - `supabase_connector.py`: Database CRUD operations for conversation history.
- `prompts/` - System prompts and templates:
  - `initial_prompt.txt`: System prompt for bot initialization.
  - `fastchat.config.json`: Fastchat MCP configuration.
- `tests/` - Unit and integration tests.
- `.env`: Environment variables for API keys and configuration.
- `requirements.txt`: Python dependencies.
- `docker-compose.yml`: Docker orchestration configuration.
- `Dockerfile`: Container build configuration.

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

### Running Locally
Start the connector to listen for incoming messages and store conversations:
```fish
python src/main.py
```

### Running with Docker
Build and run using Docker Compose:
```fish
docker-compose up --build
```

Or build and run manually:
```fish
docker build -t evolution-connector .
docker run --env-file .env evolution-connector
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
