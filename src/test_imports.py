#!/usr/bin/env python3
"""
Test script to verify that all modules import correctly 
and the reorganized structure is working.
"""

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test core modules
        from evolution_ws import EvolutionConnector
        print("✅ EvolutionConnector imported successfully")
        
        from bot_manager import BotManager
        print("✅ BotManager imported successfully")
        
        from chat_bot import initialize, get_system_prompt
        print("✅ Chat bot functions imported successfully")
        
        from handle_messages import save_message, get_chatbot_response
        print("✅ Handle messages functions imported successfully")
        
        from supabase_connector import get_customers, add_customers, add_conversation_history
        print("✅ Supabase connector functions imported successfully")
        
        # Test main module
        import main
        print("✅ Main module imported successfully")
        
        print("\n🎉 All imports successful! The reorganized structure is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()