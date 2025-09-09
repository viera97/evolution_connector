import uuid
import supabase_connector

def format_message(data):
    # Formato requerido para el campo message (jsonb)
    return {
        #TODO Ver cuando el bot envíe algo cómo identificarlo
        "type": "human",
        "content": data.get("message", {}).get("conversation", ""),
        "additional_kwargs": {},
        "response_metadata": {}
    }

def save_message(data):
    data = format_message(data)
    conversation_id = str(uuid.uuid4())
    supabase_connector.add_conversation_history(conversation_id, data)