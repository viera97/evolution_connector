"""
Bot Manager - Handles bot lifecycle, assignment, and monitoring.
"""
import time
import asyncio
import threading
from typing import Dict

import handle_messages
import supabase_connector
from chat_bot import initialize

class BotManager:
    """Manages bot instances, assignment, and lifecycle."""
    
    def __init__(self, prompt: str):
        """Initialize bot manager with system prompt."""
        self.prompt = prompt
        self.bots_dict = self._initialize_bot_pool()
        self._monitoring_active = False
    
    def _initialize_bot_pool(self) -> Dict:
        """Initialize the initial pool of available bots."""
        return {
            'A1': [time.time(), asyncio.run(initialize(self.prompt)), True],
            'A2': [time.time(), asyncio.run(initialize(self.prompt)), True],
            'A3': [time.time(), asyncio.run(initialize(self.prompt)), True]
        }
    
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
                self._process_user_message(connector, phone, data)
        else:
            self._process_bot_command(connector, data)
    
    def _process_user_message(self, connector, phone: str, data: dict):
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
            response = handle_messages.get_chatbot_response(self.bots_dict[phone][1], data["data"])
            #!Debug
            print(response)
            
            # Send response
            connector.send_message(phone, response)
            
            # Handle customer and save messages
            self._handle_customer_data(connector, phone, data, response)
    
    def _assign_bot_to_user(self, phone: str):
        """Assign an available bot to a user."""
        extra_keys = [k for k in self.bots_dict if k.startswith('A')]
        if extra_keys:
            first_extra = extra_keys[0]
            assigned_bot = self.bots_dict.pop(first_extra)
            
            # Clear history before assigning
            try:
                bot_instance = assigned_bot[1]
                bot_instance.llm.chat_history.clear()
                bot_instance.llm.current_price = 0
                bot_instance.current_messages_set = None
                print(f"🧹 Cleared history for bot {first_extra} before assigning to {phone}")
            except Exception as e:
                print(f"❌ Error clearing history for bot {first_extra}: {e}")
            
            self.bots_dict[phone] = assigned_bot
            
            # Maintain pool size
            self._maintain_bot_pool()
    
    def _maintain_bot_pool(self):
        """Maintain minimum pool size of 3 available bots."""
        remaining_extra_keys = [k for k in self.bots_dict if k.startswith('A')]
        if len(remaining_extra_keys) < 3:
            next_index = max([int(k[1:]) for k in self.bots_dict if k.startswith('A')], default=0) + 1
            new_key = f"A{next_index}"
            self.bots_dict[new_key] = [time.time(), asyncio.run(initialize(self.prompt)), True]
            print(f"🤖 Created new bot instance: {new_key}")
        else:
            print(f"Pool has enough instances ({len(remaining_extra_keys)}), not creating new bot")
    
    def _handle_customer_data(self, connector, phone: str, data: dict, response: str):
        """Handle customer creation and message saving."""
        try:
            # Create customer if doesn't exist
            existing_customers = supabase_connector.get_customers(phone=phone)
            if len(existing_customers) == 0:
                username = connector.fetch_username(phone)
                print(supabase_connector.add_customers(phone=phone, username=username))
            
            # Save messages to Supabase
            customers = supabase_connector.get_customers(phone=phone)
            if customers and len(customers) > 0:
                customer_id = customers[0]['id']
                handle_messages.save_message(data["data"], customer_id=customer_id)
                
                # Save bot response
                data["data"]["message"] = response
                handle_messages.save_message(data["data"], is_bot=True, customer_id=customer_id)
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
            #inactive_threshold = 20*60  # 20 minutes in seconds
            inactive_threshold = 10  # Debug mode

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
                    
                    # Clear chat history before converting to pool bot
                    try:
                        bot_instance.llm.chat_history.clear()
                        bot_instance.llm.current_price = 0
                        bot_instance.current_messages_set = None
                        print(f"Cleared history for bot {key} before converting to pool")
                    except Exception as e:
                        print(f"Error clearing history for bot {key}: {e}")
                    
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
                    print(f"Converted bot {key} to pool bot {new_key}")
            
            # Wait 30 seconds before next check
            time.sleep(30)