from fastchat import Fastchat
import asyncio

async def initialize() -> Fastchat:
    bot: Fastchat = Fastchat()
    await bot.initialize()
    print(bot)
    return bot

async def chating(bot:Fastchat, query: str) -> str :
    response = ""
    async for step in bot(query):
        if step.type == "response" and step.response is not None:
            response += step.response
    return response

if __name__ == "__main__":
    asyncio.run(chating(asyncio.run(initialize()) ,"Quiero una cita"))