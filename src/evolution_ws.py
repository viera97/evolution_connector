import os
import time
from dotenv import load_dotenv
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
from evolutionapi.models.chat import Presence
import asyncio

# Main connector class for Evolution API
class EvolutionConnector:
    def __init__(self):
        # Load environment variables for API credentials
        load_dotenv()
        self.api_url = os.getenv("EVOLUTION_API_URL")
        self.api_key = os.getenv("EVOLUTION_API_KEY")
        self.instance_id = os.getenv("EVOLUTION_API_INSTANCE")

        # Validate required environment variables
        if not self.api_url:
            raise ValueError("EVOLUTION_API_URL environment variable is not set.")
        if not self.api_key:
            raise ValueError("EVOLUTION_API_KEY environment variable is not set.")
        if not self.instance_id:
            raise ValueError("EVOLUTION_API_INSTANCE environment variable is not set.")

        # Initialize Evolution API client
        self.client = EvolutionClient(
            base_url=self.api_url,
            api_token=self.api_key
        )

        # Create WebSocket manager for real-time events
        self.websocket = self.client.create_websocket(
            instance_id=self.instance_id,
            api_token=self.api_key,
            max_retries=5,
            retry_delay=1.0
        )

    def start_listening(self, handle_message_fn):
        # Register callback for incoming messages
        self.websocket.on("messages.upsert", handle_message_fn)
        self.websocket.connect()
        print("Connected to WebSocket. Waiting for events...")
        # Keep the process alive to listen for events
        while True:
            time.sleep(1)

    def send_presence(self, to:str, presence_type :str ="composing", delay : int =100000):
        # Send WhatsApp presence status (e.g., typing indicator)
        if not self.instance_id or not self.api_key:
            raise ValueError("instance_id and api_key must be set and not None.")
        presence_config = Presence(
            number=to,
            delay=delay,  # milliseconds
            presence=presence_type  # "composing" means typing
        )
        self.client.chat.send_presence(self.instance_id, presence_config, self.api_key)
    

    def send_message(self, to:str, message:str):
        # Send a WhatsApp text message using Evolution API
        if not self.instance_id or not self.api_key:
            raise ValueError("instance_id and api_key must be set and not None.")
        text_msg = TextMessage(
            number=to,
            text=message
        )
        return self.client.messages.send_text(self.instance_id, text_msg, self.api_key)

if __name__ == "__main__":
    import handle_messages
    from chat_bot import initialize, get_system_prompt

    connector = EvolutionConnector()

    # Dictionary to store bot instances. Keys 'A1', 'A2', 'A3' are extra bots always available for assignment.
    # Use absolute path that works both locally and in Docker
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(os.path.dirname(script_dir), "prompts", "initial_prompt.txt")
    prompt = get_system_prompt(prompt_path)

    bots_dict = {
        #key: [starting time, bot, running]
        'A1': [time.time(), asyncio.run(initialize(prompt)), True],
        'A2': [time.time(), asyncio.run(initialize(prompt)), True],
        'A3': [time.time(), asyncio.run(initialize(prompt)), True]
    }
    
    def handle_message(data:dict):
        # Only process messages not sent by ourselves
        if not data["data"]["key"]["fromMe"]:
            # Only handle WhatsApp private messages
            if data["data"]['key']['remoteJid'].split('@')[1] == "s.whatsapp.net":
                phone = data["data"]['key']['remoteJid'].split('@')[0]

                # If this phone number does not have a bot assigned
                if phone not in bots_dict:
                    # Find available extra bot keys (those starting with 'A')
                    extra_keys = [k for k in bots_dict if k.startswith('A')]
                    if extra_keys:
                        # Assign the first available extra bot to this phone
                        first_extra = extra_keys[0]
                        bots_dict[phone] = bots_dict.pop(first_extra)
                        # Add a new extra bot to maintain the pool of 3
                        next_index = max([int(k[1:]) for k in bots_dict if k.startswith('A')], default=0) + 1
                        new_key = f"A{next_index}"
                        bots_dict[new_key] = [time.time(), asyncio.run(initialize(prompt))]

                # If the phone number has a bot assigned and the bot is running
                if bots_dict[phone][2]:
                    #Update time in dictionary
                    bots_dict[phone][0] = time.time()

                    #TODO revisar como hacer bien lo del composing
                    #Indicate typing status
                    #connector.send_presence(phone, presence_type="composing")

                    #Get bot response

                    #!Debuging
                    print("respondiendo a ", phone)
                    response = handle_messages.get_chatbot_response(bots_dict[phone][1], data["data"])
                    #!Debuging
                    print(response)

                    connector.send_message(phone, response)

                    #Save message in supabase
                    handle_messages.save_message(data["data"])
        else:
            # If the message is from ourselves and to a private chat
            if data["data"]['key']['remoteJid'].split('@')[1] == "s.whatsapp.net":
                phone = data["data"]['key']['remoteJid'].split('@')[0]

                # If our message is the start command "/start"
                if data["data"].get("message", {}).get("conversation", "") == "/start":
                    if phone in bots_dict:
                        bots_dict[phone][2] = True
                        connector.send_message(phone, "Bot reactivado. ¿En qué puedo ayudarte?")

                # Else stop the bot
                else:
                    if phone in bots_dict:
                        bots_dict[data["data"]['key']['remoteJid'].split('@')[0]][2] = False

    # Start listening for incoming messages
    connector.start_listening(handle_message)