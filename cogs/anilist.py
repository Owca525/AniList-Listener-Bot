from discord.ext import commands
import datetime
import discord
import ast

from utils import (
    logger, add_data, get_data,create_tables, delete_data, update_data, create_connection, search_anime
)

def name_add_text(data: dict):
    return data["name"]

async def time_converter(timestamp: int) -> str:
    date_time = datetime.datetime.fromtimestamp(timestamp)
    return date_time.strftime('%B %d, %H:%M:%S')

class anilistCommands(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client

    @discord.app_commands.command(name="anime", description="Search Anime using title or ID")
    async def anime(self, interaction: discord.Interaction, anime: str) -> None:
        try:
            await interaction.response.defer(thinking=True)
            data = await search_anime(anime)
            if data in ([], 404):
                await interaction.followup.send(f":x: This anime does not exist :x:")
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

            embed.set_thumbnail(url=data["coverImage"]["large"]).set_footer(text=f"ID: {data['id']}")

            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error {e}", exc_info=True)
            await interaction.followup.send("Sorry i can't search this anime")

class anilistListener(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client

    async def adding_data(self, interaction: discord.Interaction, channel: int, data: dict) -> None:
        await add_data(interaction.guild.id, (channel, interaction.user.name, interaction.guild.id, datetime.datetime.now(), str(data)))

    @commands.has_permissions(administrator=True)
    @discord.app_commands.command(name="addanime", description="Adding Anime")
    async def add(self, interaction: discord.Interaction, channel: discord.TextChannel, anime: str) -> None:
        try:
            await interaction.response.defer(thinking=True)
            details = await search_anime(anime)

            if details == []:
                await interaction.followup.send("I can't find this anime :pensive: ")
                return

            if details["nextAiringEpisode"] == None:
                await interaction.followup.send("Episodes for this anime are no longer released")
                return
            
            sql_data = await get_data(f"s{interaction.guild.id}")
            data = {
                "id": details["id"],
                "name": details["title"]["romaji"],
                "image": details["coverImage"]["large"],
                "nextepisode": details["nextAiringEpisode"],
                "sended": "0"
            }
            checking = list(filter(bool, list(map(lambda x: x["channel_id"] == channel.id, sql_data))))
            if checking == []:            
                await create_tables(server_id=interaction.guild.id)
                await self.adding_data(interaction, channel.id, [data])
                await interaction.followup.send(f":white_check_mark: ***{data['name']}*** successfully added to the channel <#{channel.id}>")
                logger.info(f"{data['name']}/{data['id']} successfully added to the channel {channel.id} data: {data}")
                return
            
            channel_check = list(map(lambda x: x if int(x["channel_id"]) == channel.id else None, sql_data))[0]
            for item in channel_check["animeData"]:
                if item["name"] == data["name"]:
                    await interaction.followup.send(f":x: ***{data['name']}*** Exist in the <#{channel.id}>")
                    return
            
            for item in sql_data:
                if int(item["channel_id"]) == channel.id:
                    check = list(map(lambda x: x["id"] == details["id"], item["animeData"]))
                    logger.info(check)
                    if True in check:
                        await interaction.followup.send("These Anime exist on this channel")
                        return
                    
                    data_dict = item["animeData"]
                    logger.info(data_dict, data)
                    data_dict.append(data)

                    await update_data(table=interaction.guild.id, name="animeData", key=channel.id, new=str(data_dict))
                    logger.info(f"{data['name']} {data['id']} successfully added to the channel {channel.id} data: {data}")
                    await interaction.followup.send(f":white_check_mark: ***{data['name']}*** successfully added to the channel <#{channel.id}>")

        except Exception as e:
            await interaction.followup.send(":x: Failed to add anime due to an error :x:")
            logger.error(e, exc_info=True)
            return

    @commands.has_permissions(administrator=True)
    @discord.app_commands.command(name="remove", description="Remove Selected Anime from channel")
    async def remove(self, interaction: discord.Interaction, channel: discord.TextChannel, *, anime: str) -> None:
        try:
            await interaction.response.defer(thinking=True)
            if anime.lower().replace(" ", "") == "all":
                await delete_data(interaction.guild.id, channel.id)
                await interaction.followup.send(f":white_check_mark: Removed everything from <#{channel.id}>")
                return
            
            data = list(map(lambda x: x if str(x["channel_id"]) == str(channel.id) else print(x), await get_data(f"s{interaction.guild.id}")))[0]
            if data == None:
                await interaction.followup.send(f":x: This anime dosen't exist in this channel :x:")
                return
            
            for i, item in enumerate(data["animeData"]):    
                if str(item["id"]) == str(anime) or str(item["name"]).lower() == anime.lower():
                    data = data["animeData"]
                    data.pop(i)
                    await update_data(table=interaction.guild.id, name="animeData", key=channel.id, new=str(data))
                    await interaction.followup.send(f":white_check_mark: Successfully removed {item['name']} from <#{channel.id}>")
                    logger.info(f"Successfully removed {item['name']} from {channel.id}")
                    return
            await interaction.followup.send(f":x: This anime dosen't exist in this channel :x:")
        except Exception as e:
            await interaction.followup.send(":x: Failed to remove anime due to an error :x:")
            logger.error(e, exc_info=True)
            return
    
    @commands.has_permissions(administrator=True)
    @discord.app_commands.command(name="checklist", description="Check Anime on the Channels")
    async def check(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        data = await get_data(f"s{interaction.guild.id}")
        embed_message = discord.Embed(title=f"Anime on the channels", color=discord.Color.magenta())
        for item in data:
            channel = self.client.get_channel(int(item["channel_id"]))
            embed_message.add_field(name=f'{len(item["animeData"])} Anime in the #{channel}',value='\n '.join(list(map(name_add_text, item["animeData"]))),inline=False)
        await interaction.followup.send(embed=embed_message)

async def setup(client) -> None:
    await client.add_cog(anilistListener(client))
    await client.add_cog(anilistCommands(client))
    logger.info("anilist is online")
