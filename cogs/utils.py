from discord.ext import commands
import discord

from main import __version__
from utils import logger

class utils(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="help")
    async def help(self, ctx) -> None:
        prefix = self.client.command_prefix
        embed = discord.Embed(title=f"**- Help Page -**", color=discord.Color.green())
        embed.add_field(name=f"{prefix}anime `title anime/id`",value="Taking anime from anilist",inline=False)
        embed.add_field(name=f"{prefix}add `channel` `title anime/id`",value="Adding listener anime for channel (admin only)",inline=False)
        embed.add_field(name=f"{prefix}remove `channel` `title anime/id/all`",value="Deleting listener for anime (admin only)",inline=False)
        embed.add_field(name=f"{prefix}check",value="Shows data from channels they have a anime (admin only)",inline=False)
        embed.add_field(name=f"{prefix}help",value="Show help commands",inline=False)
        embed.add_field(name=f"{prefix}credits",value="Show credits",inline=False)
        embed.set_footer(text=f"Bot Version: {__version__}")
        await ctx.send(embed=embed)
    
    @commands.command(name="credits")
    async def credits(self, ctx) -> None:
        embed = discord.Embed(title=f"**- Credits -**", color=discord.Color.green())
        embed.add_field(name=f"Owca525: Programer/Creator",value="Github: https://github.com/Owca525",inline=False)
        embed.add_field(name=f"KartQ: Helping with Translate/Helper",value="",inline=False)
        embed.add_field(name=f"Giyuu: Helping with Translate",value="",inline=False)
        await ctx.send(embed=embed)

async def setup(client) -> None:
    await client.add_cog(utils(client))
    logger.info("Utils is online")