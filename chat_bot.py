from fastchat import Fastchat
import asyncio

async def chating(query):
    chat: Fastchat = Fastchat()
    await chat.initialize()
    
    response = ""
    async for step in chat(query):
        if step.type == "response" and step.response is not None:
            response += step.response
    return response

if __name__ == "__main__":
    asyncio.run(chating("Quiero una cita"))