import os
import time
from dotenv import load_dotenv
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage
from evolutionapi.models.chat import Presence
from evolutionapi.models.profile import FetchProfile

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

