import os
import time
from dotenv import load_dotenv
from evolutionapi.client import EvolutionClient
import handle_messages

load_dotenv()


EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_API_INSTANCE = os.getenv("EVOLUTION_API_INSTANCE")

if not EVOLUTION_API_URL:
    raise ValueError("La variable de entorno EVOLUTION_API_URL no está definida.")
if not EVOLUTION_API_KEY:
    raise ValueError("La variable de entorno EVOLUTION_API_KEY no está definida.")
if not EVOLUTION_API_INSTANCE:
    raise ValueError("La variable de entorno EVOLUTION_API_INSTANCE no está definida.")

client = EvolutionClient(
    base_url=EVOLUTION_API_URL,
    api_token=EVOLUTION_API_KEY
)

websocket = client.create_websocket(
    instance_id=EVOLUTION_API_INSTANCE,
    api_token=EVOLUTION_API_KEY,
    max_retries=5,
    retry_delay=1.0
)

def handle_message(data):
    if not data["data"]["key"]["fromMe"]:
        handle_messages.save_message(data["data"])

websocket.on("messages.upsert", handle_message)

websocket.connect()
print("Conectado al WebSocket. Esperando eventos...")

while True:
    time.sleep(1)