import discord
import asyncio
from discord.ext import commands
import os

#import all of the cogs
from music_cog import music_cog


#place your bot token here for the bot to read
token = ""

#command prefix for bot
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

#adds bot
async def load_extensions():
    await bot.add_cog(music_cog(bot))
 
#have bot read token           
async def main():
    async with bot:
        await load_extensions()
        await bot.start(token)

#runs bot
asyncio.run(main())

