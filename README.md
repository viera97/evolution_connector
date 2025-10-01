# Evolution Connector

Connector between the Evolution API, Fastchat, and Supabase to store and analyze chatbot conversation history with async architecture for high-performance WhatsApp bot management.

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to run from the correct directory:
   ```bash
   # From project root
   python src/main.py
   ```

2. **Environment Variables**: Verify all required variables are set in `.env`:
   ```bash
   # Check if .env file exists and has all required variables
   cat .env
   ```

3. **Graceful Shutdown**: Use Ctrl+C to properly close all connections:
   ```
   🛑 Shutdown signal received. Cleaning up...
   📋 Closing bot manager...
   🤖 Closing X bot instances...
   ✅ Cleanup completed successfully!
   ```

4. **Bot Pool Issues**: Monitor bot status in logs:
   ```
   🤖 Created new bot instance: A1
   📞 Assigned bot A1 to user +1234567890
   ♻️ Converted bot +1234567890 to pool bot A4 (ready for new customers)
   ```

### Performance Tips

- The application uses async operations for all database calls
- Bot pool maintains 3+ instances for immediate response
- Inactive bots are automatically cleaned up after 20 minutes
- Background monitoring runs every 30 seconds

## Main DependenciessApp bot management.

## Overview

This project integrates:
- **Evolution API**: Receives and sends WhatsApp messages via WebSocket.
- **Fastchat**: Handles chatbot logic and responses using LLMs (OpenAI integration).
- **Supabase**: Stores all conversation history for later analysis or automation.

### Key Features

- 🔄 **Async Architecture**: Background event loop for non-blocking database operations
- 🤖 **Bot Pool Management**: Intelligent bot assignment and lifecycle management
- 📊 **Thread-Safe Operations**: Concurrent message processing without blocking WebSocket callbacks
- 🔧 **Graceful Shutdown**: Signal handling for clean application termination
- 📱 **Real-time Processing**: Instant message processing and response generation
- 💾 **Persistent Storage**: Comprehensive conversation history in Supabase
- 🔍 **Customer Management**: Automatic customer creation and profile fetching

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

### Prerequisites

- Python 3.11+ (tested with Python 3.13)
- Virtual environment (recommended)
- Supabase account and project
- Evolution API instance
- OpenAI API key

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/viera97/evolution_connector.git
   cd evolution_connector
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following variables:
   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   
   # Evolution API Configuration
   EVOLUTION_API_URL=https://your-evolution-api.com
   EVOLUTION_API_KEY=your_api_key
   EVOLUTION_API_INSTANCE=your_instance_name
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_key
   
   # Security
   CRIPTOGRAFY_KEY=your_encryption_key
   ```

## Usage

### Running Locally

Start the connector to listen for incoming messages and store conversations:
```bash
# From project root
python src/main.py
```

The application will display:
```
🚀 Evolution Connector starting...
💡 Press Ctrl+C to stop the application gracefully
Connected to WebSocket. Waiting for events...
```

### Running with Docker
Build and run using Docker Compose:
```bash
docker-compose up --build
```

Or build and run manually:
```bash
docker build -t evolution-connector .
docker run --env-file .env evolution-connector
```

### Testing

Run the import tests to verify all modules load correctly:
```bash
python tests/test_imports.py
```

## Architecture

### Async Operations Flow

1. **WebSocket Connection**: Evolution API WebSocket receives WhatsApp messages
2. **Background Event Loop**: Dedicated thread handles async database operations
3. **Bot Pool Management**: Maintains 3+ available bot instances for immediate assignment
4. **Thread-Safe Processing**: Uses `asyncio.run_coroutine_threadsafe()` for safe async calls
5. **Customer Management**: Automatic customer creation and conversation history storage
6. **Graceful Shutdown**: Signal handlers ensure clean resource cleanup

### Bot Lifecycle

- **Pool Bots**: Available bots with keys `A1`, `A2`, `A3`...
- **Assigned Bots**: Bots assigned to specific phone numbers
- **Inactive Monitoring**: Automatic cleanup after 20 minutes of inactivity
- **Resource Management**: Smart bot closing/recycling based on total count

### Message Processing Flow

1. The Evolution API WebSocket receives a new WhatsApp message.
2. The connector assigns a Fastchat bot instance to the sender (or reuses an existing one).
3. The bot processes the message using the system prompt and LLM in the background event loop.
4. The response is sent back via Evolution API and conversation is saved to Supabase asynchronously.
5. All conversation history is available for analysis in Supabase.

## API Reference

### Available Functions

#### Async Functions
- `chat_bot.initialize(prompt)`: Initialize a new bot instance
- `chat_bot.chating(bot, query)`: Send message to bot and get response
- `handle_messages.save_message(data, is_bot, customer_id)`: Save message to database
- `handle_messages.get_chatbot_response(bot, data)`: Get bot response for message
- `supabase_connector.get_customers(phone, customer_id)`: Retrieve customer data
- `supabase_connector.add_customers(phone, username)`: Create new customer
- `supabase_connector.add_conversation_history(customer_id, message)`: Save conversation

#### Sync Functions
- `chat_bot.get_system_prompt(file_path)`: Load system prompt from file
- `handle_messages.format_message(data, is_bot)`: Format message for storage
- `supabase_connector.get_all_conversation_history()`: Get all conversations


## Main Dependencies

- `evolutionapi`: API client for WhatsApp messaging
- `fastchat-mcp`: Chatbot logic and LLM integration  
- `supabase`: Database client for storing conversation history
- `python-dotenv`: Environment variable management
- `asyncio`: Async operations and event loop management
- `threading`: Background thread management for async operations

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and test them
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature/new-feature`
6. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python tests/test_imports.py

# Check code formatting
python -m black src/
python -m isort src/
```

## Changelog

### v1.0.0 (Current)
- ✅ Async architecture implementation
- ✅ Background event loop for database operations
- ✅ Thread-safe message processing
- ✅ Graceful shutdown with signal handling
- ✅ Comprehensive bot lifecycle management
- ✅ Automatic customer management
- ✅ Pool-based bot assignment system

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
