from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN
import sys

# Check config basic validation
if API_ID == 0:
    print("Please edit config.py and add your API_ID, API_HASH, and BOT_TOKEN")
    sys.exit()

# Initialize Client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
