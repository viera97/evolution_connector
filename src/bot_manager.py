"""
Bot Manager - Handles bot lifecycle, assignment, and monitoring.
"""
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
        """Initialize bot manager with system prompt."""
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
        """Start an asyncio event loop in a background thread."""
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
        """Initialize the initial pool of available bots."""
        return {
            'A1': [time.time(), asyncio.run(initialize(self.prompt)), True],
            'A2': [time.time(), asyncio.run(initialize(self.prompt)), True],
            'A3': [time.time(), asyncio.run(initialize(self.prompt)), True]
        }
    
    async def _send_new_conversation_signal(self, bot_instance):
        """Send a signal to the bot indicating a new conversation is starting."""
        new_conversation_message = "SISTEMA: Se va a iniciar una nueva conversación. Olvida el contexto anterior y prepárate para atender a un nuevo cliente."
        # Send the message but don't store it in conversation history
        async for step in bot_instance(new_conversation_message):
            pass  # Just process the message internally, don't return response
    
    def start_monitoring(self):
        """Start the bot monitoring thread."""
        if not self._monitoring_active:
            monitor_thread = threading.Thread(target=self._monitor_inactive_bots, daemon=True)
            monitor_thread.start()
            self._monitoring_active = True
            print("📊 Started bot inactivity monitor (checks every 30 seconds)")
    
    def handle_message(self, connector, data: dict):
        """Handle incoming message and manage bot assignment."""
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
                        print(response)
                        connector.send_message(phone, response)
                        print("⚠️  Message processed but not saved to Supabase (async loop required)")
        else:
            self._process_bot_command(connector, data)
    
    async def _process_user_message(self, connector, phone: str, data: dict):
        """Process message from user."""
        # Assign bot if needed
        if phone not in self.bots_dict:
            self._assign_bot_to_user(phone)
        
        # Process message if bot is active
        if phone in self.bots_dict and self.bots_dict[phone][2]:  # Bot is active
            # Update timestamp
            self.bots_dict[phone][0] = time.time()
            
            # Get response
            print(f"📱 Responding to {phone}")
            response = await handle_messages.get_chatbot_response(self.bots_dict[phone][1], data["data"])
            print(response)
            
            # Send response
            connector.send_message(phone, response)
            
            # Handle customer and save messages
            await self._handle_customer_data(connector, phone, data, response)
    
    def _assign_bot_to_user(self, phone: str):
        """Assign an available bot to a user."""
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
        """Maintain minimum pool size of 3 available bots."""
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
        """Create a new bot instance asynchronously."""
        try:
            bot_instance = await initialize(self.prompt)
            self.bots_dict[new_key] = [time.time(), bot_instance, True]
            print(f"🤖 Created new bot instance: {new_key}")
        except Exception as e:
            print(f"❌ Error creating bot {new_key}: {e}")
    
    async def _handle_customer_data(self, connector, phone: str, data: dict, response: str):
        """Handle customer creation and message saving."""
        try:
            # Create customer if doesn't exist
            existing_customers = await supabase_connector.get_customers(phone=phone)
            if len(existing_customers) == 0:
                username = connector.fetch_username(phone)
                result = await supabase_connector.add_customers(phone=phone, username=username)
                print(result)
            
            # Save messages to Supabase
            customers = await supabase_connector.get_customers(phone=phone)
            if customers and len(customers) > 0:
                customer_id = customers[0]['id']
                await handle_messages.save_message(data["data"], customer_id=customer_id)
                
                # Save bot response
                data["data"]["message"] = response
                await handle_messages.save_message(data["data"], is_bot=True, customer_id=customer_id)
                print(f"💾 Messages saved to Supabase for customer {customer_id}")
            else:
                print(f"❌ Could not find customer for phone {phone}")
                
        except Exception as e:
            print(f"❌ Error handling customer data for {phone}: {e}")
    
    def _process_bot_command(self, connector, data: dict):
        """Process commands sent by the bot itself."""
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
        """Monitor and manage inactive bots based on total count."""
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