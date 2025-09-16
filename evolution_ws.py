import os
import time
from dotenv import load_dotenv
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
class EvolutionConnector:
    def __init__(self):
        load_dotenv()
        self.api_url = os.getenv("EVOLUTION_API_URL")
        self.api_key = os.getenv("EVOLUTION_API_KEY")
        self.instance_id = os.getenv("EVOLUTION_API_INSTANCE")

        if not self.api_url:
            raise ValueError("La variable de entorno EVOLUTION_API_URL no está definida.")
        if not self.api_key:
            raise ValueError("La variable de entorno EVOLUTION_API_KEY no está definida.")
        if not self.instance_id:
            raise ValueError("La variable de entorno EVOLUTION_API_INSTANCE no está definida.")

        self.client = EvolutionClient(
            base_url=self.api_url,
            api_token=self.api_key
        )
        self.websocket = self.client.create_websocket(
            instance_id=self.instance_id,
            api_token=self.api_key,
            max_retries=5,
            retry_delay=1.0
        )

    def start_listening(self, handle_message_fn):
        self.websocket.on("messages.upsert", handle_message_fn)
        self.websocket.connect()
        print("Conectado al WebSocket. Esperando eventos...")
        while True:
            time.sleep(1)

    def send_message(self, to, message):
        if not self.instance_id or not self.api_key:
            raise ValueError("instance_id and api_key must be set and not None.")
        text_msg = TextMessage(
            number=to,
            text=message
        )
        return self.client.messages.send_text(self.instance_id, text_msg, self.api_key)
    

# Example usage:
if __name__ == "__main__":
    import handle_messages
    
    connector = EvolutionConnector()

    def handle_message(data):
        if not data["data"]["key"]["fromMe"]:
            #print(data["data"])
            phone = data["data"]['key']['remoteJid'].split('@')[0]
            #TODO poner que esta escribiendo el bot
            response = handle_messages.get_chatbot_response(data["data"])
            connector.send_message(phone, response)
            handle_messages.save_message(data["data"])

    connector.start_listening(handle_message)