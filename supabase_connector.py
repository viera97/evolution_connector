import os
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
    # Retrieves all conversation history records from Supabase
    if not supabase:
        raise RuntimeError("Supabase client is not initialized.")
    # Query using the full schema and table name
    response = supabase.schema("chatbot").table('conversation_history').select('*').execute()
    return response.data

def add_conversation_history(session_id: str, message: dict):
    # Adds a new conversation history record to Supabase
    if not supabase:
        raise RuntimeError("Supabase client is not initialized.")
    data = {
        "session_id": session_id,
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
    add_conversation_history("session123", example_message)