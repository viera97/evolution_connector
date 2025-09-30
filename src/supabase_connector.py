import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

supabase = None  # Supabase client instance

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

# Initialize Supabase client if credentials are available
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    # Raise error if credentials are missing
    raise ValueError("Environment variables SUPABASE_URL and/or SUPABASE_ANON_KEY are not defined.")

async def get_all_conversation_history():
    """
    Retrieves all conversation history records from Supabase asynchronously.

    Returns
    -------
    list
        A list of conversation history records.

    Raises
    -------
    RuntimeError
        If the Supabase client is not initialized.
    """
    if not supabase:
        raise RuntimeError("Supabase client is not initialized.")
    
    # Ejecutar la operación en un thread pool para no bloquear
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, 
        lambda: supabase.schema("chatbot").table('conversation_history').select('*').execute()
    )
    return response.data

async def get_all_customers():
    """
    Retrieves all customer records from Supabase asynchronously.

    Returns
    -------
    list
        A list of customer records.

    Raises
    -------
    RuntimeError
        If the Supabase client is not initialized.
    """
    if not supabase:
        raise RuntimeError("Supabase client is not initialized.")
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: supabase.table('customers').select('*').execute()
    )
    return response.data

def add_conversation_history(customer_id: str, message: dict):
    """
    Adds a new conversation history record to Supabase.

    Parameters
    ----------
    customer_id : int
        The ID of the customer.
    message : dict
        The message to be added to the history.

    Returns
    -------
    list
        The data returned by the Supabase client.

    Raises
    -------
    RuntimeError
        If the Supabase client is not initialized.
    """
    if not supabase:
        raise RuntimeError("Supabase client is not initialized.")
    data = {
        "customer_id": customer_id,
        "message": message,
    }
    response = supabase.schema("chatbot").table('conversation_history').insert(data).execute()
    return response.data

if __name__ == "__main__":
    # Retrieve all conversation history records
    data = get_all_conversation_history()
    example_message = {
        "type": "human",
        "content": "User with name and phone number 34685583840 sent the following message: hola\n\n\n\nIs a client of the company:\n0bc55fa1-b516-47b7-afc3-11f7f9250f03\nphone: 34662578011\n",
        "additional_kwargs": {},
        "response_metadata": {}
    }
    # Add a new conversation history record
    add_conversation_history(get_all_customers()[0]['id'], example_message)