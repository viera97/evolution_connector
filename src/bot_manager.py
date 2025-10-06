import time
import asyncio
import threading
from typing import Dict
from concurrent.futures import ThreadPoolExecutor

import handle_messages
import supabase_connector
from chat_bot import initialize, chating

class BotManager:
    """Manages bot instances, assignment, and lifecycle."""
    
    def __init__(self, prompt: str):
        """
        Initialize bot manager with system prompt.
        
        Creates the initial pool of bots, starts the async event loop in a background
        thread, and sets up the thread pool executor for async operations.
        
        Parameters
        ----------
        prompt : str
            The system prompt to be used by all bot instances.
        """
        self.prompt = prompt
        self.bots_dict = self._initialize_bot_pool()
        self._monitoring_active = False
        # Create a thread pool executor for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        # Create and start an event loop in a background thread
        self.loop = None
        self.loop_thread = None
        self._start_async_loop()
    
    def _start_async_loop(self):
        """
        Start an asyncio event loop in a background thread.
        
        Creates a new event loop and runs it in a daemon thread to handle
        async operations without blocking the main thread. This allows the
        WebSocket callback to schedule async operations.
        
        Notes
        -----
        The event loop runs indefinitely in the background thread until
        the application terminates.
        """
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        # Wait a bit for the loop to start
        import time
        time.sleep(0.1)
    
    def _initialize_bot_pool(self) -> Dict:
        """
        Initialize the initial pool of available bots.
        
        Creates three bot instances (A1, A2, A3) that are immediately available
        for assignment to users. Each bot is initialized with the system prompt
        and marked as active.
        
        Returns
        -------
        Dict
            A dictionary mapping bot IDs to [timestamp, bot_instance, active_status].
            The timestamp tracks the last interaction time, bot_instance is the
            Fastchat object, and active_status is a boolean indicating if the bot
            is currently responding to messages.
        """
        return {
            'A1': [time.time(), asyncio.run(initialize(self.prompt)), True],
            'A2': [time.time(), asyncio.run(initialize(self.prompt)), True],
            'A3': [time.time(), asyncio.run(initialize(self.prompt)), True]
        }
    
    async def _send_new_conversation_signal(self, bot_instance):
        """
        Send a signal to the bot indicating a new conversation is starting.
        
        Sends an internal system message to the bot to reset its conversational
        context without clearing the system prompt or configuration. This is used
        when converting inactive bots back to the pool.
        
        Parameters
        ----------
        bot_instance : Fastchat
            The bot instance to send the signal to.
            
        Notes
        -----
        The message is processed internally by the bot and not stored in
        conversation history or returned as a response.
        """
        new_conversation_message = "SISTEMA: Se va a iniciar una nueva conversación. Olvida el contexto anterior y prepárate para atender a un nuevo cliente."
        # Send the message but don't store it in conversation history
        async for step in bot_instance(new_conversation_message):
            pass  # Just process the message internally, don't return response
    
    def start_monitoring(self):
        """
        Start the bot monitoring thread.
        
        Initiates a daemon thread that monitors inactive bots and manages their
        lifecycle. The monitor checks every 30 seconds for bots that have been
        inactive for more than 20 minutes and either closes them or converts
        them back to the pool depending on the total number of assigned bots.
        
        Notes
        -----
        The monitoring thread is started only once. Subsequent calls to this
        method will be ignored if monitoring is already active.
        """
        if not self._monitoring_active:
            monitor_thread = threading.Thread(target=self._monitor_inactive_bots, daemon=True)
            monitor_thread.start()
            self._monitoring_active = True
            print("📊 Started bot inactivity monitor (checks every 30 seconds)")
    
    def handle_message(self, connector, data: dict):
        """
        Handle incoming message and manage bot assignment.
        
        Processes incoming WhatsApp messages by assigning bots to users and
        scheduling async operations to handle message processing and database
        operations. Also handles bot commands for activation/deactivation.
        
        Parameters
        ----------
        connector : EvolutionConnector
            The Evolution API connector instance for sending messages.
        data : dict
            The message data received from the WebSocket containing user info,
            message content, and metadata.
            
        Notes
        -----
        Only processes messages from private WhatsApp chats (not groups).
        Uses the background event loop for async operations to avoid blocking
        the WebSocket callback.
        """
        # Only process messages not sent by ourselves
        if not data["data"]["key"]["fromMe"]:
            if data["data"]['key']['remoteJid'].split('@')[1] == "s.whatsapp.net":
                phone = data["data"]['key']['remoteJid'].split('@')[0]
                # Schedule async operation in background event loop
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._process_user_message(connector, phone, data), 
                        self.loop
                    )
                else:
                    print("❌ Event loop not available, processing message synchronously")
                    # Fall back to sync processing - assign bot if needed
                    if phone not in self.bots_dict:
                        self._assign_bot_to_user(phone)
                    
                    if phone in self.bots_dict and self.bots_dict[phone][2]:
                        self.bots_dict[phone][0] = time.time()
                        print(f"📱 Responding to {phone}")
                        # Note: This will still have the chating warning, but it's a fallback
                        response = asyncio.run(handle_messages.get_chatbot_response(self.bots_dict[phone][1], data["data"]))
                        #print(response)
                        connector.send_message(phone, response)
                        print("⚠️  Message processed but not saved to Supabase (async loop required)")
        else:
            self._process_bot_command(connector, data)
    
    async def _process_user_message(self, connector, phone: str, data: dict):
        """
        Process message from user asynchronously.
        
        Handles the complete message processing workflow including bot assignment,
        response generation, message sending, and database operations. This function
        runs in the background event loop to avoid blocking the main thread.
        
        Parameters
        ----------
        connector : EvolutionConnector
            The Evolution API connector instance for sending messages.
        phone : str
            The user's phone number (without country code prefix).
        data : dict
            The message data containing the user's message and metadata.
            
        Notes
        -----
        This function performs several async operations:
        - Bot response generation
        - Customer data management in Supabase
        - Message history storage
        """
        # Assign bot if needed
        if phone not in self.bots_dict:
            self._assign_bot_to_user(phone)
        
        # Process message if bot is active
        if phone in self.bots_dict and self.bots_dict[phone][2]:  # Bot is active
            # Update timestamp
            self.bots_dict[phone][0] = time.time()
            
            # Show typing indicator immediately
            try:
                connector.send_presence(phone, "composing", delay=5000)
            except Exception as e:
                print(f"⚠️  Could not send typing indicator to {phone}: {e}")
            
            # Get response
            print(f"📱 Responding to {phone}")
            response = await handle_messages.get_chatbot_response(self.bots_dict[phone][1], data["data"])
            #print(response)
            
            # ✅ Send response IMMEDIATELY
            connector.send_message(phone, response)
            
            # ✅ Handle customer and save messages in BACKGROUND (don't wait)
            asyncio.create_task(self._handle_customer_data(connector, phone, data, response))
    
    def _assign_bot_to_user(self, phone: str):
        """
        Assign an available bot to a user.
        
        Takes the first available bot from the pool (those with keys starting with 'A')
        and assigns it to the specified phone number. After assignment, maintains
        the minimum pool size by creating new bots if necessary.
        
        Parameters
        ----------
        phone : str
            The user's phone number to assign a bot to.
            
        Notes
        -----
        The bot is assigned directly without sending a new conversation signal.
        This allows the bot to maintain its system prompt while being ready to
        serve the new user.
        """
        extra_keys = [k for k in self.bots_dict if k.startswith('A')]
        if extra_keys:
            first_extra = extra_keys[0]
            assigned_bot = self.bots_dict.pop(first_extra)
            
            # Assign bot directly without sending new conversation signal
            self.bots_dict[phone] = assigned_bot
            print(f"🤖 Assigned bot {first_extra} to user {phone}")
            
            # Maintain pool size
            self._maintain_bot_pool()
    
    def _maintain_bot_pool(self):
        """
        Maintain minimum pool size of 3 available bots.
        
        Ensures there are always at least 3 bots available in the pool for
        immediate assignment to new users. Creates new bot instances asynchronously
        using the background event loop to avoid blocking the main thread.
        
        Notes
        -----
        New bots are created with sequential IDs (A4, A5, etc.) and are initialized
        with the same system prompt as the original pool bots. Bot creation is
        scheduled asynchronously and doesn't block the current operation.
        """
        remaining_extra_keys = [k for k in self.bots_dict if k.startswith('A')]
        if len(remaining_extra_keys) < 3:
            next_index = max([int(k[1:]) for k in self.bots_dict if k.startswith('A')], default=0) + 1
            new_key = f"A{next_index}"
            
            # Create bot asynchronously using background event loop
            if self.loop and self.loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._create_bot_async(new_key), 
                    self.loop
                )
                # Don't wait for completion, just schedule it
                print(f"🤖 Scheduling creation of new bot instance: {new_key}")
            else:
                # Fallback to sync creation
                self.bots_dict[new_key] = [time.time(), asyncio.run(initialize(self.prompt)), True]
                print(f"🤖 Created new bot instance: {new_key}")
        else:
            print(f"Pool has enough instances ({len(remaining_extra_keys)}), not creating new bot")
    
    async def _create_bot_async(self, new_key: str):
        """
        Create a new bot instance asynchronously.
        
        Initializes a new Fastchat bot instance with the system prompt and adds
        it to the bot pool. This function runs in the background event loop to
        avoid blocking other operations.
        
        Parameters
        ----------
        new_key : str
            The key identifier for the new bot (e.g., 'A4', 'A5').
            
        Notes
        -----
        If bot creation fails, an error message is logged but the operation
        continues. The bot pool may temporarily have fewer than 3 available
        bots until the next maintenance cycle.
        """
        try:
            bot_instance = await initialize(self.prompt)
            self.bots_dict[new_key] = [time.time(), bot_instance, True]
            print(f"🤖 Created new bot instance: {new_key}")
        except Exception as e:
            print(f"❌ Error creating bot {new_key}: {e}")
    
    async def _handle_customer_data(self, connector, phone: str, data: dict, response: str):
        """
        Handle customer creation and message saving asynchronously.
        
        Manages customer data in Supabase by creating new customer records when
        needed and saving both user messages and bot responses to the conversation
        history. Fetches user profile information from WhatsApp for new customers.
        
        Parameters
        ----------
        connector : EvolutionConnector
            The Evolution API connector for fetching user profile information.
        phone : str
            The user's phone number.
        data : dict
            The original message data from the user.
        response : str
            The bot's response message.
            
        Notes
        -----
        All database operations are performed asynchronously to avoid blocking
        the message processing pipeline. Errors are logged but do not prevent
        the bot from responding to the user.
        """
        try:
            customer_id = None
            
            # Create customer if doesn't exist
            existing_customers = await supabase_connector.get_customers(phone=phone)
            if len(existing_customers) == 0:
                username = await connector.fetch_username_async(phone)
                result = await supabase_connector.add_customers(phone=phone, username=username)
                if result and len(result) > 0:
                    customer_id = result[0]['id']
                    print(f"✅ Created new customer {customer_id} for {phone}")
            else:
                customer_id = existing_customers[0]['id']
                print(f"📋 Using existing customer {customer_id} for {phone}")
            
            # Save messages to Supabase if we have a customer_id
            if customer_id:
                # Save both messages concurrently for better performance
                await asyncio.gather(
                    handle_messages.save_message(data["data"], customer_id=customer_id),
                    handle_messages.save_message(
                        {"message": response}, 
                        is_bot=True, 
                        customer_id=customer_id
                    ),
                    return_exceptions=True  # Don't fail if one message fails to save
                )
                print(f"💾 Messages saved to Supabase for customer {customer_id}")
            else:
                print(f"⚠️  Could not determine customer_id for {phone}, messages not saved")
                
        except Exception as e:
            print(f"❌ Error handling customer data for {phone}: {e}")
    
    def _process_bot_command(self, connector, data: dict):
        """
        Process commands sent by the bot itself.
        
        Handles special commands sent by the system or users to control bot
        behavior, such as activating or deactivating bots for specific users.
        
        Parameters
        ----------
        connector : EvolutionConnector
            The Evolution API connector for sending response messages.
        data : dict
            The message data containing the command.
            
        Notes
        -----
        Currently supports:
        - '/start': Reactivates a bot for the user
        - Any other message: Deactivates the bot for the user
        """
        if data["data"]['key']['remoteJid'].split('@')[1] == "s.whatsapp.net":
            phone = data["data"]['key']['remoteJid'].split('@')[0]
            
            if data["data"].get("message", {}).get("conversation", "") == "/start":
                if phone in self.bots_dict:
                    self.bots_dict[phone][2] = True
                    connector.send_message(phone, "🤖 Bot reactivado. ¿En qué puedo ayudarte?")
            else:
                if phone in self.bots_dict:
                    self.bots_dict[phone][2] = False
    
    def _monitor_inactive_bots(self):
        """
        Monitor and manage inactive bots based on total count.
        
        Runs continuously in a background thread, checking every 30 seconds for
        bots that have been inactive for more than 20 minutes. Implements two
        strategies based on the total number of assigned bots:
        
        - If more than 10 bots are assigned: closes inactive bots to free resources
        - If 10 or fewer bots are assigned: converts inactive bots back to the pool
        
        Notes
        -----
        This function runs indefinitely until the application terminates. Only
        monitors bots assigned to users (not pool bots with keys starting with 'A').
        
        When converting bots back to the pool, sends a new conversation signal
        to reset their context before making them available for new users.
        """
        while True:
            current_time = time.time()
            inactive_threshold = 20*60  # 20 minutes in seconds
            #inactive_threshold = 10  # Debug mode
            
            bots_to_remove = []  # List to store keys of bots to remove
            bots_to_convert = []  # List to store bots to convert to pool
            
            # Count assigned bots (not pool bots)
            assigned_bots = [key for key in self.bots_dict.keys() if not key.startswith('A')]
            assigned_bot_count = len(assigned_bots)
            
            for key, bot_data in self.bots_dict.items():
                # Only monitor bots assigned to users (skip pool bots starting with 'A')
                if not key.startswith('A'):
                    last_interaction_time = bot_data[0]
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
                if key in self.bots_dict:
                    del self.bots_dict[key]
                    print(f"Removed bot {key} from active dictionary")
            
            # Convert inactive bots to pool bots
            for key in bots_to_convert:
                if key in self.bots_dict:
                    bot_data = self.bots_dict[key]
                    bot_instance = bot_data[1]  # The Fastchat bot instance
                    
                    # Send new conversation signal before converting to pool bot
                    try:
                        asyncio.run(self._send_new_conversation_signal(bot_instance))
                        print(f"🔄 Sent new conversation reset signal to bot {key} before converting to pool")
                    except Exception as e:
                        print(f"❌ Error sending new conversation signal to bot {key}: {e}")
                    
                    # Find next available A key
                    existing_a_keys = [k for k in self.bots_dict.keys() if k.startswith('A')]
                    if existing_a_keys:
                        next_index = max([int(k[1:]) for k in existing_a_keys]) + 1
                    else:
                        next_index = 1
                    new_key = f"A{next_index}"
                    
                    # Move bot to pool with new timestamp and active status
                    self.bots_dict[new_key] = [time.time(), bot_instance, True]
                    del self.bots_dict[key]
                    print(f"♻️  Converted bot {key} to pool bot {new_key} (ready for new customers)")
            
            # Wait 30 seconds before next check
            time.sleep(30)