import aiohttp
import aiohttp.client_exceptions
from discord.ext import commands, tasks
import discord
import inflect
import os

import pytz

from utils import *
from utils.config import check_config

__current_location__ = os.path.dirname(__file__)

__version__ = "2.0"
__anilist_database__ = __current_location__ + "/db/anilist.db"

inf = inflect.engine()
config_data = check_config()

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(
    command_prefix=config_data[1],
    help_command=None,
    intents=intents
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
    
    logger.error(error, exc_info=True)

async def initial_database():
    if os.path.exists(__current_location__ + "/db") != True:
        os.mkdir(__current_location__ + "/db")
    
    if os.path.exists(__anilist_database__) != True:
        logger.info(f"Creating database: {__anilist_database__}")
        create_connection().close()

@client.event
async def on_ready() -> None:
    await initial_database()
    for filename in os.listdir(f'{__current_location__}/cogs'):
         if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await client.load_extension(f'cogs.{filename[:-3]}')
            except Exception as error:
                logger.critical(f'{error}')
    try:
        synced = await client.tree.sync()
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logger.error(e, exc_info=True)
    await change_status("online")

    await dataBase_Background_Task.start()
    await client.wait_until_ready() 
    logger.info(f'Connected To {client.user.name}')

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
                activity=discord.Game(name="Anilist Is Offline"),
            )
            
async def checkAnime(serverDatabse, today_anime):
    try:
        IDList = set(map(lambda x: x["id"], today_anime))
        for currentchannel in serverDatabse:
            checking = list(filter(lambda x: x["id"] in IDList, currentchannel["animeData"]))
            for anime in checking:
                if anime["sended"] == 1:
                    return
                channel = client.get_channel(int(currentchannel["channel_id"]))
                current = list(filter(lambda x: x["id"] == anime["id"], today_anime))[0]
                Date = pytz.timezone('Europe/Zagreb').localize(datetime.datetime.utcfromtimestamp(current["data"]["airing"]))
                # Creating Embed
                embed = discord.Embed(title=f"Today releases {inf.ordinal(current["data"]["episode"])} episode of {current["data"]['title']}", description=f"It will come out at {Date.strftime('%H:%M')}", color=discord.Colour.dark_blue())
                try:
                    embed.set_image(url=anime["image"])
                except Exception as e:
                    logger.error(e, anime, exc_info=True)
                embed.set_footer(text=f"ID: {current["id"]}")
                await channel.send(embed=embed)
                # Checking Anime
                animeData = list(filter(lambda x: x["id"] != current["id"], currentchannel["animeData"]))
                if anime["nextepisode"] != None:
                    current.update({ "sended": 1 })
                    animeData.append(current)
                    
                await update_data(table=int(currentchannel["server_id"]), name="animeData", key=int(currentchannel["channel_id"]), new=str(list(filter(lambda x: x is not None, animeData))))
                logger.info(f"Updated {current["id"]}")
                await dataBase_Check(today_anime)
    except Exception as e:
        logger.error(f"Error in checkAnime: {e}", exc_info=True)

@tasks.loop(hours=8)
async def clear_cache():
    try:
        cache.clear()
        logger.info("Cache AnilistApi Clear: Task done")
    except Exception as e:
        logger.error(f"Failed clear cache: {e}", exc_info=True)

async def dataBase_Check(today_anime):
    try:
        IDList = set(map(lambda x: x["id"], today_anime))
        for item in await get_all_data():
            for curchannel in item:
                not_today = list(filter(lambda x: x["id"] not in IDList, curchannel["animeData"]))
                # animeData = list(map(lambda x: x.update({'sended': 0}), not_today))
                animeData = []
                for anime in not_today:
                    tmp = anime
                    tmp.update({ "sended": 0 })
                    animeData.append(tmp)
                await update_data(table=int(curchannel["server_id"]), name="animeData", key=int(curchannel["channel_id"]), new=str([*list(filter(lambda x: x is not None, animeData)), *list(filter(lambda x: x["id"] in IDList, curchannel["animeData"]))]))
        logger.info("Checking Databse Done")
    except Exception as e:
        logger.error(f"Failed Checking Database: {e}", exc_info=True)

@tasks.loop(hours=1)
async def dataBase_Background_Task():
    try:
        logger.info("Running Task anilist_background_task")
        today_anime = await get_today_anime()
        if today_anime == []:
            await change_status("offline")
            logger.warning("API Anilist is current Offline")
            return
        await change_status("online")
        
        today_anime = list(map(lambda x: { "id": x["media"]["id"], "data": { "title": x["media"]["title"]["romaji"], "airing": x["airingAt"], "episode": x["episode"] } }, today_anime))
        await dataBase_Check(today_anime)
        for item in await get_all_data():
            await checkAnime(item, today_anime)
    except Exception as e:
        logger.error(f"Failed Task: dataBase_Background_Task {e}", exc_info=True)

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
        logger.error(error)
