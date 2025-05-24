import aiohttp
import aiohttp.client_exceptions
from discord.ext import commands, tasks
import datetime
import asyncio
import discord
import inflect
import random
import pytz
import os

from utils import *
from utils.config import check_config

__current_location__ = os.path.dirname(__file__)

__version__ = "1.2"
__anilist_database__ = __current_location__ + "/db/anilist.db"

inf = inflect.engine()
config_data = check_config()

client = commands.Bot(
    command_prefix=config_data[1],
    help_command=None,
    intents=discord.Intents.default()
)

@client.event
async def on_command_error(ctx, error) -> None:
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Uknown Command please type help")
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send(":no_entry_sign: You don't have permision :no_entry_sign: ")
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing argument please type help")
        return
    
#     logger.error(error)

async def initial_database():
    if os.path.exists(__current_location__ + "/db") != True:
        os.mkdir(__current_location__ + "/db")
    
    if os.path.exists(__anilist_database__) != True:
        logger.info(f"Creating database: {__anilist_database__}")
        create_connection().close()

@client.event
async def on_ready() -> None:
    await initial_database()
    for filename in os.listdir(f'{__file__[:__file__.rfind("/")+1]}cogs'):
         if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await client.load_extension(f'cogs.{filename[:-3]}')
            except Exception as error:
                logger.critical(f'{error}')

    await change_status("online")
    await client.wait_until_ready() 
    logger.info(f'Connected To {client.user.name}')
    await anilist_background_task.start()
    await clear_cache.start()

async def send(channel, data, today_data):
    try:
        channel = client.get_channel(channel)
        await asyncio.sleep(random.uniform(0.1, 2.0))
        number_episode = data["nextepisode"]["episode"]
        for item in today_data:
            if item["title"] == data["name"]:
                number_episode = item["anime_data"]["episode"]
        Date = pytz.timezone('Europe/Zagreb').localize(datetime.datetime.utcfromtimestamp(data["nextepisode"]["airingAt"]))
        
        # Creating Embed
        embed = discord.Embed(title=f"Today releases {inf.ordinal(number_episode)} episode of {data['name']}", description=f"It will come out at {Date.strftime('%H:%M')}", color=discord.Colour.dark_blue())
        embed.set_image(url=data["image"])
        embed.set_footer(text=f"ID: {data['id']}")
        await channel.send(embed=embed)
        
        # logger.info(f"Data anime {data['name']} ({data['id']}) sended succesfull in {channel}, data: {data}")
    except Exception as e:
        logger.error(f"Sending anime data {data['name']} ({data['id']}) Failed in channel {channel} error: {e}, data: {data}")
        return "error"

async def checkElement(data: dict, server: int, channel: int, anime_today_list: list):
    if data["nextepisode"] == None:
        logger.info(f"Deleting {data['name']} ({data['id']}) from server {server}")
        return None
    anime_today = [item["title"] for item in anime_today_list]
    if data["name"] in anime_today and data["sended"] != 1:
        tmp = await send(channel, data, anime_today_list)
        if tmp != "error":
            data.update({'sended': 1})
        return data
    if data["name"] in anime_today:
        return data
    new_data = await search_anime(str(data["id"]))
    data.update({
            'nextepisode': new_data["nextAiringEpisode"], 
            'sended': 0,
        }
    )
    logger.info(f"Anime {data['name']} ({data['id']}) information Updated: {data}")
    return data

async def get_data_server(data: list, anime_today: list):
    try:
        for item in data:
            tasks = [checkElement(data=items, server=int(item["server_id"]), channel=int(item["channel_id"]), anime_today_list=anime_today) for items in item["animeData"]]
            animeData = await asyncio.gather(*tasks)
            await update_data(table=int(item["server_id"]), name="animeData", key=int(item["channel_id"]), new=str([x for x in animeData if x is not None]))
    except Exception as e:
        logger.error(f"get_data_server has error: {e}")

async def sort_data_name(data):
    return {"title": data['media']["title"]["romaji"], "anime_data": data}

@tasks.loop(hours=8)
async def clear_cache():
    try:
        cache.clear()
        logger.info("Cache AnilistApi Clear: Task done")
    except Exception as e:
        logger.error(f"Failed clear cache: {e}")

async def change_status(status: str):
    match status:
        case "online":
            await client.change_presence(
                status=discord.Status.idle,
                activity=discord.activity.Game(f"My prefix is {client.command_prefix}")
            )
        case "offline":
            await client.change_presence(
                status=discord.Status.do_not_disturb,
                activity=discord.Game(name="Api anilist is now offline"),
            )

@tasks.loop(minutes=10)
async def anilist_background_task() -> None:
    try:
        logger.info("Running Task anilist_background_task")
        today = await get_today_anime()
        if today == []:
            await change_status("offline")
            logger.info("Api anilist is not avaible")
            return
        await change_status("online")
        # TODO: FIX get_all_data to support multichannel
        anime_today = await asyncio.gather(*[sort_data_name(item) for item in today])
        task = [get_data_server(item, anime_today) for item in await get_all_data()]
        await asyncio.gather(*task)
        logger.info("The task anilist_background_task completed successfully")
    except Exception as e:
        logger.error(f"Failed task anilist_background_task: {e}")

if __name__ == "__main__":
    if config_data[0] == "":
        logger.error("Token Missing, check config.ini")
        exit()
    if config_data[1] == "":
        logger.error("Prefix missing, check config.ini")
        exit()

    try:
        client.run(config_data[0])
    except aiohttp.client_exceptions.ClientConnectionError as error:
        print(error)
