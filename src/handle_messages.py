import time
import os
from typing import Optional
import supabase_connector
import chat_bot
from fastchat import Fastchat

class OptimizedTimer:
    """Lightweight timer with minimal overhead and environment control."""
    
    def __init__(self):
        self.enabled = os.getenv("TIMING_DEBUG", "true").lower() == "true"
        self.start_time = None
        self.operation_name = None
        self.phone = None
    
    def start(self, operation_name: str, phone: Optional[str] = None):
        """Start timing an operation."""
        if not self.enabled:
            return
        
        self.operation_name = operation_name
        self.phone = phone
        self.start_time = time.time()
        
        # Only log critical operations to reduce noise
        if any(critical in operation_name for critical in ["GET_CHATBOT_RESPONSE", "CHAT_BOT_PROCESSING"]):
            phone_info = f" for {phone}" if phone else ""
            print(f"⏱️ {operation_name}{phone_info}")
    
    def end(self, details: Optional[str] = None):
        """End timing and log if slow or critical."""
        if not self.enabled or self.start_time is None:
            return 0
        
        duration = time.time() - self.start_time
        
        # Only log if slow (>1s) or critical operations
        should_log = (
            duration > 1.0 or 
            (self.operation_name and any(critical in self.operation_name for critical in ["GET_CHATBOT_RESPONSE", "CHAT_BOT_PROCESSING"])) or
            "ERROR" in (details or "")
        )
        
        if should_log:
            phone_info = f" for {self.phone}" if self.phone else ""
            details_info = f" - {details}" if details else ""
            
            # Simplified color coding
            emoji = "�" if duration > 2.0 else "🟡" if duration > 0.5 else "�"
            print(f"{emoji} {self.operation_name}{phone_info} {duration:.2f}s{details_info}")
        
        # Reset
        self.start_time = None
        self.operation_name = None
        self.phone = None
        return duration

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

async def save_message(data: dict, is_bot: bool = False, customer_id: str = "") -> None:
    """
    Saves the formatted message to the conversation history in Supabase with timing.

    Parameters
    ----------
    data : dict
        The input data containing the message information.
    is_bot : bool
        Whether this is a bot message or user message.
    customer_id : str
        The customer ID to associate with the message.
    """
    timer = OptimizedTimer()
    timer.start("SAVE_MESSAGE_TO_DB")
    
    try:
        formatted_data = format_message(data, is_bot)
        await supabase_connector.add_conversation_history(customer_id=customer_id, message=formatted_data)
        timer.end(f"{'bot' if is_bot else 'user'} message for customer {customer_id}")
    except Exception as e:
        timer.end(f"ERROR: {e}")
        raise

async def get_chatbot_response(bot: Fastchat, data: dict):
    """
    Sends a query to the chatbot and returns its response with detailed timing.

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
    timer = OptimizedTimer()
    timer.start("GET_CHATBOT_RESPONSE")
    
    try:
        query = data.get("message", {}).get("conversation", "")
        print(f"🤖 Querying chatbot with: '{query[:100]}{'...' if len(query) > 100 else ''}'")
        
        # This is likely the main bottleneck - measure it separately
        chat_timer = OptimizedTimer()
        chat_timer.start("CHAT_BOT_PROCESSING")
        response = await chat_bot.chating(bot, query)
        chat_duration = chat_timer.end(f"response length: {len(response)} chars")
        
        total_duration = timer.end(f"query: '{query[:50]}...', response: '{response[:50]}...'")
        
        # Log slow responses
        if total_duration and total_duration > 5.0:
            print(f"🐌 SLOW AI RESPONSE: {total_duration:.3f}s for query: '{query[:100]}'")
        
        return response
    except Exception as e:
        timer.end(f"ERROR: {e}")
        print(f"❌ Error getting chatbot response: {e}")
        raise