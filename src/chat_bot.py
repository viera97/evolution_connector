from fastchat import Fastchat  # Imports the Fastchat class for the chatbot
import asyncio  # Imports asyncio for handling asynchronous functions

async def initialize(initial_prompt: str = "") -> Fastchat:
    #Initializes a Fastchat instance with an optional initial prompt.
    bot: Fastchat = Fastchat(extra_reponse_system_prompts=[initial_prompt])  # Creates the bot with the initial prompt
    await bot.initialize()  # Initializes the bot (asynchronous)

    #!Debuging
    print(bot)  # Prints the bot instance for debugging
    return bot  # Returns the bot

async def chating(bot:Fastchat, query: str) -> str :
    #Sends a query to the bot and returns the complete response.
    response = ""  # Variable to accumulate the response
    async for step in bot(query):  # Iterates over the bot's response steps
        if step.type == "response" and step.response is not None:
            response += step.response  # Adds the response if available
    return response  # Returns the complete response

def get_system_prompt(file: str) -> str:
    #Reads and returns the content of a file as the system prompt.
    with open(file, "r") as f:
        return f.read()  # Returns the file content
    
if __name__ == "__main__":
    # Runs the chatbot with the default prompt and a sample query
    asyncio.run(chating(asyncio.run(initialize(get_system_prompt("Clinica_prompt.txt"))), "Quiero una cita"))