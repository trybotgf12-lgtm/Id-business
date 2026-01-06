# Config.py
# Fill in your details below

# Fill in your details below

API_ID = 0  # Replace with your API ID
API_HASH = "your_api_hash_here"  # Replace with your API Hash
BOT_TOKEN = "your_bot_token_here"  # Replace with your Bot Token

# Admin User IDs (list of integers)
# Replace these with your own Telegram User ID (get it from @userinfobot)
ADMINS = []

# Database File
DB_FILE = "shop.db"

# Currency Settings
CURRENCY = "₹" # User wants INR default
USD_SYMBOL = "💲"
EXCHANGE_RATE = 90 # 1 USD = 90 INR

# Payment Details
payment_config = {
    "UPI": "your_upi_id_here", # Replace with actual UPI
    "USDT": "your_usdt_address_here" # Replace with actual USDT TRC20 Address
}

# Logs
LOG_CHANNEL_ID = 0 # Using Group for all logs (Topics)
SOLD_LOG_GROUP_ID = 0

# Force Join Channels (List of Channel IDs or Usernames)
# Users must join ALL these channels to send messages in ANY group the bot is in.
# Example: FORCE_JOIN_CHANNELS = [-1001234567890, "channelusername"]
FORCE_JOIN_CHANNELS = []
