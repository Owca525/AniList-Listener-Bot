from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils import *
import datetime
import asyncio
import discord
import inflect
import random
import pytz
import ast
import os


__current_location__ = __file__[:__file__.rfind("/")]

__version__ = "1.0"
__anilist_database__ = __current_location__ + "/db/anilist.db"

inf = inflect.engine()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = commands.Bot(
    command_prefix=">",
    help_command=None,
    intents=discord.Intents.all()
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
    
    logger.error(error)

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

    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.activity.Game(f"My prefix is {client.command_prefix}")
    )

    await client.wait_until_ready() 
    logger.info(f'Connected To {client.user.name}')
    await anilist_background_task.start()
    await clear_cache.start()

async def send(channel, data, today_data):
    try:
        await asyncio.sleep(random.uniform(0.1, 0.9))
        number_episode = data["nextepisode"]["episode"]
        for item in today_data:
            if item["title"] == data["name"]:
                number_episode = item["anime_data"]["episode"]
        channel = client.get_channel(channel)
        dt = datetime.datetime.utcfromtimestamp(data["nextepisode"]["airingAt"])
        dt = pytz.timezone('Europe/Zagreb').localize(dt)
        embed = discord.Embed(title=f"Today releases {inf.ordinal(number_episode)} episode of {data['name']}", description=f"It will come out at {dt.strftime('%H:%M')}", color=discord.Colour.dark_blue())
        embed.set_image(url=data["image"])
        embed.set_footer(text=f"ID: {data['id']}")
        await channel.send(embed=embed)
        logger.info(f"Data anime {data['name']} ({data['id']}) sended succesfull in {channel}, data: {data}")
    except Exception as e:
        logger.error(f"Sending anime data {data['name']} ({data['id']}) Failed in channel {channel} error: {e}, data: {data}")
        return "error"

async def preaper_to_send(data: dict, server: int, channel: int, anime_today_list: list):
    if data["nextepisode"] == None:
        logger.info(f"Deleting {data['name']} ({data['id']}) from server {server}")
        return
    anime_today = [item["title"] for item in anime_today_list]
    if data["name"] in anime_today and data["sended"] != 1:
        tmp = await send(channel, data, anime_today_list)
        if tmp != "error":
            data.update({'sended': 1})
            return data
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

async def get_data_server(server, anime_today):
    try:
        tables_data = await get_data(server[1:])
        for item in tables_data:
            task = [preaper_to_send(data=items, server=item[1], channel=item[0], anime_today_list=anime_today) for items in ast.literal_eval(item[4])]
            data = await asyncio.gather(*task)
            await update_data(table=server[1:], name="animeData", key=item[0], new=str([x for x in data if x is not None]))
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

@tasks.loop(minutes=10)
async def anilist_background_task() -> None:
    try:
        logger.info("Running Task anilist_background_task")
        task = [sort_data_name(item) for item in await get_today_anime()]
        anime_today = await asyncio.gather(*task)
        task = [get_data_server(item[0], anime_today) for item in await get_all_data()]
        await asyncio.gather(*task)
    except Exception as e:
        logger.error(f"Failed task anilist_background_task: {e}")

if __name__ == "__main__":
    if TOKEN == None:
        logger.error("Token Missing")
        exit()

    client.run(TOKEN)