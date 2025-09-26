from fastchat import Fastchat  # Imports the Fastchat class for the chatbot
import asyncio  # Imports asyncio for handling asynchronous functions

async def initialize(initial_prompt: str = "") -> Fastchat:
    """
    Initializes a Fastchat instance with an optional initial prompt.

    Parameters
    ----------
    initial_prompt : str, optional
        The initial prompt to be used by the chatbot. Defaults to "".

    Returns
    -------
    Fastchat
        An initialized Fastchat instance.
    """
    bot: Fastchat = Fastchat(extra_reponse_system_prompts=[initial_prompt])
    await bot.initialize()

    #!Debuging
    print(bot)
    return bot

async def chating(bot: Fastchat, query: str) -> str:
    """
    Sends a query to the bot and returns the complete response.

    Parameters
    ----------
    bot : Fastchat
        The Fastchat instance to which the query will be sent.
    query : str
        The query to be sent to the chatbot.

    Returns
    -------
    str
        The complete response from the chatbot.
    """
    response = ""
    async for step in bot(query):
        if step.type == "response" and step.response is not None:
            response += step.response  # Adds the response if available
    return response  # Returns the complete response

def get_system_prompt(file: str) -> str:
    """
    Reads and returns the content of a file as the system prompt.

    Parameters
    ----------
    file : str
        The path to the file containing the system prompt.

    Returns
    -------
    str
        The content of the file.
    """
    with open(file, "r") as f:
        return f.read()

if __name__ == "__main__":
    # Runs the chatbot with the default prompt and a sample query
    asyncio.run(chating(asyncio.run(initialize(get_system_prompt("Clinica_prompt.txt"))), "Quiero una cita"))