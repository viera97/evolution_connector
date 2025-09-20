import uuid
import supabase_connector
import chat_bot
from fastchat import Fastchat
import asyncio

def format_message(data:dict) -> dict:
    # Formato requerido para el campo message (jsonb)
    return {
        #TODO Ver cuando el bot envíe algo cómo identificarlo
        "type": "human",
        "content": data.get("message", {}).get("conversation", ""),
        "additional_kwargs": {},
        "response_metadata": {}
    }

def save_message(data:dict):
    data = format_message(data)
    conversation_id = str(uuid.uuid4())
    supabase_connector.add_conversation_history(conversation_id, data)

def get_chatbot_response(bot:Fastchat, data:dict):
    query = data.get("message", {}).get("conversation", "")
    return asyncio.run(chat_bot.chating(bot, query))