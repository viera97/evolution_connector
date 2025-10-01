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
supabase = None
if SUPABASE_URL is not None and SUPABASE_ANON_KEY is not None:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    # Raise error if credentials are missing
    raise ValueError("Environment variables VITE_SUPABASE_URL and/or VITE_SUPABASE_ANON_KEY are not defined.")

def get_all_conversation_history():
    """
    Retrieves all conversation history records from Supabase.

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
    # Query using the full schema and table name
    response = supabase.schema("chatbot").table('conversation_history').select('*').execute()
    return response.data

async def get_customers(phone: str | None = None, customer_id: str | None = None):
    """
    Retrieves customer records from Supabase, optionally filtered by phone number or customer ID.

    Parameters
    ----------
    phone : str, optional
        The phone number to filter by. If None, no phone filter is applied.
    customer_id : str, optional
        The customer ID to filter by. If None, no ID filter is applied.

    Returns
    -------
    list
        A list of customer records matching the criteria.

    Raises
    -------
    RuntimeError
        If the Supabase client is not initialized.
    ValueError
        If both phone and customer_id are provided (mutually exclusive).
    """
    if not supabase:
        raise RuntimeError("Supabase client is not initialized.")
    
    # Validate that only one filter is provided
    if phone is not None and customer_id is not None:
        raise ValueError("Cannot filter by both phone and customer_id. Use only one parameter.")
    
    # Start building the query
    query = supabase.table('customers').select('*')
    
    # Add phone filter if provided
    if phone is not None:
        query = query.eq('phone', phone)
    
    # Add customer_id filter if provided
    if customer_id is not None:
        query = query.eq('id', customer_id)
    
    # Execute the query
    response = query.execute()
    return response.data

async def add_customers(phone: str, username:str | None = None):
    """
    Adds a new customer record to Supabase.

    Parameters
    ----------
    phone : str
        The phone number of the customer.

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
        "phone": phone,
        "user_name":username
    }
    response = supabase.table('customers').insert(data).execute()
    return response.data

async def add_conversation_history(customer_id: str, message: dict):
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

async def main_example():
    """Example usage of the async functions."""
    # Retrieve all conversation history records
    data = get_all_conversation_history()
    print(f"Found {len(data)} conversation records")
    
    # Example: Get all customers
    all_customers = await get_customers()
    print(f"Found {len(all_customers)} customers")
    
    # Example: Get customer by phone
    customer_by_phone = await get_customers(phone="34662578011")
    print(f"Found {len(customer_by_phone)} customers with that phone")
    
    # Example: Get customer by ID
    if all_customers:
        customer_by_id = await get_customers(customer_id=all_customers[0]['id'])
        print(f"Found {len(customer_by_id)} customers with that ID")
    
    example_message = {
        "type": "human",
        "content": "Test message",
        "additional_kwargs": {},
        "response_metadata": {}
    }
    
    # Add a new conversation history record if we have customers
    if all_customers:
        await add_conversation_history(all_customers[0]['id'], example_message)
        print("Added test conversation")

if __name__ == "__main__":
    asyncio.run(main_example())