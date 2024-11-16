import logging
import datetime
import os

__version__ = "1.0.2"

log_folder = os.path.dirname(__file__).replace("utils", "") + "logs"
os.makedirs(log_folder, exist_ok=True)

LOG_COLORS = {
    "DEBUG": "\033[94m",    # Blue
    "INFO": "\033[92m",     # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",    # Red
    "CRITICAL": "\033[95m", # Magenta
    "RESET": "\033[0m",     # Reset color
}

def add_color(levelname):
    level = logging.getLevelName(levelname)
    setattr(logging, levelname, level)
    setattr(logging, levelname.lower(), f"{LOG_COLORS.get(levelname, '')}{levelname}{LOG_COLORS['RESET']}")
    logging.addLevelName(level, f"{LOG_COLORS.get(levelname, '')}{levelname}{LOG_COLORS['RESET']}")

for level in LOG_COLORS.keys():
    add_color(level)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "[\033[37m%(asctime)s\033[0m-%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(log_folder, f"log_{current_time}.log")
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
