import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase = None

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

supabase = None
if SUPABASE_URL is not None and SUPABASE_ANON_KEY is not None:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    raise ValueError("Las variables de entorno VITE_SUPABASE_URL y/o VITE_SUPABASE_ANON_KEY no están definidas.")

def get_all_conversation_history():
    if not supabase:
        raise RuntimeError("Supabase client no está inicializado.")
    # Consulta usando el nombre completo del esquema y tabla
    response = supabase.schema("chatbot").table('conversation_history').select('*').execute()
    return response.data

def add_conversation_history(session_id: str, message: dict):
    
    if not supabase:
        raise RuntimeError("Supabase client no está inicializado.")
    data = {
        "session_id": session_id,
        "message": message,
    }
    response = supabase.schema("chatbot").table('conversation_history').insert(data).execute()
    return response.data

# Ejemplo de uso:
if __name__ == "__main__":
    data = get_all_conversation_history()
    example_message = {
        "type": "human",
        "content": "El usuario con nombre  y número de teléfono 34685583840, envió el siguiente mensaje:hola\n\n\n\nEs cliente de la compañia:\n0bc55fa1-b516-47b7-afc3-11f7f9250f03\nphone: 34662578011\n",
        "additional_kwargs": {},
        "response_metadata": {}
    }
    add_conversation_history("session123", example_message)