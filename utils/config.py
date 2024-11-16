import configparser
import os

def make_config() -> None:
    try:
        config = configparser.ConfigParser()
        config["BOT"] = {
            "token": "",
            "prefix": ">",
        }
        with open(os.path.dirname(__file__).replace("utils", "") + "config.ini", "w") as configfile:
            config.write(configfile)
    except PermissionError:
        print("Error: Can't create config")
        exit()

def load_config() -> list:
    try:
        config = configparser.ConfigParser()
        config.read(os.path.dirname(__file__).replace("utils", "") + "config.ini")
        return [config["BOT"]["token"], config["BOT"]["prefix"]]
    except KeyError:
        print("Error: Can't read config")
        exit()

def check_config() -> list:
    if os.path.exists(os.path.dirname(__file__).replace("utils", "")+"config.ini") == False:
        make_config()
        return load_config()
    else:
        return load_config()