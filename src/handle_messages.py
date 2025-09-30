import uuid
import supabase_connector
import chat_bot
from fastchat import Fastchat
import asyncio

def format_message(data: dict, is_bot: bool = False) -> dict:
    """
    Formats the message data into the required structure for the 'message' (jsonb) field.

    Parameters
    ----------
    data : dict
        The input data containing the message information.

    Returns
    -------
    dict
        A dictionary with the formatted message data.
    """

    if is_bot:
        content = data["message"]  # Extracts the bot's message content
    else:
        content = data.get("message", {}).get("conversation", ""),  # Extracts the message content
    return {
        "type": f"{'bot' if is_bot else 'human'}",  # Indicates the message type (currently set to 'human')
        "content": f"{content}",
        "additional_kwargs": {},  # Placeholder for additional arguments
        "response_metadata": {}   # Placeholder for response metadata
    }

def save_message(data: dict, is_bot: bool = False, customer_id:str ="") -> None:
    """
    Saves the formatted message to the conversation history in Supabase.

    Parameters
    ----------
    data : dict
        The input data containing the message information.
    """
    data = format_message(data, is_bot)
    customer_id = customer_id
    #conversation_id = str(uuid.uuid4())
    supabase_connector.add_conversation_history(customer_id=customer_id, message=data)

def get_chatbot_response(bot: Fastchat, data: dict):
    """
    Sends a query to the chatbot and returns its response.

    Parameters
    ----------
    bot : Fastchat
        The Fastchat instance to which the query will be sent.
    data : dict
        The input data containing the message information.

    Returns
    -------
    str
        The response from the chatbot.
    """
    query = data.get("message", {}).get("conversation", "")
    return asyncio.run(chat_bot.chating(bot, query))