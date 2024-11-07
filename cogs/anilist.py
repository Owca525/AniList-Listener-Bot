from utils import logger, add_data, get_data,create_tables, delete_data, update_data, create_connection, search_anime
from discord.ext import commands
import datetime
import discord
import ast
import re

def name_add_text(data: dict):
    return data["name"]

async def time_converter(timestamp: int) -> str:
    date_time = datetime.datetime.fromtimestamp(timestamp)
    return date_time.strftime('%B %d, %H:%M:%S')

class anilistCommands(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client

    @commands.command(name="anime")
    async def anime(self, ctx, *, anime: str) -> None:
        data = await search_anime(anime)
        if data in ([], 404):
            await ctx.send(f"This anime does not exist")
            return

        nep = data["nextAiringEpisode"]
        if nep == None:
            nep = "Not provided"
        else:
            nep = f"Ep: {nep['episode']} at {await time_converter(nep['airingAt'])}"
        
        duration = data["duration"]
        if duration == None:
            duration = "Not provided"
        else:
            duration = f"{duration} Min"
        
        embed = discord.Embed(title=f"Anime: {data['title']['romaji']}", description="", color=discord.Colour.magenta())
        embed.add_field(name=f"Next Episode", value=nep, inline=False)
        embed.add_field(name="Status", value=data["status"].capitalize(), inline=False)
        embed.add_field(name="Format", value=data["format"].capitalize(), inline=False)
        embed.add_field(name="Episodes", value=data["episodes"], inline=False)
        embed.add_field(name="Episode Duration", value=duration, inline=False)
        embed.add_field(name="Season", value=data["season"].capitalize(), inline=False)
        embed.add_field(name="Emission", value=f"{data['startDate']['year']} {data['startDate']['month']} {data['startDate']['day']}-{data['endDate']['year']} {data['endDate']['month']} {data['endDate']['day']}", inline=False)
        embed.add_field(name="Studios", value="\n".join([item["node"]["name"] for item in data['studios']["edges"] if item["node"]["name"] != "Mainichi Broadcasting System"]), inline=False)

        embed.set_thumbnail(url=data["coverImage"]["large"]).set_footer(text=f"ID: {data['id']}")

        await ctx.send(embed=embed)

class anilistListener(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client

    async def adding_data(self, ctx, channel, data: dict) -> None:
        await add_data(ctx.guild.id, (channel, ctx.author.id, ctx.guild.id, datetime.datetime.now(), str(data)))

    @commands.command(name="addanime")
    @commands.has_permissions(administrator=True)
    async def addanime(self, ctx, channel: str, *, anime: str) -> None:
        try:
            channel = [int(channel) if channel.isdigit() else channel[2:len(channel)-1]][0]
            details = await search_anime(anime)
            if details["nextAiringEpisode"] == None:
                await ctx.send("Episodes for this anime are no longer released")
                return

            data = {
                "id": details["id"],
                "name": details["title"]["romaji"],
                "image": details["coverImage"]["large"],
                "nextepisode": details["nextAiringEpisode"],
                "sended": "0"
            }
            
            sql_data = await get_data(ctx.guild.id)

            if sql_data == []:
                await create_tables(server_id=ctx.guild.id)
                await self.adding_data(ctx, channel, [data])
                await ctx.send(f"{data['name']} successfully added to the channel: <#{channel}>")
                logger.info(f"{data['name']} {data['id']} successfully added to the channel {channel} data: {data}")
                return
            for item in sql_data:
                data_dict = ast.literal_eval(item[4])
                if int(item[0]) == int(channel) and re.findall(rf"'id':\s*{details['id']}", str(item)) != []:
                    await ctx.send("These Anime exist on this channel")
                    return

                if int(item[0]) == int(channel):
                    data_dict.append(data)
                    await update_data(table=ctx.guild.id, name="animeData", key=channel, new=str(data_dict))
                    logger.info(f"{data['name']} {data['id']} successfully added to the channel {channel} data: {data}")
                    await ctx.send(f"{data['name']} successfully added to the channel <#{channel}>")
                    return
                else:
                    await ctx.send(f"{data['name']} successfully added to the channel: <#{channel}>")
                    logger.info(f"{data['name']} {data['id']} successfully added to the channel {channel} data: {data}")
                    await self.adding_data(ctx, channel, [data])
                    return
        except Exception as e:
            logger.error(e)
            return
        
    @commands.command(name="rmanime")
    @commands.has_permissions(administrator=True)
    async def rmanime(self, ctx, channel_id, *, anime: str) -> None:
        channel = self.client.get_channel(int([int(channel_id) if channel_id.isdigit() else channel_id[2:len(channel_id)-1]][0]))
        if channel == None:
            await ctx.send("This channel does not exist")
            return
        
        if anime.lower().replace(" ", "") == "all":
            await delete_data(ctx.guild.id, channel.id)
            await ctx.send(f"Removed everything from <#{channel.id}>")
            return
        
        data = await get_data(ctx.guild.id)[0]
        data_dict = ast.literal_eval(data[4])

        for i, item in enumerate(data):
            if anime.isdigit() and item["id"] == int(anime):
                data_dict.pop(i)
                await update_data(table=ctx.guild.id, name="animeData", key=channel_id, new=str(data_dict))
                await ctx.send(f"Successfully removed {item['name']} from <#{channel_id}>")
                logger.info(f"Successfully removed {item['name']} from {channel_id}")
                return
            
            if anime.lower() == item["name"].lower():
                data_dict.pop(i)
                await update_data(table=ctx.guild.id, name="animeData", key=channel_id, new=str(data_dict))
                logger.info(f"Successfully removed {item['name']} from {channel_id}")
                return

    @commands.command(name="checkanime")
    @commands.has_permissions(administrator=True)
    async def checkanime(self, ctx) -> None:
        conn = await create_connection()
        data = conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        data = sum([await get_data(str(item[0][1:])) for item in data], [])
        embed_message = discord.Embed(title=f"Anime is waiting on the channels", color=discord.Color.magenta())
        for item in data:
            user = await self.client.fetch_user(item[2])
            channel = self.client.get_channel(int(item[0]))
            embed_message.add_field(name=f'#{channel}, {item[3][:item[3].rfind(".")]}, {user}',value='\n '.join(list(map(name_add_text, ast.literal_eval(item[4])))),inline=False)
        await ctx.send(embed=embed_message)

async def setup(client) -> None:
    await client.add_cog(anilistListener(client))
    await client.add_cog(anilistCommands(client))
    logger.info("anilist is online")