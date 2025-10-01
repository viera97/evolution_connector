import os
import time
from dotenv import load_dotenv
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
from evolutionapi.models.chat import Presence
from evolutionapi.models.profile import FetchProfile
import asyncio
import supabase_connector

class EvolutionConnector:
    """
    Main connector class for Evolution API.

    This class handles the connection to the Evolution API, including
    WebSocket for real-time events and sending messages.

    Attributes
    ----------
    api_url : str
        The URL of the Evolution API.
    api_key : str
        The API key for the Evolution API.
    instance_id : str
        The instance ID for the Evolution API.
    client : EvolutionClient
        The Evolution API client.
    websocket : any
        The WebSocket manager for real-time events.
    """
    def __init__(self):
        """
        Initializes the EvolutionConnector.

        Raises
        ------
        ValueError
            If any of the required environment variables are not set.
        """
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
        """
        Starts listening for incoming messages.

        Parameters
        ----------
        handle_message_fn : function
            The function to be called when a message is received.
        """
        self.websocket.on("messages.upsert", handle_message_fn)
        self.websocket.connect()

        print("Connected to WebSocket. Waiting for events...")
        # Keep the process alive to listen for events
        while True:
            time.sleep(1)
    
    def fetch_username(self, phone: str) -> str | None:
        """
        Fetches the username/profile name for a given phone number from WhatsApp.
        
        This method retrieves the WhatsApp profile information for the specified
        phone number using the Evolution API. It attempts to extract the display
        name from the user's WhatsApp profile.

        Parameters
        ----------
        phone : str
        The phone number to fetch the username for (without country code prefix).
        Returns
        -------
        str or None
            The username/display name if found, None if not available or if an error occurs.
        Raises
        ------
        Exception
        Any exception that occurs during the API call to fetch the profile.
        """

        # Validate required credentials
        if not self.instance_id or not self.api_key:
            return None
            
        # Create profile config with the actual sender's phone number
        config = FetchProfile(number=phone)
        
        # Fetch profile using correct parameters
        profile_response = self.client.profile.fetch_profile(
            instance_id=self.instance_id,
            data=config,
            instance_token=self.api_key
        )
        
        # Extract user name if available
        user_name = None
        if profile_response and hasattr(profile_response, 'name'):
            user_name = profile_response.name
        elif isinstance(profile_response, dict) and 'name' in profile_response:
            user_name = profile_response['name']
        
        return user_name

    def send_presence(self, to: str, presence_type: str = "composing", delay: int = 100000):
        """
        Sends a WhatsApp presence status (e.g., typing indicator).

        Parameters
        ----------
        to : str
            The recipient's phone number.
        presence_type : str, optional
            The type of presence to send. Defaults to "composing".
        delay : int, optional
            The delay in milliseconds. Defaults to 100000.

        Raises
        ------
        ValueError
            If instance_id or api_key are not set.
        """
        if not self.instance_id or not self.api_key:
            raise ValueError("instance_id and api_key must be set and not None.")
        presence_config = Presence(
            number=to,
            delay=delay,  # milliseconds
            presence=presence_type  # "composing" means typing
        )
        self.client.chat.send_presence(self.instance_id, presence_config, self.api_key)

    def send_message(self, to: str, message: str):
        """
        Sends a WhatsApp text message using Evolution API.

        Parameters
        ----------
        to : str
            The recipient's phone number.
        message : str
            The message to be sent.

        Raises
        ------
        ValueError
            If instance_id or api_key are not set.

        Returns
        -------
        any
            The response from the API.
        """
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
    import threading

    connector = EvolutionConnector()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Obtaining initial prompt
    prompt_path = os.path.join(os.path.dirname(script_dir), "prompts", "initial_prompt.txt")
    prompt = get_system_prompt(prompt_path)

    # Dictionary to store bot instances. Keys 'A1', 'A2', 'A3' are extra bots always available for assignment.
    bots_dict = {
        #key: [starting time, bot, running]
        'A1': [time.time(), asyncio.run(initialize(prompt)), True],
        'A2': [time.time(), asyncio.run(initialize(prompt)), True],
        'A3': [time.time(), asyncio.run(initialize(prompt)), True]
    }

    def monitor_inactive_bots():
        """
        Monitors assigned bot instances and manages inactive bots based on total count:
        - If more than 10 bots assigned: closes inactive bots
        - If 10 or fewer bots assigned: converts inactive bots to pool bots (A prefix)
        Only checks bots assigned to users (not pool bots starting with 'A').
        Runs in a separate thread and checks every 30 seconds.
        """
        while True:
            current_time = time.time()
            inactive_threshold = 20 * 60  # 20 minutes in seconds
            bots_to_remove = []  # List to store keys of bots to remove
            bots_to_convert = []  # List to store bots to convert to pool
            
            # Count assigned bots (not pool bots)
            assigned_bots = [key for key in bots_dict.keys() if not key.startswith('A')]
            assigned_bot_count = len(assigned_bots)
            
            for key, bot_data in bots_dict.items():
                # Only monitor bots assigned to users (skip pool bots starting with 'A')
                if not key.startswith('A'):
                    last_interaction_time = bot_data[0]
                    is_active = bot_data[2]
                    bot_instance = bot_data[1]  # The Fastchat bot instance
                    time_since_last_interaction = current_time - last_interaction_time
                    
                    # Check if bot has been inactive for more than 20 minutes
                    if time_since_last_interaction > inactive_threshold:
                        
                        if assigned_bot_count > 10:
                            # More than 10 bots: close the inactive ones
                            print(f"Closing bot {key} - inactive for {time_since_last_interaction/60:.1f} minutes (total bots: {assigned_bot_count})")
                            
                            try:
                                # Close the Fastchat bot instance (async method)
                                asyncio.run(bot_instance.close())
                                print(f"Successfully closed bot {key}")
                            except Exception as e:
                                print(f"Error closing bot {key}: {e}")
                            
                            # Mark for removal from dictionary
                            bots_to_remove.append(key)
                            
                        else:
                            # 10 or fewer bots: convert to pool bot
                            print(f"Converting bot {key} to pool bot - inactive for {time_since_last_interaction/60:.1f} minutes (total bots: {assigned_bot_count})")
                            bots_to_convert.append(key)
            
            # Remove closed bots from dictionary
            for key in bots_to_remove:
                if key in bots_dict:
                    del bots_dict[key]
                    print(f"Removed bot {key} from active dictionary")
            
            # Convert inactive bots to pool bots
            for key in bots_to_convert:
                if key in bots_dict:
                    bot_data = bots_dict[key]
                    # Find next available A key
                    existing_a_keys = [k for k in bots_dict.keys() if k.startswith('A')]
                    if existing_a_keys:
                        next_index = max([int(k[1:]) for k in existing_a_keys]) + 1
                    else:
                        next_index = 1
                    new_key = f"A{next_index}"
                    
                    # Move bot to pool with new timestamp and active status
                    bots_dict[new_key] = [time.time(), bot_data[1], True]
                    del bots_dict[key]
                    print(f"Converted bot {key} to pool bot {new_key}")
            
            # Wait 30 seconds before next check
            time.sleep(30)

    # Start the monitoring thread
    monitor_thread = threading.Thread(target=monitor_inactive_bots, daemon=True)
    monitor_thread.start()
    
    print("Started bot inactivity monitor (checks every 30 seconds)")
    
    def handle_message(data: dict):
        """
        Handles incoming messages from the WebSocket.

        Parameters
        ----------
        data : dict
            The message data received from the WebSocket.
        """
        # Only process messages not sent by ourselves
        if not data["data"]["key"]["fromMe"]:
            # Only handle WhatsApp private messages
            if data["data"]['key']['remoteJid'].split('@')[1] == "s.whatsapp.net":
                phone = data["data"]['key']['remoteJid'].split('@')[0]

                # Fetch user profile for better customer experience
                # Validate required credentials
                if not connector.instance_id or not connector.api_key:
                    raise ValueError("instance_id and api_key must be set to fetch profile.")

                # If this phone number does not have a bot assigned
                if phone not in bots_dict:
                    # Find available extra bot keys (those starting with 'A')
                    extra_keys = [k for k in bots_dict if k.startswith('A')]
                    if extra_keys:
                        # Assign the first available extra bot to this phone
                        first_extra = extra_keys[0]
                        bots_dict[phone] = bots_dict.pop(first_extra)
                        
                        # Only add a new extra bot if we have less than 3 available instances
                        remaining_extra_keys = [k for k in bots_dict if k.startswith('A')]
                        if len(remaining_extra_keys) < 3:
                            next_index = max([int(k[1:]) for k in bots_dict if k.startswith('A')], default=0) + 1
                            new_key = f"A{next_index}"
                            bots_dict[new_key] = [time.time(), asyncio.run(initialize(prompt)), True]
                            #!Debuging
                            print(f"Created new bot instance: {new_key}")
                        else:
                            #!Debuging
                            print(f"Pool has enough instances ({len(remaining_extra_keys)}), not creating new bot")

                # If the phone number has a bot assigned and the bot is running
                if bots_dict[phone][2]:
                    #Update time in dictionary when bot is active and will respond
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

                    # Create or update customer in Supabase with profile information
                    
                    existing_customers = supabase_connector.get_customers(phone=phone)
                    if len(existing_customers) == 0:
                        username = connector.fetch_username(phone)
                        print(supabase_connector.add_customers(phone=phone, username=username))

                    #Save message in supabase
                    handle_messages.save_message(data["data"], customer_id=supabase_connector.get_customers(phone=phone)[0]['id'])
                    
                    data["data"]["message"] = response
                    handle_messages.save_message(data["data"], is_bot=True, customer_id=supabase_connector.get_customers(phone=phone)[0]['id'])

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