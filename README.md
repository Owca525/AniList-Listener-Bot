# Anilist Listener Bot
This is a simple bot for notifying when the next episode of an anime is released.
# Screenshot
![preview](assets/image.png)
# Requirements
- python 3.12
- discord.py 2.3.2
- httpx 0.27.0
- inflect 7.3.0
# Instalation Guide
Installation [Pythona 3.12](https://www.python.org/) <br> <br>
Cloning the repository
```bash
git clone https://github.com/Owca525/AniList-Listener-Bot.git
```
Installing the Required Libraries
```bash
python3 -m pip install -r requirements.txt
```
Running the Bot
```bash
python3 main.py
```
# Config
When you start the bot, a `config.ini` file will appear, and inside it:
- token:  Required for connecting to Discord.
- prefix: This is the prefix you use to send commands to the bot, default is `>`