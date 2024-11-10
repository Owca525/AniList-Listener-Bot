from discord.ext import commands
from datetime import datetime
from utils import *
import platform
import discord
import asyncio
import sys
import os

startTime = datetime.datetime.now()

class devcog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.is_owner()
    async def sendlog(self,ctx) -> None:
        try:
            file = discord.File(f"{log_file}", filename=str(log_file))
            await ctx.send(f"Log: {log_file}:", file=file)
        except Exception as e:
            await ctx.send(f'Error: {e}')

    @commands.command()
    @commands.is_owner()
    async def ping(self,ctx) -> None:
        ctx.send(f"Bot Latency: {round(self.client.latency * 1000)}")

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx) -> None:
        async with ctx.typing():
            embed = discord.Embed(title='# Reload All cogs #', timestamp=ctx.message.created_at, color=discord.Color.green())

            for cog in os.listdir(f'{__file__[:__file__.rfind("/")+1]}cogs'):
                if cog.endswith('.py') and not cog.startswith('_'):
                    try:
                        cog_name = cog[:-3]
                        await self.client.unload_extension(f"cogs.{cog_name}")
                        await self.client.load_extension(f"cogs.{cog_name}")
                        embed.add_field(name=f":white_check_mark: Loaded: {cog_name}", value="", inline=False)
                    except Exception as error:
                        embed.add_field(name=f':x: Not Loaded: {cog} ', value=error, inline=False)

                    await asyncio.sleep(0.5)

            await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def devinfo(self, ctx) -> None:
        time = datetime.datetime.now() - startTime

        dev_message = discord.Embed(title="Developer information",color=discord.Color.purple())
        dev_message.add_field(name='Python Version',value=sys.version,inline=False)
        dev_message.add_field(name='Discord.py version',value=discord.__version__,inline=True)
        dev_message.add_field(name='Latency bot',value=round(self.client.latency * 1000),inline=True)
        dev_message.add_field(name='Host system',value=str(platform.system()) + ' ' +  str(platform.release()),inline=True)
        dev_message.add_field(name='Time runing',value=str(time)[:-7],inline=True)

        await ctx.send(embed=dev_message)

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx) -> None:
        await ctx.send("bot shutdown")
        exit()

async def setup(client) -> None:
    await client.add_cog(devcog(client))
    logger.info("Dev is online")