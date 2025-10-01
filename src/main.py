#!/usr/bin/env python3

import os
import signal
import sys
import asyncio
from typing import Optional
from dotenv import load_dotenv

from evolution_ws import EvolutionConnector
from bot_manager import BotManager
from chat_bot import get_system_prompt

# Global variables for cleanup
connector: Optional[EvolutionConnector] = None
bot_manager: Optional[BotManager] = None

def signal_handler(signum, frame):
    """
    Handle shutdown signals (SIGINT, SIGTERM) for graceful cleanup.
    
    This function is called when the application receives a shutdown signal
    (typically Ctrl+C). It performs cleanup operations including:
    - Closing all bot instances
    - Stopping the bot manager monitoring
    - Disconnecting WebSocket connections
    - Shutting down async event loops
    
    Parameters
    ----------
    signum : int
        The signal number that triggered the handler.
    frame : frame object
        The current stack frame.
    """
    print("\n🛑 Shutdown signal received. Cleaning up...")
    
    try:
        if bot_manager:
            print("📋 Closing bot manager...")
            # Stop monitoring
            if hasattr(bot_manager, '_monitoring_active'):
                bot_manager._monitoring_active = False
            
            # Close all bots
            if hasattr(bot_manager, 'bots_dict'):
                print(f"🤖 Closing {len(bot_manager.bots_dict)} bot instances...")
                for key, bot_data in bot_manager.bots_dict.items():
                    try:
                        bot_instance = bot_data[1]
                        if hasattr(bot_instance, 'close'):
                            asyncio.run(bot_instance.close())
                            print(f"✅ Closed bot {key}")
                    except Exception as e:
                        print(f"⚠️  Error closing bot {key}: {e}")
            
            # Shutdown executor
            if hasattr(bot_manager, 'executor'):
                print("🔧 Shutting down thread pool executor...")
                bot_manager.executor.shutdown(wait=True)
        
        if connector:
            print("🌐 Disconnecting WebSocket...")
            # If the websocket has a disconnect method, call it
            if hasattr(connector, 'websocket') and hasattr(connector.websocket, 'disconnect'):
                connector.websocket.disconnect()
        
        print("✅ Cleanup completed successfully!")
        
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")
    
    finally:
        print("👋 Evolution Connector shutting down...")
        sys.exit(0)

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
    global connector, bot_manager
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
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
    
    # Start listening
    print("🚀 Evolution Connector starting...")
    print("💡 Press Ctrl+C to stop the application gracefully")
    
    try:
        # Define message handler with proper type checking
        def handle_message(data: dict):
            # At this point we know bot_manager and connector are not None
            assert bot_manager is not None
            assert connector is not None
            bot_manager.handle_message(connector, data)
        
        connector.start_listening(handle_message)
    except KeyboardInterrupt:
        # This shouldn't be reached due to signal handler, but just in case
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()