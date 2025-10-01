#!/usr/bin/env python3
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test core modules
        from evolution_ws import EvolutionConnector
        print("✅ EvolutionConnector imported successfully")
        
        from bot_manager import BotManager
        print("✅ BotManager imported successfully")
        
        # Test chat_bot functions (async and sync)
        from chat_bot import initialize, chating, get_system_prompt
        print("✅ Chat bot functions imported successfully")
        
        # Test handle_messages functions (async and sync)
        from handle_messages import format_message, save_message, get_chatbot_response
        print("✅ Handle messages functions imported successfully")
        
        # Test supabase_connector functions (async and sync)
        from supabase_connector import (
            get_all_conversation_history,
            get_customers, 
            add_customers, 
            add_conversation_history
        )
        print("✅ Supabase connector functions imported successfully")
        
        # Test main module
        import main
        print("✅ Main module imported successfully")
        
        print("\n🎉 All imports successful! The reorganized structure is working correctly.")
        print("📋 Available functions:")
        print("   • chat_bot: initialize (async), chating (async), get_system_prompt")
        print("   • handle_messages: format_message, save_message (async), get_chatbot_response (async)")
        print("   • supabase_connector: get_all_conversation_history, get_customers (async), add_customers (async), add_conversation_history (async)")
        print("   • bot_manager: BotManager class with async architecture")
        print("   • evolution_ws: EvolutionConnector")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()