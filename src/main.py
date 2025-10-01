#!/usr/bin/env python3
"""
Main entry point for the Evolution Connector application.
Orchestrates all components and starts the service.
"""
import os
from dotenv import load_dotenv

from evolution_ws import EvolutionConnector
from bot_manager import BotManager
from chat_bot import get_system_prompt

def main():
    """
    Main application entry point.
    
    Initializes and orchestrates all components of the Evolution Connector:
    - Loads environment variables from .env file
    - Creates Evolution API connector for WhatsApp integration
    - Loads system prompt for chatbot initialization
    - Initializes bot manager with pool of AI chatbots
    - Starts background monitoring for bot lifecycle management
    - Establishes WebSocket connection to receive WhatsApp messages
    
    Notes
    -----
    This function runs indefinitely, listening for incoming WhatsApp messages
    through the Evolution API WebSocket connection. The application will continue
    running until manually terminated.
    
    The function establishes a complete async architecture with:
    - Background event loop for database operations
    - Thread-safe message processing
    - Automatic bot pool management
    - Customer data persistence in Supabase
    
    Environment variables required:
    - EVOLUTION_API_URL: Base URL for Evolution API
    - EVOLUTION_INSTANCE: Instance name for Evolution API
    - EVOLUTION_API_KEY: Authentication key for Evolution API
    - SUPABASE_URL: Supabase project URL
    - SUPABASE_KEY: Supabase service key
    """
    load_dotenv()
    
    # Initialize components
    connector = EvolutionConnector()
    
    # Get system prompt
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(os.path.dirname(script_dir), "prompts", "initial_prompt.txt")
    prompt = get_system_prompt(prompt_path)
    
    # Initialize bot manager
    bot_manager = BotManager(prompt)
    
    # Start monitoring
    bot_manager.start_monitoring()
    
    # Define message handler
    def handle_message(data: dict):
        bot_manager.handle_message(connector, data)
    
    # Start listening
    print("🚀 Evolution Connector starting...")
    connector.start_listening(handle_message)

if __name__ == "__main__":
    main()