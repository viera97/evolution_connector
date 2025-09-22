import uuid
import supabase_connector
import chat_bot
from fastchat import Fastchat
import asyncio

def format_message(data:dict) -> dict:
    # Formats the message data into the required structure for the 'message' (jsonb) field
    return {
        #TODO Determine how to identify when the bot sends a message
        "type": "human",  # Indicates the message type (currently set to 'human')
        "content": data.get("message", {}).get("conversation", ""),  # Extracts the message content
        "additional_kwargs": {},  # Placeholder for additional arguments
        "response_metadata": {}   # Placeholder for response metadata
    }

def save_message(data:dict):
    # Saves the formatted message to the conversation history in Supabase
    data = format_message(data)  # Format the incoming data
    conversation_id = str(uuid.uuid4())  # Generate a unique conversation ID
    supabase_connector.add_conversation_history(conversation_id, data)  # Store the message

def get_chatbot_response(bot:Fastchat, data:dict):
    # Sends a query to the chatbot and returns its response
    query = data.get("message", {}).get("conversation", "")  # Extracts the query from the message
    return asyncio.run(chat_bot.chating(bot, query))  # Runs the chatbot response asynchronously