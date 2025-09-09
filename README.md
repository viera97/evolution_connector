
# evolution_connector

Connector between the Evolution API and Supabase to store a chatbot's conversation history.

## Description

This project connects to the Evolution API WebSocket to receive chatbot messages and stores the conversation history in a Supabase database. It uses environment variables for configuration and is designed to be integrated into automation flows or conversation analysis pipelines.

## Project Structure

- `evolution_ws.py`: Connects to the Evolution WebSocket and manages incoming events.
- `handle_messages.py`: Formats and saves received messages to Supabase.
- `supabase_connector.py`: Handles connection and CRUD operations with Supabase.
- `requirements.txt`: List of project dependencies.

## Installation

1. Clone the repository.
2. Install the dependencies:
   ```fish
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   EVOLUTION_API_URL=...
   EVOLUTION_API_KEY=...
   EVOLUTION_API_INSTANCE=...
   VITE_SUPABASE_URL=...
   VITE_SUPABASE_ANON_KEY=...
   ```

## Usage

Run the main file to start the connection and begin storing messages:
```fish
python evolution_ws.py
```

## Example Flow

1. The WebSocket receives a new message.
2. The message is processed and formatted.
3. The message is stored in the `chatbot.conversation_history` table in Supabase.

## Main Dependencies

- `evolutionapi`
- `supabase`
- `python-dotenv`

## Notes

- Make sure your environment variables are properly configured.
- The project is designed to run continuously (daemon).
