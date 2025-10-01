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
    """Main application entry point."""
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