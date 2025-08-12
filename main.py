# --- START OF REFACTORED FILE broad.txt ---

import json # Keep for potential future use or config parsing, though not for primary data storage
import telebot
from telebot import types
import threading
import time
import re
import html # For escaping HTML
import datetime # For timestamps
import logging
import os
from telebot.types import BotCommand

# --- Library Imports for MongoDB ---
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv # Optional: for environment variables

# --- Telegram Utilities ---
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message

# --- Templating ---
from jinja2 import Template

# --- Environment Variable Setup (Optional but Recommended) ---
load_dotenv() # Loads variables from a .env file if it exists

# --- Constants ---
API_TOKEN = os.getenv('API_TOKEN', '7901086318:AAHnAbSHciG9HtVw2qOxM4LTb6NVmOkViKg') # Replace with your actual token if not using .env

admin_id = [6265981509, 6969086416, 1411248872, 6680499027, 5026099926]
xmods = [6265981509, 6969086416, 1411248872, 6680499027, 5026099926] # Admins are also mods
owner_id = [6265981509, 6969086416]
CURRENT_BOT_VERSION = '2.1.3_mongo' # Indicate DB version and fixes
BOT_ID = 572621020 # Hexamon Bot ID for forward checks

# --- Sticker IDs ---
WELCOME_STICKER_ID = 'CAACAgIAAxkBAAMaZ87jUNqSyGQPY7QtSM0yAc6GY9MAAo48AAKfT6FL9m3qZy2bDHo2BA'
WARNING_STICKER_ID = 'CAACAgIAAxkBAAMcZ87kE8hkAUM7_5SU9ooLpnaz1wEAAvJPAAL00MFLv3iVc316FkI2BA'
SOLD_STICKER_ID ='CAACAgIAAxkBAAMeZ87kMNn-RV1LpyhTTmXHLFazSs4AAtdFAAJ1U6FLxJBd2EJWgUo2BA'
THINK_STICKER_ID = 'CAACAgIAAxkBAAMMZ87iQwTCaohIrXEPmuo737biU28AAvROAAJwfXFKVOLfiYCbwdQ2BA'
ANGRY_STICKER_ID = 'CAACAgIAAxkBAAMLZ87hgXAi9j4AAYh38qIXREOTPtxGAAJ9IwACxLexSlhnxsp8febCNgQ'
DOUBT_STICKER_ID = 'CAACAgIAAxkBAAMOZ87ibR9HFRdqhTQDTwpF41Bc5HAAAj5NAAIzm_FIffcUQZmhtn02BA'
SAD_STICKER_ID = 'CAACAgIAAxkBAAMRZ87iwVkHEXNwEjBEVNzrAAH3TMEBAAIEMgACworQSPHJLKeiJZA8NgQ'
OK_STICKER_ID = 'CAACAgIAAxkBAAMWZ87jKxy7en5eagIoE5rTgLsYebgAAthNAAJh0cFLNNXdCJvy9Gc2BA'

# --- Channel/Group IDs ---
AUCTION_GROUP_LINK = 'https://t.me/PHG_POKES' # Public link
AUCTION_CHAT_ID = -1002327346480 # Numerical ID for checking membership
TRADE_CHAT_ID = -1002468384682 # Numerical ID for checking membership
APPROVE_CHANNEL = -1002245132909 # Where admins approve/reject submissions
POST_CHANNEL = -1002327346480 # Where approved items & bids are posted
REJECT_CHANNEL = -1002245132909 # Where rejection notifications can be logged (can be same as approve)
ADMIN_BID_LOG_CHANNEL = -1002682358606 # For logging every bid attempt
ADMIN_GROUP_ID = -1002245132909 # For high-level notifications (e.g., points threshold)
LOG_GROUP_ID = -1002583646872 # ⚠️ Replace with your ACTUAL Log Group ID
# --- Profile Templates ---
TEMPLATES = {
    1:"https://files.catbox.moe/ljv11q.jpg", 2:"https://files.catbox.moe/t5bqi8.jpg",
    3:"https://files.catbox.moe/rlsg6i.jpg", 4:"https://files.catbox.moe/muyuqz.jpg",
    5:"https://files.catbox.moe/kb4v54.jpg", 6:"https://files.catbox.moe/9r1bj2.jpg",
    7:"https://files.catbox.moe/2u9jc1.jpg", 8:"https://files.catbox.moe/ll4o7u.jpg",
    9:"https://files.catbox.moe/py2p5e.jpg", 10:"https://files.catbox.moe/4h1vbf.jpg",
    11:"https://files.catbox.moe/ut393r.jpg", 12:"https://files.catbox.moe/gvcrux.jpg",
    13:"https://files.catbox.moe/vc0yws.jpg", 14:"https://files.catbox.moe/801wxs.jpg",
    15:"https://files.catbox.moe/rox79e.jpg", 16:"https://files.catbox.moe/i65b74.jpg"
}


# === Telegram Logging Handler ===
class TelegramLogHandler(logging.Handler):
    """
    A custom logging handler that sends log records to a Telegram chat.
    """
    def __init__(self, bot_instance, chat_id, level=logging.NOTSET):
        super().__init__(level=level)
        self.bot = bot_instance
        self.chat_id = chat_id
        # Optional: Set a default formatter if none is provided later
        self.formatter = logging.Formatter('%(levelname)s - %(message)s') # Simple default

    def emit(self, record):
        """
        Formats and sends the log record to Telegram.
        """
        try:
            log_entry = self.format(record) # Format the record using the handler's formatter

            # Add emoji prefix based on level for quick visual parsing
            level_emoji = {
                logging.DEBUG: "⚙️ DEBUG",
                logging.INFO: "ℹ️ INFO",
                logging.WARNING: "⚠️ WARNING",
                logging.ERROR: "❌ ERROR",
                logging.CRITICAL: "🔥 CRITICAL",
            }.get(record.levelno, f"📊 LVL-{record.levelno}")

            # Escape the main log message content for HTML safety
            safe_log_entry = html.escape(log_entry)

            # Construct the final message for Telegram
            telegram_message = f"<b>{level_emoji}</b>\n<pre>{safe_log_entry}</pre>" # Use <pre> for code-like formatting

            # Truncate if too long for Telegram
            max_len = 4096
            if len(telegram_message) > max_len:
                telegram_message = telegram_message[:max_len - 20] + "\n... (truncated)" # Keep some space

            # Send the message using the bot instance
            self.bot.send_message(
                self.chat_id,
                telegram_message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as e:
            # IMPORTANT: Log errors during Telegram sending *to the console*
            # to avoid infinite loops if the logging itself fails.
            print(f"!!! FAILED TO SEND LOG TO TELEGRAM ({self.chat_id}): {e}")
            # Optionally log the original message that failed
            try:
                original_log = self.format(record)
                print(f"--- Original Log Message: {original_log}")
            except Exception:
                print("--- Could not format original log message.")


# --- Logging Setup ---
# Keep your existing basicConfig or modify its level if desired
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Optional: Prevent double logging to console if root logger also has handlers
logger.propagate = True
# --- MongoDB Setup ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://yesvashisht2005:yash2005@cluster0.lmere3q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0") # Replace YOUR_PASSWORD or use env var

# IMPORTANT: Replace YOUR_PASSWORD with your actual MongoDB Atlas password
if "YOUR_PASSWORD" in MONGO_URI or "<FLIRTER>" in MONGO_URI: # Added common placeholder check
    logger.critical("\n" + "="*50)
    logger.critical("❌ CRITICAL WARNING: MongoDB password seems to be missing or is a placeholder!")
    logger.critical("   Please replace 'YOUR_PASSWORD' or '<FLIRTER>' in the MONGO_URI variable")
    logger.critical("   with your actual MongoDB Atlas password or set the MONGO_URI environment variable.")
    logger.critical("   For security, avoid hardcoding credentials directly in the script.")
    logger.critical("="*50 + "\n")
    # exit(1) # Uncomment to force exit if password is wrong

try:
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000) # Increased timeout slightly
    # Ping the server to verify connection early
    client.admin.command('ping')
    db = client['phg_auction_db'] # Choose your database name
    users_col = db['users']                   # Stores user info, points, ban status, version, template
    bids_col = db['bids']                     # Stores active/past bid information
    approved_items_col = db['approved_items'] # Tracks items approved for auction (replaces users_nich)
    pending_items_col = db['pending_items']   # For items awaiting admin approval
    config_col = db['config']                 # For counters, settings

    # --- Create Indexes for Performance (run once, safe to run multiple times) ---
    logger.info("Attempting to create MongoDB indexes...")
    users_col.create_index("user_id", unique=True)
    users_col.create_index("points")
    users_col.create_index("is_banned")
    bids_col.create_index("bid_id", unique=True)
    bids_col.create_index("owner_id")
    bids_col.create_index("highest_bidder_id")
    bids_col.create_index("status")
    bids_col.create_index("item_type") # Index for /elements filtering
    approved_items_col.create_index([("user_id", 1), ("category", 1)]) # Compound index
    approved_items_col.create_index("link")
    pending_items_col.create_index("user_id")
    pending_items_col.create_index("submission_time")
    pending_items_col.create_index("status")
    config_col.create_index("key", unique=True)
    logger.info("✅ MongoDB Indexes checked/created.")

    logger.info("✅ Successfully connected to MongoDB.")

except pymongo.errors.ConfigurationError as e:
    logger.error(f"❌ MongoDB Configuration Error: {e}")
    logger.error("   Check your MONGO_URI format, username, password, and database name.")
    exit(1)
except pymongo.errors.ServerSelectionTimeoutError as e:
    logger.error(f"❌ MongoDB Connection Timeout: {e}")
    logger.error("   Could not connect to the server. Check network/firewall settings and Atlas IP Whitelist.")
    exit(1)
except pymongo.errors.ConnectionFailure as e:
    logger.error(f"❌ MongoDB Connection Error: {e}")
    exit(1)
except Exception as e:
    logger.error(f"❌ An unexpected error occurred during MongoDB setup: {e}")
    exit(1)
# --- End MongoDB Setup ---

# --- Telegram Bot Initialization ---
bot = telebot.TeleBot(API_TOKEN)

# --- Add Telegram Logging Handler ---
# Define a placeholder value to check against (can be anything invalid, like 0 or None)
PLACEHOLDER_LOG_ID = None # Or 0, or a specific string if you prefer

# Check if LOG_GROUP_ID is a valid integer group ID (negative number)
if LOG_GROUP_ID and isinstance(LOG_GROUP_ID, int) and LOG_GROUP_ID < 0:
    # Check if it's NOT the specific placeholder value if you had one, otherwise just proceed
    # In this corrected version, we just assume any negative integer is intended as the ID.
    try:
        # Create the handler instance, passing the bot instance and chat ID
        telegram_handler = TelegramLogHandler(bot_instance=bot, chat_id=LOG_GROUP_ID)

        # Set the level for the handler (e.g., send INFO and above to Telegram)
        telegram_handler.setLevel(logging.INFO) # Change level as needed (INFO, WARNING, ERROR)

        # Create a formatter for the Telegram handler
        telegram_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        telegram_handler.setFormatter(telegram_formatter)

        # Add the handler to *your specific logger* instance
        logger.addHandler(telegram_handler)

        # Log a confirmation message *after* adding the handler (this should appear now)
        logger.info(f"✅ Telegram logging handler initialized. Logs (Level >= {logging.getLevelName(telegram_handler.level)}) sent to Chat ID: {LOG_GROUP_ID}")

    except Exception as log_init_error:
        # Log initialization error to console and standard logger
        print(f"!!! FAILED TO INITIALIZE TELEGRAM LOG HANDLER: {log_init_error}")
        logger.error(f"Failed to initialize Telegram log handler: {log_init_error}", exc_info=False)
else:
    # This 'else' block now correctly catches cases where LOG_GROUP_ID is missing,
    # is not a valid integer, is 0, or is positive.
    warn_msg = f"LOG_GROUP_ID ('{LOG_GROUP_ID}') is not set or is not a valid negative integer group ID. Telegram logging disabled."
    logger.warning(warn_msg)
    print(f"!!! WARNING: {warn_msg}")
# --- End Add Telegram Logging Handler ---

# --- Global State Variables ... (rest of your code continues here)



# --- Global State Variables (Transient - In-Memory) ---
user_join_status = {} # Tracks users during the initial join flow
user_states = {}      # Tracks user state for multi-step commands (like /add)
user_cache = {}       # Temporarily stores submission data during /add steps
pending_bids = {}     # Temporarily stores bids awaiting confirmation {confirmation_key: details}
user_templates = {}   # Cache user template preferences (currently fetched live)
sub_process = True    # Submission status flag
bid_ji = True         # Bidding status flag

# === Helper Functions ===

def escape(text):
    """Basic HTML escape for user-provided text."""
    if not text:
        return ""
    return html.escape(str(text))

def is_admin(user_id):
    """Checks if user_id is in the admin_id list."""
    return user_id in admin_id

def is_mod(user_id):
    """Checks if user_id is in the xmods list."""
    return user_id in xmods # Includes admins

def is_banned(user_id):
    """Checks if a user is marked as banned in the database."""
    try:
        user_doc = users_col.find_one({"user_id": str(user_id)}, {"is_banned": 1})
        return user_doc and user_doc.get("is_banned", False)
    except Exception as e:
        logger.error(f"Error checking ban status for {user_id}: {e}")
        return False # Fail safe: assume not banned if DB error

def has_started_bot(user_id):
    """Checks if a user exists in the users collection."""
    try:
        return users_col.count_documents({"user_id": str(user_id)}) > 0
    except Exception as e:
        logger.error(f"Error checking if user {user_id} started: {e}")
        return False # Fail safe

def get_user_doc(user_id):
     """Fetches the user document from the database."""
     try:
         return users_col.find_one({"user_id": str(user_id)})
     except Exception as e:
         logger.error(f"Error fetching user doc for {user_id}: {e}")
         return None

def is_user_updated(user_doc):
    """Check if the user's bot version matches the current bot version using the user document."""
    if not user_doc: return False
    return user_doc.get("version") == CURRENT_BOT_VERSION

def format_username_html(user_doc):
    """Formats username for display, preferring HTML link."""
    if not user_doc: return "N/A"
    user_id = user_doc.get('user_id')
    name = escape(user_doc.get("name", f"User {user_id}"))
    username_stored = user_doc.get("username_tg", "") # Use username_tg field

    # Try creating a mention link first
    return f'<a href="tg://user?id={user_id}">{name}</a>'

def parse_bid_amount(amount_str):
    """Parses bid strings like '1k', '500', '2.5k', '100pd', '100pds' into a float."""
    if not isinstance(amount_str, str):
        amount_str = str(amount_str) # Convert just in case

    original_str = amount_str # Keep original for logging if needed
    amount_str = amount_str.lower().replace('pd','').replace('s','').strip()
    multiplier = 1.0
    if 'k' in amount_str:
        multiplier = 1000.0
        amount_str = amount_str.replace('k', '')
    try:
        # Allow for potential float values like '2.5' before the 'k'
        return float(amount_str) * multiplier
    except ValueError:
        logger.warning(f"Could not parse bid amount: '{original_str}'")
        return 0.0 # Default to 0 if parsing fails

def get_next_bid_id():
    """Atomically increments and returns the next bid counter value."""
    try:
        counter_doc = config_col.find_one_and_update(
           {"_id": "bid_counter"},
           {"$inc": {"value": 1}},
           upsert=True, # Create if doesn't exist, starting value will be 1
           return_document=pymongo.ReturnDocument.AFTER
        )
        if counter_doc and 'value' in counter_doc:
             # Ensure the counter starts from 1 if upserted
             current_value = counter_doc['value']
             if current_value == 0: # Should not happen with $inc on upsert, but safeguard
                  counter_doc = config_col.find_one_and_update(
                     {"_id": "bid_counter"},
                     {"$set": {"value": 1}},
                     return_document=pymongo.ReturnDocument.AFTER
                  )
                  current_value = 1

             return f"P{current_value}"
        else:
             # Fallback if something went wrong
             logger.error("Failed to get/update bid counter, attempting recovery.")
             # Re-query to ensure it was created if upserted but returned None
             counter_doc = config_col.find_one({"_id": "bid_counter"})
             if counter_doc and 'value' in counter_doc:
                  return f"P{counter_doc['value']}"
             else: # Still broken, use timestamp fallback
                  config_col.update_one({"_id": "bid_counter"}, {"$set": {"value": 1}}, upsert=True)
                  logger.warning("Bid counter re-initialized to 1.")
                  return f"P1"
    except Exception as counter_err:
        logger.error(f"Error getting/updating bid counter: {counter_err}")
        # Try to fetch current value as a last resort
        fallback_doc = config_col.find_one({"_id": "bid_counter"})
        fallback_val = fallback_doc['value'] if fallback_doc else int(time.time()) % 10000
        return f"ERR{fallback_val}"

def add_points(user_id_str, points_to_add, reason=""):
    """Adds points to a user in the DB and checks the 5000 threshold."""
    if not isinstance(user_id_str, str):
         user_id_str = str(user_id_str)

    try:
        # Use find_one_and_update to get the document *after* the update
        updated_doc = users_col.find_one_and_update(
            {"user_id": user_id_str},
            {"$inc": {"points": points_to_add},
             "$setOnInsert": { # Set defaults if user is new
                 "name": f"User {user_id_str}", # Placeholder name
                 "username_tg": "",
                 "is_banned": False,
                 "version": CURRENT_BOT_VERSION,
                 "join_date": datetime.datetime.utcnow(),
                 "template_id": 1,
                 "notified_5000pts": False,
             }
            },
            upsert=True,
            return_document=pymongo.ReturnDocument.AFTER # Get the doc *after* update
        )

        if not updated_doc:
            logger.error(f"Failed to update or find user {user_id_str} after adding points.")
            return

        new_total_points = updated_doc.get("points", 0)
        logger.info(f"Awarded {points_to_add} points to {user_id_str} for {reason}. New total: {new_total_points}")

        # Check threshold using the updated document
        check_notify_5000(user_id_str, updated_doc)

    except Exception as e:
        logger.error(f"Error adding points to user {user_id_str}: {e}")

def check_notify_5000(user_id_str, user_doc):
    """Notifies admin group when user reaches 5000 points, using the provided user document."""
    if not user_doc:
        logger.warning(f"No user document provided for 5000 points check for {user_id_str}.")
        return

    points = user_doc.get("points", 0)
    notified_field = "notified_5000pts"

    # Check if points are >= 5000 and notification hasn't been sent
    if points >= 5000 and not user_doc.get(notified_field, False):
        try:
            # Format user link using the helper
            link = format_username_html(user_doc)

            # Notify admin group
            bot.send_message(ADMIN_GROUP_ID, f"🎉 {link} has reached {points} points!\nID: <code>{user_id_str}</code>", parse_mode="HTML")
            logger.info(f"Sent 5000 points notification for user {user_id_str}.")

            # Notify user (optional)
            # bot.send_message(int(user_id_str), "🎉 Congratulations! You've reached 5000 points!")

            # Mark user as notified in the database
            users_col.update_one({"user_id": user_id_str}, {"$set": {notified_field: True}})

        except Exception as e:
            logger.error(f"Error notifying about 5000 points for {user_id_str}: {e}")

def create_bid_message(bid_id, highest_bidder_mention, current_bid, base_price):
    """Creates the standard text for the bid message in the auction channel."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC') # Use UTC ideally
    # Ensure numerical values are formatted without decimals if they are whole numbers
    current_bid_display = f"{current_bid:,.0f}" if isinstance(current_bid, (int, float)) else str(current_bid)
    base_price_display = f"{base_price:,.0f}" if isinstance(base_price, (int, float)) else str(base_price)

    if highest_bidder_mention:
        # Bid placed
        text = (
            f"╔═══════ Bid Update ═══════╗\n"
            f"║ 🏷️ **Item ID:** `{bid_id}`\n"
            f"║ 💰 **Current Bid:** `{current_bid_display}`\n"
            f"║ 👤 **By:** {highest_bidder_mention}\n" # Mention is already Markdown/HTML formatted
            f"║ 🕒 {timestamp}\n"
            f"╚════════════════════════╝"
        )
    else:
        # Initial state or no bids
        text = (
            f"╔═══════ Auction Start ═══════╗\n"
            f"║ 🏷️ **Item ID:** `{bid_id}`\n"
            f"║ 💰 **Starting Bid:** `{base_price_display}`\n"
            f"║ 👤 **No bids yet!**\n"
            f"║ 🕒 {timestamp}\n"
            f"╚══════════════════════════╝"
        )
    return text

def update_bid_message_in_channel(bid_id):
    """Fetches bid data and updates the corresponding message in POST_CHANNEL."""
    try:
        bid_data = bids_col.find_one({"bid_id": bid_id})
        if not bid_data:
            logger.warning(f"Could not find bid data for {bid_id} to update message.")
            return

        if bid_data.get("status") != "active":
             logger.info(f"Bid {bid_id} is not active, skipping message update.")
             return # Don't update closed bids

        chat_id = bid_data.get("chat_id")
        message_id = bid_data.get("message_id")
        highest_bidder = bid_data.get("highest_bidder_mention") # Already formatted mention
        current_bid = bid_data.get("current_bid")
        base_price = bid_data.get("base_price") # Needed for initial message

        if not chat_id or not message_id:
            logger.error(f"Missing chat_id or message_id for bid {bid_id}.")
            return

        # Generate updated text
        updated_text = create_bid_message(bid_id, highest_bidder, current_bid, base_price)

        # Create updated markup
        markup = InlineKeyboardMarkup()
        bot_username = bot.get_me().username
        markup.row(
            InlineKeyboardButton("🔄 Refresh", callback_data=f"ref_{bid_id}"),
            InlineKeyboardButton("🔗 Place Bid", url=f"https://t.me/{bot_username}?start=bid-{bid_id}")
        )

        # Edit the message
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=updated_text,
            parse_mode="Markdown", # create_bid_message uses Markdown
            disable_web_page_preview=True,
            reply_markup=markup
        )
        logger.info(f"Updated bid message for {bid_id} in channel {chat_id}.")

    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" in str(e):
              logger.debug(f"Bid message {bid_id} was not modified.") # Less noise for this common case
         else:
              logger.error(f"Error updating bid message for {bid_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error updating bid message for {bid_id}: {e}")


def get_min_bid_increment(current_bid):
    """Determines the minimum required bid increment based on rules."""
    current_bid_numeric = parse_bid_amount(current_bid) # Ensure it's numeric

    if current_bid_numeric <= 30000:
        return 1000.0
    elif current_bid_numeric <= 60000:
        return 2000.0
    elif current_bid_numeric <= 100000:
        return 3000.0
    else:
        return 4000.0

def is_valid_forwarded_message(message):
    """Checks if the forwarded message is from the specified Hexamon bot."""
    # Check if message has 'forward_from' attribute and if its 'id' matches BOT_ID
    return message.forward_from and message.forward_from.id == BOT_ID


# === Telegram Bot Command Handlers ===

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)

    if is_banned(user_id):
        bot.reply_to(message, "You Are Banned By an Administrator")
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "" # Store @ or empty
    first_name = message.from_user.first_name
    full_name = message.from_user.full_name # Use full name for storage

    # Prepare user data for potential DB update/insert
    user_data_for_db = {
        "name": full_name,
        "username_tg": username, # Store telegram @username if available
        "first_name": first_name, # Can store first_name separately if needed
        "last_updated": datetime.datetime.utcnow()
    }
     # Format username for display link if needed
    display_username = f'<a href="tg://user?id={user_id}">{escape(full_name)}</a>'

    if message.chat.type == 'private':
        args = message.text.split()
        command_param = args[1] if len(args) > 1 else None

        # Update or insert user into DB on /start
        try:
             update_result = users_col.update_one(
                 {"user_id": user_id_str},
                 {"$set": user_data_for_db,
                  "$setOnInsert": { # Fields to set only when creating the user
                     "is_banned": False,
                     "points": 0,
                     "version": CURRENT_BOT_VERSION, # Start with current version
                     "join_date": datetime.datetime.utcnow(),
                     "template_id": 1, # Default template
                     "notified_5000pts": False,
                 }},
                 upsert=True
             )
             if update_result.upserted_id:
                 logger.info(f"New user started: {user_id_str} ({full_name})")
                 # Send initial welcome for new users
                 send_welcome_message(message.chat.id, display_username)
                 return # Don't process deep links immediately for brand new users
             else:
                  logger.info(f"User {user_id_str} started again.")
                  # If existing user, check version
                  existing_doc = get_user_doc(user_id)
                  if not is_user_updated(existing_doc):
                      update_prompt(message) # Prompt update if needed
                      return # Stop further processing until updated

        except Exception as e:
             logger.error(f"Database error during /start for user {user_id}: {e}")
             bot.reply_to(message, "Sorry, there was an error processing your request. Please try again later.")
             return

        # Handle deep linking parameters *only if user is updated*
        if command_param:
            if command_param == 'add':
                sell(message) # Pass the original message object
                return
            elif command_param == 'start':
                # Just send a simple welcome back if they used ?start=start
                 bot.send_message(message.chat.id, f"Welcome back, {display_username}!", parse_mode="html")
            elif command_param == 'profile':
                 set_profile_pic(message)
                 return
            elif command_param == 'cancel':
                handle_cancel(message)
                return
            elif command_param == 'update':
                update_prompt(message) # Trigger update flow again if they use the link
                return
            elif command_param.startswith('bid-'):
                if not bid_ji:
                     bot.reply_to(message, "Bidding is currently closed.")
                     return
                handle_bid_link(message, command_param)
                return
            # Add more deep link handlers as needed

        # If no specific deep link was handled, and user is updated, maybe show main menu or profile
        # For now, do nothing extra if no deep link matched. User is started/updated.
        if not command_param: # Default action if just /start
            bot.send_message(message.chat.id, f"Welcome back, {display_username}! Use /add to submit or /elements to browse.", parse_mode="html")


    else: # Message in group
        bot.send_sticker(message.chat.id, WARNING_STICKER_ID)
        markup=InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Start Bot', url=f'https://t.me/{bot.get_me().username}?start=start'))
        bot.reply_to(message, "<blockquote>Please use bot commands in a private message with me. Click the button above!</blockquote>", parse_mode="html", reply_markup=markup, disable_web_page_preview=True)

def send_welcome_message(chat_id, display_username):
    """Sends the initial welcome message with group join links."""
    bot.send_sticker(chat_id, WELCOME_STICKER_ID)
    markup = types.InlineKeyboardMarkup(row_width=2) # Arrange buttons nicely
    join_auction_btn = types.InlineKeyboardButton("Join Auction", url=f"https://t.me/PHG_POKES")
    join_trade_btn = types.InlineKeyboardButton("Join Trade", url=f"https://t.me/PHG_HEXA")
    joined_btn = types.InlineKeyboardButton("✅ I Have Joined ✅", callback_data="confirm_joined")

    markup.add(join_auction_btn, join_trade_btn)
    markup.add(joined_btn)

    # Use display_username which is already formatted
    caption = (
        f" 𝚆𝚎𝚕𝚌𝚘𝚖𝚎, {display_username} 𝚃𝚘 PHG 𝙰𝚞𝚌𝚝𝚒𝚘𝚗 𝙱𝚘𝚝\n\n"
         "𝚃𝚑𝚒𝚜 𝙱𝚘𝚝 𝚒𝚜 𝚞𝚜𝚎𝚍 𝚝𝚘 𝚊𝚍𝚍 𝚢𝚘𝚞𝚛 𝙿𝚘𝚔𝚎𝚖𝚘𝚗 𝚊𝚗𝚍 𝚃𝚖𝚜 𝚊𝚗𝚍 𝚂𝚑𝚒𝚗𝚢 𝚝𝚘 𝚝𝚑𝚎 𝙰𝚞𝚌𝚝𝚒𝚘𝚗\n\n"
         "𝙿𝚕𝚎𝚊𝚜𝚎 𝚓𝚘𝚒𝚗 𝚘𝚞𝚛 𝚃𝚛𝚊𝚍𝚎 𝙶𝚛𝚘𝚞𝚙 𝚊𝚗𝚍 𝙰𝚞𝚌𝚝𝚒𝚘𝚗 𝙶𝚛𝚘𝚞𝚙 𝚋𝚢 𝚌𝚕𝚒𝚌𝚔𝚒𝚗𝚐 𝚝𝚑𝚎 𝚋𝚞𝚝𝚝𝚘𝚗𝚜 𝚋𝚎𝚕𝚘𝚠, 𝚝𝚑𝚎𝚗 𝚌𝚕𝚒𝚌𝚔 '𝙸 𝙷𝚊𝚟𝚎 𝙹𝚘𝚒𝚗𝚎𝚍'."
    )

    bot.send_photo(
        chat_id,
        photo="https://graph.org/file/b15a91150a98a83bd2c78-1f710de66b88a037d1.png", # Store this ID?
        caption=caption,
        reply_markup=markup,
        parse_mode='HTML' # Use HTML as display_username is HTML
    )

@bot.callback_query_handler(func=lambda call: call.data == "confirm_joined")
def handle_joined(call):
    """Handles the 'Joined' button click, checks membership, and prompts for stats."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    try:
        # Check membership status in both groups
        auction_member = bot.get_chat_member(chat_id=AUCTION_CHAT_ID, user_id=user_id)
        trade_member = bot.get_chat_member(chat_id=TRADE_CHAT_ID, user_id=user_id)
        has_joined_auction = auction_member.status in ['member', 'administrator', 'creator']
        has_joined_trade = trade_member.status in ['member', 'administrator', 'creator']

    except telebot.apihelper.ApiTelegramException as e:
         logger.warning(f"Could not verify group membership for {user_id}: {e}. Allowing bypass.")
         # Allow proceeding if check fails (e.g., bot not admin in check groups, or user not found temporarily)
         has_joined_auction = True
         has_joined_trade = True
    except Exception as e:
        logger.error(f"Unexpected error verifying group membership for {user_id}: {e}")
        # Fail gracefully
        bot.answer_callback_query(call.id, "Error checking membership. Please try again.", show_alert=True)
        return


    if has_joined_auction and has_joined_trade:
        bot.edit_message_caption( # Edit the existing message
            chat_id=chat_id,
            message_id=call.message.message_id,
            caption="𝘛𝘩𝘢𝘯𝘬𝘴 𝘧𝘰𝘳 𝘫𝘰𝘪𝘯𝘪𝘯𝘨 𝘰𝘶𝘳 𝘨𝘳𝘰𝘶𝘱𝘴! 😊\n\n𝘕𝘰𝘸, 𝘰𝘯𝘦 𝘭𝘢𝘴𝘵 𝘴𝘵𝘦𝘱 𝘵𝘰 𝘷𝘦𝘳𝘪𝘧𝘺 𝘺𝘰𝘶𝘳 𝘢𝘤𝘤𝘰𝘶𝘯𝘵...",
            # Keep the photo, remove buttons
            reply_markup=None,
            parse_mode='html'
        )
        # Send a new message asking for stats
        bot.send_message(
            chat_id,
            "<b>Please forward your <code>/mystats</code> page from @HexamonBot here.</b>\n\n"
            "<i>This helps prevent fake bids and ensures fair auctions.</i>",
            parse_mode='html'
        )
        # Register the next step handler to wait for the forwarded message
        bot.register_next_step_handler(call.message, process_stats_forward) # Use call.message so it captures the next message in this chat
    else:
        missing_groups = []
        if not has_joined_auction: missing_groups.append("Auction Group")
        if not has_joined_trade: missing_groups.append("Trade Group")
        bot.answer_callback_query(
            call.id,
            f"Please join the {' and '.join(missing_groups)} first!",
            show_alert=True
        )


# Modified process_stats_forward function
def process_stats_forward(message):
    """Processes the forwarded /mystats message for initial verification."""
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. Check if it's a forwarded message
    if not message.forward_date:
        bot.send_message(chat_id, "❌ Please *forward* the `/mystats` message from @HexamonBot, don't send a new one or a screenshot.")
        # Ask again
        bot.register_next_step_handler(message, process_stats_forward)
        return

    # 2. Check if it's forwarded from the correct bot ID (HexamonBot)
    if not is_valid_forwarded_message(message):
        bot.reply_to(message, f"❌ This message was not forwarded from the required bot (@HexamonBot). Please forward the correct `/mystats` message.")
        # Ask again
        bot.register_next_step_handler(message, process_stats_forward)
        return

    # 3. Check if the forwarded message contains a Photo (Trainer Card)
    if not message.photo:
        bot.reply_to(message, "❌ The forwarded `/mystats` message must contain the Trainer Card photo. Please forward the correct one.")
        # Ask again
        bot.register_next_step_handler(message, process_stats_forward)
        return

    # 4. If all checks pass, send to admin for manual approval
    try:
        full_name = message.from_user.full_name
        # Get username or create link
        display_username = f'<a href="tg://user?id={user_id}">{escape(full_name)}</a>'

        markup = InlineKeyboardMarkup().row( # Buttons side-by-side
            InlineKeyboardButton('Approve', callback_data=f'verify_approve_{user_id}'),
            InlineKeyboardButton('Ban (Alt)', callback_data=f'verify_ban_{user_id}')
        )

        tex = (f'❓ User Verification Request:\n'
               f' Name: {escape(full_name)}\n'
               f' User: {display_username}\n'
               f' ID: <code>{user_id}</code>\n\n'
               f'👇 Forwarded /mystats Trainer Card below:')

        # Send info text first to the admin channel
        bot.send_message(
            APPROVE_CHANNEL,
            tex,
            reply_markup=markup,
            parse_mode='html'
        )
        # Forward the actual stats message (the photo) for admins to review
        bot.forward_message(APPROVE_CHANNEL, chat_id, message.message_id)

        bot.reply_to(message, "✅ Your stats have been sent to the administrators for verification. Please wait for approval. You'll be notified.")
        logger.info(f"Stats verification request for {user_id} sent to admins.")

    except Exception as e:
        logger.error(f"Error processing stats forward for user {user_id}: {e}")
        bot.reply_to(message, "❌ An error occurred while processing your request. Please contact an admin if this persists.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def handle_initial_verification(call):
    admin_user_id = call.from_user.id

    # Ensure the action is performed by a moderator/admin
    if not is_mod(admin_user_id):
        bot.answer_callback_query(call.id, "You are not authorized to perform this action.", show_alert=True)
        return

    try:
        parts = call.data.split('_')
        action = parts[1] # 'approve' or 'ban'
        user_id_to_verify = parts[2]
        user_id_int = int(user_id_to_verify)

        # --- Fetch user details ---
        try:
            user_info = bot.get_chat(user_id_int)
            full_name = user_info.full_name
            username_tg = f"@{user_info.username}" if user_info.username else ""
            display_username_html = f'<a href="tg://user?id={user_id_int}">{escape(full_name)}</a>'
        except Exception as e:
            logger.error(f"Could not get chat details for {user_id_int} during verification: {e}")
            # Use stored info if available, otherwise fallback
            user_doc = get_user_doc(user_id_to_verify)
            if user_doc:
                full_name = user_doc.get("name", f"User {user_id_to_verify}")
                username_tg = user_doc.get("username_tg", "")
                display_username_html = format_username_html(user_doc)
            else:
                full_name = f"User {user_id_to_verify}"
                username_tg = ""
                display_username_html = f"User <code>{user_id_to_verify}</code>"


        # --- Edit the admin message ---
        try:
            action_text = "Approved" if action == "approve" else "Banned (Alt)"
            admin_mention = f"@{call.from_user.username}" if call.from_user.username else f"Admin {admin_user_id}"
            bot.edit_message_text(
                 f"Action Taken: {action_text} for user {display_username_html} (<code>{user_id_to_verify}</code>)\nBy: {admin_mention}",
                 chat_id=call.message.chat.id,
                 message_id=call.message.message_id,
                 reply_markup=None, # Remove buttons
                 parse_mode='html'
            )
        except Exception as edit_err:
            logger.warning(f"Could not edit verification message {call.message.message_id}: {edit_err}")


        # --- Process Approve/Ban Action ---
        if action == 'approve':
            # Update user in DB: Mark as verified (implicitly by existing), ensure not banned, update info
            update_result = users_col.update_one(
                {"user_id": user_id_to_verify},
                {"$set": {
                    "is_banned": False, # Ensure not banned
                    "name": full_name,
                    "username_tg": username_tg,
                    "version": CURRENT_BOT_VERSION, # Mark as updated on approval
                    "last_verified_by": str(admin_user_id),
                    "last_verified_time": datetime.datetime.utcnow()
                    },
                 "$setOnInsert": {
                     "points": 0,
                     "join_date": datetime.datetime.utcnow(),
                     "template_id": 1,
                     "notified_5000pts": False
                 }
                },
                upsert=True # Create user doc if they somehow skipped /start
            )
            bot.send_message(user_id_int, "✅ Congratulations! Your account has been verified by an administrator. You can now fully use the bot (e.g., `/add` to submit items).")
            bot.answer_callback_query(call.id, f"User {user_id_to_verify} approved.")
            logger.info(f"User {user_id_to_verify} approved by {admin_user_id}")

        elif action == 'ban':
            # Ban the user
            update_result = users_col.update_one(
                {"user_id": user_id_to_verify},
                {"$set": {
                    "is_banned": True,
                    "ban_reason": "Alt Account Verification Failed",
                    "name": full_name,  # Store name even when banning
                    "username_tg": username_tg
                    }},
                upsert=True
            )
            bot.send_message(user_id_int, "❌ Your account verification failed. You have been banned. Reason: Suspected Alt Account.")
            bot.answer_callback_query(call.id, f"User {user_id_to_verify} banned.")
            logger.info(f"User {user_id_to_verify} banned (alt) by {admin_user_id}")

    except IndexError:
        bot.answer_callback_query(call.id, "Error: Invalid callback data.", show_alert=True)
        logger.error(f"Invalid verify callback data: {call.data}")
    except ValueError:
         bot.answer_callback_query(call.id, "Error: Invalid User ID in callback.", show_alert=True)
         logger.error(f"Invalid user ID in verify callback data: {call.data}")
    except Exception as e:
        logger.error(f"Error handling initial verification callback ({call.data}): {e}")
        bot.answer_callback_query(call.id, "An error occurred.", show_alert=True)


# === User List Commands ===

def get_page_html(page, per_page):
    """Fetches and formats a page of users from the database."""
    start = (page - 1) * per_page
    try:
        # Fetch users directly from DB with pagination, sorting by join_date or name
        user_cursor = users_col.find(
            {}, # No filter for now, could add filters (e.g., filter banned)
            {"user_id": 1, "name": 1, "username_tg": 1} # Project necessary fields
        ).sort("join_date", pymongo.DESCENDING).skip(start).limit(per_page) # Sort by newest first

        user_lines = []
        for i, user_doc in enumerate(user_cursor, start=start + 1):
            # Format display using helper
            display_link = format_username_html(user_doc) # This gives the HTML link/username
            user_lines.append(f"{i}. {display_link}") # Add numbering

        if not user_lines:
             return "No users found for this page."

        return "\n".join(user_lines)

    except Exception as e:
        logger.error(f"Error fetching user page {page}: {e}")
        return "Error retrieving user list."


@bot.message_handler(commands=['users'])
def users_list(message):
    """Displays a paginated list of registered users."""
    chat_id = message.chat.id
    if not is_mod(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        total_users = users_col.count_documents({}) # Get total count from DB
    except Exception as e:
        logger.error(f"Error counting users: {e}")
        bot.reply_to(message, "Error retrieving user count.")
        return

    if not total_users:
        bot.send_message(chat_id, "⚠️ No users found.")
        return

    per_page = 20 # Users per page
    total_pages = (total_users + per_page - 1) // per_page

    markup = telebot.types.InlineKeyboardMarkup()
    if total_pages > 1:
        markup.add(telebot.types.InlineKeyboardButton("Next ➡️", callback_data=f"userspage:2"))
    markup.add(telebot.types.InlineKeyboardButton("❌ Close", callback_data=f"close_{message.from_user.id}"))

    page_content = get_page_html(1, per_page)
    header = f"<b>📄 Users List (Page 1/{total_pages}) Total: {total_users}</b>\n\n"
    bot.send_message(
        chat_id,
        header + page_content,
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('userspage:'))
def users_pagination(call):
    """Handles pagination for the user list."""
    try:
        page = int(call.data.split(':')[1])
        total_users = users_col.count_documents({})
        per_page = 20
        total_pages = (total_users + per_page - 1) // per_page

        markup = telebot.types.InlineKeyboardMarkup()
        button_row = []
        if page > 1:
            button_row.append(telebot.types.InlineKeyboardButton("⬅️ Prev", callback_data=f"userspage:{page-1}"))
        if page < total_pages:
            button_row.append(telebot.types.InlineKeyboardButton("Next ➡️", callback_data=f"userspage:{page+1}"))
        if button_row:
            markup.row(*button_row)
        markup.add(telebot.types.InlineKeyboardButton("❌ Close", callback_data=f"close_{call.from_user.id}"))


        page_content = get_page_html(page, per_page)
        header = f"<b>📄 Users List (Page {page}/{total_pages}) Total: {total_users}</b>\n\n"

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=header + page_content,
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error handling users pagination (page {call.data}): {e}")
        bot.answer_callback_query(call.id, "Error updating list.")


# === Admin Commands (Ban, Unban, Msg, Verify) ===

@bot.message_handler(commands=['msg'])
def handle_msg(message):
    """Admin command to send a message to a specific user ID."""
    if is_banned(message.from_user.id):
        bot.reply_to(message, "You are banned and cannot use commands.")
        return
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "Invalid syntax. Use: /msg <user_id> <message>")
            return
        target_user_id = int(parts[1])
        user_message = parts[2]
    except (ValueError, IndexError):
        bot.reply_to(message, "Invalid syntax. Use: /msg <user_id> <message>")
        return

    try:
        # You can add a prefix to the message to indicate it's from an admin
        bot.send_message(target_user_id, f"ℹ️ **Message from Admin:**\n\n{user_message}", parse_mode="Markdown")
        bot.reply_to(message, f"Message successfully sent to user `{target_user_id}`.", parse_mode="Markdown")
        logger.info(f"Admin {message.from_user.id} sent message to {target_user_id}")
    except telebot.apihelper.ApiTelegramException as e:
        bot.reply_to(message, f"Failed to send message to user `{target_user_id}`. Error: {e}", parse_mode="Markdown")
        logger.error(f"Failed sending message from {message.from_user.id} to {target_user_id}: {e}")
    except Exception as e:
        bot.reply_to(message, f"An unexpected error occurred sending to `{target_user_id}`.", parse_mode="Markdown")
        logger.error(f"Unexpected error sending message from {message.from_user.id} to {target_user_id}: {e}")


def get_user_id_from_arg(arg):
    """Attempts to resolve a user ID from an argument (ID or @username)."""
    try:
        # Try direct ID conversion
        return str(int(arg))
    except ValueError:
        # Assume username if not an integer
        try:
            clean_username = arg.lstrip('@')
            # MongoDB lookup (more reliable than get_chat if user hasn't interacted recently)
            user_doc = users_col.find_one({"username_tg": f"@{clean_username}"}, {"user_id": 1})
            if user_doc:
                return user_doc['user_id']
            else:
                # Fallback to bot.get_chat if needed, but less reliable for non-public usernames
                # user = bot.get_chat(f"@{clean_username}")
                # if user: return str(user.id)
                logger.warning(f"Could not find user in DB by username: @{clean_username}")
                return None
        except Exception as e:
            logger.error(f"Error resolving username {arg}: {e}")
            return None

@bot.message_handler(commands=['unban'])
def unban_user(message):
    """Unbans a user by reply or user ID/username."""
    if not is_mod(message.from_user.id):
        bot.reply_to(message, "You don't have rights to use this command.")
        return

    args = message.text.split()[1:]
    user_id_to_unban = None

    if message.reply_to_message:
        user_id_to_unban = str(message.reply_to_message.from_user.id)
    elif args:
        user_id_to_unban = get_user_id_from_arg(args[0])
        if not user_id_to_unban:
             bot.reply_to(message, f"Could not find user '{args[0]}'. Please use their User ID.")
             return
    else:
        bot.reply_to(message, "Please reply to a user or provide their User ID / @Username.")
        return

    try:
        # Attempt to unban in DB
        result = users_col.update_one(
            {"user_id": user_id_to_unban},
            {"$set": {"is_banned": False, "ban_reason": None}} # Also clear reason
        )

        if result.matched_count == 0:
             bot.reply_to(message, "🚫 User not found in the database.")
        elif result.modified_count == 1:
            bot.reply_to(message, f"✅ User `{user_id_to_unban}` has been unbanned.", parse_mode="Markdown")
            logger.info(f"User {user_id_to_unban} unbanned by {message.from_user.id}")
            # Notify the user
            try:
                bot.send_message(int(user_id_to_unban), "✅ You have been unbanned by an administrator.")
            except Exception as e:
                logger.warning(f"Could not notify user {user_id_to_unban} about unban: {e}")
        else: # Matched but not modified
             # Check if they were actually banned before saying "already unbanned"
             user_doc = get_user_doc(user_id_to_unban)
             if user_doc and not user_doc.get("is_banned", False):
                bot.reply_to(message, "🚫 This user is not currently banned.")
             else: # Should not happen if modified_count is 0 but matched_count > 0
                 logger.warning(f"Unban command matched user {user_id_to_unban} but modified_count was 0.")
                 bot.reply_to(message, "An inconsistency occurred. Please check the user's status.")

    except Exception as e:
        logger.error(f"Error during unban process for {user_id_to_unban}: {e}")
        bot.reply_to(message, "An error occurred while unbanning the user.")


@bot.message_handler(commands=['ban'])
def ban_user(message):
    """Bans a user by reply or user ID/username."""
    if not is_mod(message.from_user.id):
        bot.reply_to(message, "You dont have rights to use this.")
        return

    args = message.text.split(maxsplit=2) # Allow reason: /ban <id/reply> [reason]
    target_arg = args[1] if len(args) > 1 else None
    reason = args[2] if len(args) > 2 else "No reason provided."
    user_id_to_ban = None

    if message.reply_to_message:
        user_id_to_ban = str(message.reply_to_message.from_user.id)
        # If a reason was also provided as arg[1] when replying, use it.
        if target_arg and not target_arg.isdigit() and not target_arg.startswith('@'):
            reason = target_arg # Treat the first arg after /ban as reason if replying
        elif len(args) > 2 : # If there's a third arg when replying, it's the reason
            reason = args[2]
    elif target_arg:
        user_id_to_ban = get_user_id_from_arg(target_arg)
        if not user_id_to_ban:
             bot.reply_to(message, f"Could not find user '{target_arg}'. Please use their User ID.")
             return
    else:
        bot.reply_to(message, "Please reply to a user or provide their User ID / @Username.")
        return

    # Prevent banning admins/mods/self
    if int(user_id_to_ban) in xmods or int(user_id_to_ban) == message.from_user.id:
        bot.reply_to(message, "⚠️ Cannot ban moderators or yourself.")
        return

    try:
        # Ban the user (upsert ensures the user exists in the DB)
        result = users_col.update_one(
            {"user_id": user_id_to_ban},
            {"$set": {"is_banned": True, "ban_reason": reason}},
            upsert=True # Create the user doc if it doesn't exist, marking them as banned
        )

        # Check status after update
        current_status = users_col.find_one({"user_id": user_id_to_ban}, {"is_banned": 1})

        if current_status and current_status.get("is_banned"):
             if result.modified_count > 0 or result.upserted_id:
                 bot.reply_to(message, f"🚫 User `{user_id_to_ban}` has been banned. Reason: {escape(reason)}", parse_mode="Markdown")
                 logger.info(f"User {user_id_to_ban} banned by {message.from_user.id}. Reason: {reason}")
                 # Notify the user
                 try:
                     bot.send_message(int(user_id_to_ban), f"🚫 You have been banned by an administrator. Reason: {escape(reason)}")
                 except Exception as e:
                     logger.warning(f"Could not notify user {user_id_to_ban} about ban: {e}")
             else: # Matched but not modified (already banned)
                  bot.reply_to(message, f"⚠️ User `{user_id_to_ban}` is already banned.", parse_mode="Markdown")
        else:
             # Should not happen if update worked, indicates a potential issue
             logger.error(f"Ban command executed for {user_id_to_ban} but DB status is not banned.")
             bot.reply_to(message, "An inconsistency occurred during the ban process. Please check manually.")


    except Exception as e:
        logger.error(f"Error during ban process for {user_id_to_ban}: {e}")
        bot.reply_to(message, "An error occurred while banning the user.")


@bot.message_handler(commands=['phg'])
def handle_phg(message):
    """Admin command to manually verify a user (adds/updates them in DB)."""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 You are not authorized to verify users.")
        return

    args = message.text.split()[1:]
    user_id_to_verify = None
    user_info = None

    if message.reply_to_message:
        user_id_to_verify = str(message.reply_to_message.from_user.id)
        user_info = message.reply_to_message.from_user
    elif args:
        user_id_to_verify = get_user_id_from_arg(args[0])
        if user_id_to_verify:
            try:
                # Try fetching fresh info first
                user_info = bot.get_chat(int(user_id_to_verify))
            except Exception as e:
                logger.warning(f"Could not fetch chat details for {user_id_to_verify} during /phg: {e}")
                # Fallback to DB info if get_chat fails
                user_doc = get_user_doc(user_id_to_verify)
                if user_doc:
                    # Reconstruct a user-like object for consistency (optional)
                    user_info = types.User(id=int(user_id_to_verify),
                                           first_name=user_doc.get("first_name", "Unknown"),
                                           last_name=user_doc.get("last_name", ""),
                                           username=user_doc.get("username_tg", "").lstrip('@'),
                                           is_bot=False) # Assuming it's not a bot
                    user_info.full_name = user_doc.get("name", f"User {user_id_to_verify}")
                else:
                    bot.reply_to(message, f"Could not fetch details for User ID {user_id_to_verify}. User not found in DB or Telegram.")
                    return
        else:
            bot.reply_to(message, f"❌ Invalid user identifier '{args[0]}'. Use User ID or @Username.")
            return
    else:
        bot.reply_to(message, "❌ Please reply to a user or provide their User ID / @Username to verify.")
        return

    if not user_info:
         bot.reply_to(message, "❌ Could not retrieve user information.")
         return

    user_id_str = str(user_info.id)
    full_name = user_info.full_name
    username_tg = f"@{user_info.username}" if user_info.username else ""
    display_username_html = f'<a href="tg://user?id={user_id_str}">{escape(full_name)}</a>'

    # Check if already banned
    if is_banned(user_id_str):
        bot.reply_to(message, f"🚫 {display_username_html} is banned and cannot be verified.", parse_mode='html')
        return

    try:
        # Add/Update the user in the database, ensuring they are not banned and have current version
        update_result = users_col.update_one(
            {"user_id": user_id_str},
            {"$set": {
                "name": full_name,
                "username_tg": username_tg,
                "first_name": user_info.first_name, # Store first name too
                "is_banned": False, # Explicitly unban if they were somehow banned before verification
                "version": CURRENT_BOT_VERSION,
                "last_verified_by": str(message.from_user.id),
                "last_verified_time": datetime.datetime.utcnow(),
                "last_updated": datetime.datetime.utcnow(),
                },
             "$setOnInsert": {
                 "points": 0,
                 "join_date": datetime.datetime.utcnow(),
                 "template_id": 1,
                 "notified_5000pts": False
                 }
            },
            upsert=True
        )

        if update_result.matched_count > 0 and not update_result.modified_count and not update_result.upserted_id:
             # Check if version was already current
             user_doc = get_user_doc(user_id_str)
             if user_doc and user_doc.get("version") == CURRENT_BOT_VERSION:
                 bot.reply_to(message, f"✅ {display_username_html} is already verified and up-to-date!", parse_mode='html')
             else: # Version might have been updated even if no other fields changed
                  bot.reply_to(message, f"✅ {display_username_html} has been updated/verified!", parse_mode='html')
                  logger.info(f"User {user_id_str} updated/manually verified by {message.from_user.id}")
                  # Notify user on version update via verify
                  try:
                      bot.send_message(int(user_id_str), "✅ Your bot access has been updated/verified by an admin!")
                  except Exception as e:
                      logger.warning(f"Could not notify user {user_id_str} about manual verification: {e}")

        else: # Upserted or modified
             bot.reply_to(message, f"✅ {display_username_html} has been successfully verified!", parse_mode='html')
             logger.info(f"User {user_id_str} manually verified by {message.from_user.id}")
             # Notify the user
             try:
                 bot.send_message(int(user_id_str), "✅ You have been verified by an admin and can now use the bot features!")
             except Exception as e:
                 logger.warning(f"Could not notify user {user_id_str} about manual verification: {e}")

    except Exception as e:
        logger.error(f"Error verifying user {user_id_str} with /phg: {e}")
        bot.reply_to(message, "An error occurred during verification.")


# === General Commands ===

@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    """Cancels any ongoing multi-step operation for the user."""
    if is_banned(message.from_user.id):
        return

    if message.chat.type == 'private':
        user_id = message.from_user.id
        state_cancelled = False
        cache_cleared = False
        if user_id in user_states:
            del user_states[user_id]
            state_cancelled = True
            logger.info(f"State cancelled for user {user_id}")
        if user_id in user_cache:
             del user_cache[user_id] # Clear any cached submission data
             cache_cleared = True
             logger.info(f"Submission cache cleared for user {user_id} on cancel.")

        if state_cancelled or cache_cleared:
             bot.send_message(message.chat.id, "✅ Any active command process has been cancelled.", parse_mode="html")
        else:
             bot.send_message(message.chat.id, "✅ No active process found to cancel.")
    else:
        bot.send_sticker(message.chat.id, WARNING_STICKER_ID)
        markup=InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Cancel Process', url=f'https://t.me/{bot.get_me().username}?start=cancel'))
        bot.reply_to(message, "<blockquote>Please use /cancel in our private chat to stop any ongoing process.</blockquote>", parse_mode="html", reply_markup=markup, disable_web_page_preview=True)

# --- Global variable for pending broadcasts ---
pending_broadcasts = {} # {confirmation_key: {'type': 'text'/'forward', 'content': ..., 'fwd_chat_id': ..., 'target_count': ...}}

@bot.message_handler(commands=["abroad"])
def broadcast_request(message: Message):
    """Admin command to INITIATE a broadcast request."""
    if not is_mod(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    admin_user_id = message.from_user.id
    broadcast_type = None
    content = None
    fwd_chat_id = None

    # --- Determine message to send ---
    if message.reply_to_message:
        content = message.reply_to_message.message_id
        fwd_chat_id = message.chat.id
        broadcast_type = "forward"
    elif len(message.text.split()) > 1:
        content = message.text.replace("/abroad ", "", 1)
        broadcast_type = "text"
    else:
        bot.reply_to(message, "❌ Please reply to a message or type a message after /abroad to broadcast.")
        return

    # --- Get target user count ---
    try:
        target_count = users_col.count_documents({"is_banned": {"$ne": True}})
        if target_count == 0:
            bot.reply_to(message, "⚠️ No target users found (excluding banned). Cannot broadcast.")
            return
    except Exception as e:
        logger.error(f"Error counting users for broadcast: {e}")
        bot.reply_to(message, "Error fetching user count for broadcast.")
        return

    # --- Store pending broadcast and ask for confirmation ---
    confirmation_key = f"bc_{admin_user_id}_{int(time.time())}"
    pending_broadcasts[confirmation_key] = {
        'type': broadcast_type,
        'content': content,
        'fwd_chat_id': fwd_chat_id,
        'target_count': target_count,
        'requester_id': admin_user_id
    }

    # Schedule cleanup for this pending request (e.g., after 10 minutes)
    schedule_pending_broadcast_cleanup(confirmation_key, 600)

    markup = InlineKeyboardMarkup().row(
        InlineKeyboardButton(f"✅ Yes, Send to {target_count}", callback_data=f"confirm_bc_{confirmation_key}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_bc_{confirmation_key}")
    )

    broadcast_preview = ""
    if broadcast_type == "text":
        preview_text = content[:100] + "..." if len(content) > 100 else content
        broadcast_preview = f"Message:\n```\n{escape(preview_text)}\n```"
    elif broadcast_type == "forward":
        broadcast_preview = f"Forwarded message (ID: {content} from this chat)"

    bot.reply_to(
        message,
        f"❓ **Confirm Broadcast**\n\n"
        f"Type: {broadcast_type.capitalize()}\n"
        f"Target Users: {target_count} (non-banned)\n\n"
        f"{broadcast_preview}\n\n"
        f"Are you sure you want to send this broadcast?",
        parse_mode="Markdown",
        reply_markup=markup
    )

def schedule_pending_broadcast_cleanup(key, timeout):
    """Removes pending broadcast data after a timeout."""
    def cleanup():
        if key in pending_broadcasts:
            logger.info(f"Cleaning up expired pending broadcast: {key}")
            del pending_broadcasts[key]
    threading.Timer(timeout, cleanup).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith(("confirm_bc_", "cancel_bc_")))
def handle_broadcast_confirmation(call):
    """Handles the confirmation for the broadcast."""
    admin_user_id = call.from_user.id
    message = call.message # The confirmation message bot sent

    try:
        action_part, confirmation_key = call.data.split("_", 2)[1:] # confirm_bc_KEY -> bc_KEY
        action = call.data.split("_")[0] # confirm or cancel
    except ValueError:
        logger.error(f"Invalid broadcast confirmation callback data: {call.data}")
        bot.answer_callback_query(call.id, "Error: Invalid data")
        return

    # Retrieve pending broadcast details
    pending_data = pending_broadcasts.get(confirmation_key)

    if not pending_data:
        bot.answer_callback_query(call.id, "⚠️ This broadcast request has expired or is invalid.", show_alert=True)
        try: bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id, reply_markup=None)
        except Exception: pass
        return

    # Ensure the admin clicking is the one who requested
    if admin_user_id != pending_data['requester_id']:
        bot.answer_callback_query(call.id, "This confirmation is not for you.")
        return

    # --- Handle Cancellation ---
    if action == "cancel":
        del pending_broadcasts[confirmation_key] # Remove pending request
        bot.answer_callback_query(call.id, "❌ Broadcast cancelled.")
        try:
            bot.edit_message_text("❌ Broadcast cancelled by user.", chat_id=message.chat.id, message_id=message.message_id, reply_markup=None)
        except Exception: pass
        return

    # --- Handle Confirmation ---
    if action == "confirm":
        # Remove from pending now that we are processing it
        if confirmation_key in pending_broadcasts:
            del pending_broadcasts[confirmation_key]
        else: # Should not happen if initial check passed, but safeguard
            bot.answer_callback_query(call.id, "⚠️ Broadcast request already processed or expired.", show_alert=True)
            return

        # Edit confirmation message to show "Starting..."
        try:
            bot.edit_message_text(f"⏳ Initializing broadcast to {pending_data['target_count']} users...",
                                  chat_id=message.chat.id, message_id=message.message_id, reply_markup=None)
        except Exception as edit_err:
            logger.warning(f"Could not edit broadcast confirmation message: {edit_err}")

        # --- Start the actual broadcast ---
        # Retrieve necessary info from pending_data
        broadcast_type = pending_data['type']
        content = pending_data['content']
        fwd_chat_id = pending_data['fwd_chat_id']
        total_users = pending_data['target_count']
        status_message = message # Use the edited confirmation message for status updates

        # Call a separate function to handle the actual sending loop
        execute_broadcast(admin_user_id, broadcast_type, content, fwd_chat_id, total_users, status_message)
        bot.answer_callback_query(call.id, "Broadcast initiated!")


def execute_broadcast(admin_user_id, broadcast_type, content, fwd_chat_id, total_users, status_message):
    """Performs the actual user iteration and sending for broadcast."""
    sent_count = 0
    blocked_users = [] # Store {'id': user_id_str, 'doc': user_doc}
    failed_users = [] # Store {'id': user_id_str, 'doc': user_doc, 'error': str(e)}
    start_time = time.time()

    logger.info(f"Executing broadcast initiated by {admin_user_id}. Type: {broadcast_type}, Target: {total_users}")

    try:
        user_cursor = users_col.find({"is_banned": {"$ne": True}}, {"user_id": 1, "name": 1, "username_tg": 1}) # Fetch needed fields

        update_interval = max(5, total_users // 20)
        last_update_time = start_time
        i = 0

        for user_doc in user_cursor:
            user_id_str = user_doc.get('user_id')
            if not user_id_str:
                logger.error("Found user document without user_id during broadcast execution.")
                failed_users.append({'id': 'UNKNOWN', 'doc': user_doc, 'error': 'Missing user_id'})
                continue

            try:
                user_id_int = int(user_id_str)
                if broadcast_type == "forward":
                    bot.forward_message(user_id_int, fwd_chat_id, content)
                elif broadcast_type == "text":
                    # Send without "Broadcast:" prefix now, as admin confirmed
                    bot.send_message(user_id_int, content, parse_mode="Markdown") # Or HTML if needed

                sent_count += 1
                time.sleep(0.05) # 50ms delay

            except telebot.apihelper.ApiTelegramException as e:
                error_str = f"{e.error_code} - {e.description}"
                logger.warning(f"Broadcast API Exception for user {user_id_str}: {error_str}")
                if e.error_code == 403: # Blocked/Deactivated
                    blocked_users.append({'id': user_id_str, 'doc': user_doc})
                else: # Other API errors (Chat not found, etc.)
                    failed_users.append({'id': user_id_str, 'doc': user_doc, 'error': error_str})
            except Exception as e:
                 error_str = str(e)
                 logger.warning(f"General broadcast error for user {user_id_str}: {error_str}")
                 failed_users.append({'id': user_id_str, 'doc': user_doc, 'error': error_str})

            i += 1
            # Update status periodically
            current_time = time.time()
            if (i % update_interval == 0) or (current_time - last_update_time > 15) or (i == total_users):
                 elapsed_time = current_time - start_time
                 blocked_count = len(blocked_users)
                 failed_count = len(failed_users)
                 try:
                     bot.edit_message_text(
                          f"⏳ Broadcasting... {i}/{total_users} done.\n"
                          f"✅ Sent: {sent_count}, 🚫 Blocked: {blocked_count}, ❌ Failed: {failed_count}\n"
                          f"⏱️ Elapsed: {elapsed_time:.1f}s",
                          chat_id=status_message.chat.id,
                          message_id=status_message.message_id
                     )
                     last_update_time = current_time
                 except Exception as edit_e:
                     if "message is not modified" not in str(edit_e):
                         logger.warning(f"Could not edit broadcast status during loop: {edit_e}")

        # --- Final Status Update ---
        end_time = time.time()
        duration = end_time - start_time
        blocked_count = len(blocked_users)
        failed_count = len(failed_users)

        final_status_lines = [
            f"🏁 Broadcast Complete!\n",
            f"✅ Sent: {sent_count}",
            f"🚫 Blocked/Inactive: {blocked_count}",
            f"❌ Other Failed: {failed_count}",
            f"👥 Total Targeted: {total_users}",
            f"⏱️ Duration: {duration:.2f} seconds"
        ]

        # Add lists of failed users (limited)
        if blocked_users:
            final_status_lines.append("\n🚫 **Blocked/Inactive Users (Max 15):**")
            for idx, u_info in enumerate(blocked_users[:15]):
                user_link = format_username_html(u_info['doc']) if u_info['doc'] else f"<code>{u_info['id']}</code>"
                final_status_lines.append(f" - {user_link}")
            if len(blocked_users) > 15:
                final_status_lines.append(" - ... (and more)")

        if failed_users:
            final_status_lines.append("\n❌ **Other Failed Users (Max 15):**")
            for idx, u_info in enumerate(failed_users[:15]):
                user_link = format_username_html(u_info['doc']) if u_info['doc'] else f"<code>{u_info['id']}</code>"
                error_msg = escape(u_info.get('error', 'Unknown Error'))
                final_status_lines.append(f" - {user_link} ({error_msg})")
            if len(failed_users) > 15:
                 final_status_lines.append(" - ... (and more)")


        final_status_text = "\n".join(final_status_lines)

        # Truncate if too long
        if len(final_status_text) > 4096:
             final_status_text = final_status_text[:4092] + "\n..."

        try:
            bot.edit_message_text(
                final_status_text,
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Failed to update final broadcast status message: {e}")
            # Send as new message if edit fails
            bot.send_message(status_message.chat.id, final_status_text, parse_mode='HTML', disable_web_page_preview=True)

        logger.info(f"Broadcast finished. Sent: {sent_count}, Blocked: {blocked_count}, Failed: {failed_count}, Duration: {duration:.2f}s")

    except Exception as loop_err:
         logger.error(f"Error during broadcast loop execution: {loop_err}", exc_info=True)
         try:
             bot.edit_message_text(f"❌ An error occurred during the broadcast process: {escape(str(loop_err))}",
                                   chat_id=status_message.chat.id, message_id=status_message.message_id)
         except Exception:
             bot.send_message(status_message.chat.id, "❌ An error occurred during the broadcast process.")


# === Item Submission Handlers (/add) ===

@bot.message_handler(commands=['add'])
def sell(message):
    """Initiates the item submission process."""
    user_id = message.from_user.id
    user_id_str = str(user_id)

    # --- Pre-checks ---
    if is_banned(user_id):
        bot.reply_to(message, "You are banned and cannot submit items.")
        return

    user_doc = get_user_doc(user_id)
    if not user_doc:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Start Bot', url=f'https://t.me/{bot.get_me().username}?start=start'))
        bot.reply_to(message, "You need to /start the bot first before submitting.", reply_markup=markup)
        return

    if not is_user_updated(user_doc):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update'))
        bot.reply_to(message, '<blockquote><b>Please update the bot first using the button below.</b></blockquote>', parse_mode='html', reply_markup=markup, disable_web_page_preview=True)
        return

    if not sub_process: # Check global submission flag
        bot.reply_to(message, 'Submissions are currently disabled by the administrators.')
        return

    if message.chat.type != 'private':
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Submit Item', url=f'https://t.me/{bot.get_me().username}?start=add'))
        bot.reply_to(message, '<blockquote><b>Please use the /add command in my private chat.</b></blockquote>', parse_mode='html', reply_markup=markup, disable_web_page_preview=True)
        return

    # Cancel any previous state/cache
    if user_id in user_states: del user_states[user_id]
    if user_id in user_cache: del user_cache[user_id]

    # --- Ask User Confirmation ---
    markup = types.InlineKeyboardMarkup().row( # Buttons side-by-side
        types.InlineKeyboardButton('✅ Yes', callback_data='sell_yes'),
        types.InlineKeyboardButton('❌ No', callback_data='sell_no')
    )
    display_username = format_username_html(user_doc) # Get formatted username/link
    bot.send_sticker(message.chat.id, THINK_STICKER_ID)
    bot.send_message(user_id, f"Hello {display_username}!\n\nWould you like to submit an item (Pokémon, TM, Team) for auction?", parse_mode="html", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['sell_yes', 'sell_no'])
def handle_sell_confirmation(call):
    """Handles the Yes/No confirmation for starting submission."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == 'sell_yes':
        markup = types.InlineKeyboardMarkup(row_width=2) # Max 2 buttons per row
        markup.add(
            types.InlineKeyboardButton('𝟲𝗹⚡️ Legendary', callback_data='sell_category_legendary'),
            types.InlineKeyboardButton('𝟬𝗹 🌪 Non-Legendary', callback_data='sell_category_non_legendary')
        )
        markup.add(
             types.InlineKeyboardButton('𝗦𝗵𝗶𝗻𝘆 ✨', callback_data='sell_category_shiny'),
             types.InlineKeyboardButton('𝗧𝗺𝘀 💿', callback_data='sell_category_tms')
        )
        markup.add(types.InlineKeyboardButton('𝗧𝗲𝗮𝗺𝘀 🎯', callback_data='sell_category_teams'))
        markup.add(types.InlineKeyboardButton('Cancel Submission', callback_data='cancel_submission')) # Add cancel

        try:
             bot.edit_message_text('Okay! What category does your item fall into?', chat_id, message_id, reply_markup=markup)
             bot.answer_callback_query(call.id)
        except Exception as e:
             logger.warning(f"Error editing sell confirmation message: {e}")
             # If edit fails, send new message
             bot.send_message(chat_id, 'Okay! What category does your item fall into?', reply_markup=markup)

    elif call.data == 'sell_no':
        try:
            bot.edit_message_text('Alright! Feel free to use /add again when you\'re ready. Have a great day! ✨', chat_id, message_id, reply_markup=None)
        except Exception: pass # Ignore if message deleted
        bot.answer_callback_query(call.id)
@bot.callback_query_handler(func=lambda call: call.data.startswith('sell_category_'))
def handle_category_selection(call):
    """Handles the item category selection with explicit checks."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    raw_data = call.data # Keep the raw data

    # --- Force Clear State (Just in Case) ---
    if user_id in user_states:
        logger.warning(f"Clearing existing state for {user_id} before category selection: {user_states[user_id]}")
        del user_states[user_id]
    if user_id in user_cache:
        logger.warning(f"Clearing existing cache for {user_id} before category selection: {user_cache[user_id]}")
        del user_cache[user_id]
    # --- End Force Clear ---

    logger.info(f"--- Category Selection Triggered ---")
    logger.info(f"User {user_id} clicked button.")
    logger.info(f"Received raw call.data: '{raw_data}'")

    # --- Explicit Category Check ---
    category = None # Initialize category
    if raw_data == 'sell_category_legendary':
        category = 'legendary'
    elif raw_data == 'sell_category_non_legendary':
        category = 'non_legendary'
    elif raw_data == 'sell_category_shiny':
        category = 'shiny'
    elif raw_data == 'sell_category_tms':
        category = 'tms'
    elif raw_data == 'sell_category_teams':
        category = 'teams'
    else:
        logger.error(f"Received UNKNOWN category callback data: '{raw_data}'")
        bot.answer_callback_query(call.id, "Error: Unknown category selected.", show_alert=True)
        try: # Try to edit the message to show error
            bot.edit_message_text("Error: Unknown category selection.", chat_id, message_id, reply_markup=None)
        except Exception: pass
        return # Stop processing if category is unknown

    logger.info(f"Explicitly determined category variable: '{category}'") # Log the explicitly determined category

    # --- Proceed with Determined Category ---
    user_states[user_id] = {'step': 'ask_details', 'category': category}
    user_cache[user_id] = {'category': category}

    category_display = category.replace('_', ' ').title()
    logger.info(f"Formatted category_display for message: '{category_display}'")

    next_instruction = ""

    if category == 'tms':
        logger.info(f"Category is 'tms', registering TM handler.")
        next_instruction = "Okay, please **forward** the TM details message directly from @HexamonBot."
        bot.register_next_step_handler(call.message, process_tm_details_forward)
    elif category == 'teams':
        logger.info(f"Category is 'teams', registering Team handler.")
        next_instruction = "First, enter a short name for your Training Team (e.g., `SPA Team`, `Speed Team`, `Mixed Team`)."
        bot.register_next_step_handler(call.message, process_team_name)
    else: # Pokémon categories
        logger.info(f"Category is Pokémon ('{category}'), registering Pokémon handler.")
        next_instruction = "Please enter the exact name of the Pokémon you want to submit."
        bot.register_next_step_handler(call.message, process_pokemon_name)

    final_message_text = f"Selected: **{category_display}**\n\n{next_instruction}"
    logger.info(f"Attempting to edit message {message_id} with text: {repr(final_message_text)}")

    try:
        bot.edit_message_text(
            final_message_text,
            chat_id, message_id, reply_markup=None, parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Error editing category selection message: {e}")
        # Send new message if edit fails
        bot.send_message(chat_id, final_message_text, parse_mode="Markdown")

    bot.answer_callback_query(call.id)

# --- Submission Step Handlers ---

# Handles Pokémon Name Input
def process_pokemon_name(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_details':
        # User might have cancelled or state is wrong
        return # Ignore message

    pokemon_name = message.text.strip()
    if not pokemon_name:
        bot.reply_to(message, "⚠️ Please enter a valid Pokémon name.")
        bot.register_next_step_handler(message, process_pokemon_name) # Ask again
        return

    user_cache[user_id]['pokemon_name'] = pokemon_name
    user_states[user_id]['step'] = 'ask_nature_page' # Set next specific step

    bot.send_message(
        chat_id,
        f"Got it: **{escape(pokemon_name)}**\n\n"
        f"➡️ **Next:** Please **forward** the Pokémon's **Nature page** from @HexamonBot.\n\n"
        f"*(Ensure it's the correct Pokémon!)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_nature_pic_forward)

# Handles Nature Page Forward (for Pokémon)
def process_nature_pic_forward(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_nature_page': return

    # Validations
    if not message.forward_date:
        bot.reply_to(message, "❌ Please *forward* the message...");
        bot.register_next_step_handler(message, process_nature_pic_forward); return
    if not is_valid_forwarded_message(message):
        bot.reply_to(message, f"❌ Please forward the message directly from @HexamonBot.");
        bot.register_next_step_handler(message, process_nature_pic_forward); return
    if not message.photo or not message.caption:
        bot.reply_to(message, "❌ The forwarded message must be a photo with a caption (the Nature page).")
        bot.register_next_step_handler(message, process_nature_pic_forward); return

    # --- Extract Nature ---
    nature = "Unknown" # Default value
    nature_match = re.search(r"Nature:\s*(\w+)", message.caption) # Regex to find "Nature: Word"
    if nature_match:
        nature = nature_match.group(1).capitalize() # Get the word after "Nature:" and capitalize it
        logger.info(f"Extracted nature: {nature} for user {user_id}")
    else:
        # If regex fails, still check if "Nature:" is present for basic validation
        if "Nature:" not in message.caption:
             bot.reply_to(message, "❌ This doesn't look like the Pokémon's Nature page. Please forward the correct one.")
             bot.register_next_step_handler(message, process_nature_pic_forward)
             return
        else:
             logger.warning(f"Could not extract specific nature word for user {user_id}, but 'Nature:' was present.")

    # Store data in user_cache
    user_cache[user_id]['nature_pic_id'] = message.photo[-1].file_id
    user_cache[user_id]['nature_caption'] = message.caption
    user_cache[user_id]['nature'] = nature # Store extracted nature

    user_states[user_id]['step'] = 'ask_iv_ev_page'

    bot.send_message(
        chat_id,
        f"✅ Nature page received (Nature: {nature}).\n\n" # Show extracted nature
        f"➡️ **Next:** Please **forward** the **SAME Pokémon's IVs/EVs page** from @HexamonBot.\n\n"
        f"*(It must be the same forwarded message showing IVs/EVs instead of Nature)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_iv_ev_pic_forward)

# Handles IV/EV Page Forward (for Pokémon)
def process_iv_ev_pic_forward(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Add this line for debugging:
    logger.info(f"--- IV/EV Check --- User: {user_id}")
    if message.caption:
        # Use repr() to show hidden characters like extra spaces or newlines
        logger.info(f"Caption received (repr): {repr(message.caption)}")
        # FIX: Check for substrings individually
        has_iv = "IV" in message.caption
        has_ev = "EV" in message.caption
        has_total = "Total" in message.caption
        logger.info(f"Checking IV: {has_iv}, EV: {has_ev}, Total: {has_total}")
    else:
        logger.warning("No caption found in message for IV/EV check.")
    # --- End of Debugging lines ---

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_iv_ev_page':
        logger.warning(f"Ignoring IV/EV step for user {user_id} due to incorrect state: {user_states.get(user_id)}")
        return # Ignore if state is wrong

    # Validations
    if not message.forward_date:
        bot.reply_to(message, "❌ Please *forward* the message.")
        bot.register_next_step_handler(message, process_iv_ev_pic_forward)
        return
    if not is_valid_forwarded_message(message):
        bot.reply_to(message, f"❌ Please forward the message directly from @HexamonBot.")
        bot.register_next_step_handler(message, process_iv_ev_pic_forward)
        return
    if not message.photo or not message.caption:
        bot.reply_to(message, "❌ The forwarded message must be a photo with a caption (the IVs/EVs page).")
        bot.register_next_step_handler(message, process_iv_ev_pic_forward)
        return

    # FIX: Check for key components individually instead of exact string match
    if not ("IV" in message.caption and "EV" in message.caption and "Total" in message.caption):
        logger.warning(f"IV/EV component check failed for caption: {repr(message.caption)}") # Log on failure
        bot.reply_to(message, "❌ This doesn't look like the Pokémon's IVs/EVs page (missing IV, EV, or Total). Please forward the correct one.")
        bot.register_next_step_handler(message, process_iv_ev_pic_forward)
        return
    # Check if it's the SAME image as the nature page
    cached_nature_pic_id = user_cache.get(user_id, {}).get('nature_pic_id')
    if not cached_nature_pic_id or cached_nature_pic_id != message.photo[-1].file_id:
        logger.warning(f"IV/EV image mismatch for user {user_id}. Nature: {cached_nature_pic_id}, IV/EV: {message.photo[-1].file_id}")
        bot.reply_to(message, "❌ This image doesn't match the Nature page you sent earlier. Please forward the correct IVs/EVs page (from the same original message).")
        bot.register_next_step_handler(message, process_iv_ev_pic_forward)
        return

    # Store data
    user_cache[user_id]['iv_ev_caption'] = message.caption
    user_states[user_id]['step'] = 'ask_moveset_page'

    bot.send_message(
        chat_id,
        f"✅ IVs/EVs page received.\n\n"
        f"➡️ **Next:** Please **forward** the **SAME Pokémon's Moveset page** from @HexamonBot.\n\n"
        f"*(It must be the same forwarded message showing the Moveset)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_moveset_pic_forward)

# Handles Moveset Page Forward (for Pokémon)
def process_moveset_pic_forward(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_moveset_page': return

    # Validations
    if not message.forward_date:
        bot.reply_to(message, "❌ Please *forward* the message.")
        bot.register_next_step_handler(message, process_moveset_pic_forward)
        return
    if not is_valid_forwarded_message(message):
        bot.reply_to(message, f"❌ Please forward the message directly from @HexamonBot.")
        bot.register_next_step_handler(message, process_moveset_pic_forward)
        return
    if not message.photo or not message.caption:
        bot.reply_to(message, "❌ The forwarded message must be a photo with a caption (the Moveset page).")
        bot.register_next_step_handler(message, process_moveset_pic_forward)
        return
    # Basic check for Moveset format - look for Power and Accuracy
    if "Power:" not in message.caption or "Accuracy:" not in message.caption:
        bot.reply_to(message, "❌ This doesn't look like the Pokémon's Moveset page. Please forward the correct one.")
        bot.register_next_step_handler(message, process_moveset_pic_forward)
        return
    # Check if it's the SAME image
    if user_cache[user_id].get('nature_pic_id') != message.photo[-1].file_id:
        bot.reply_to(message, "❌ This image doesn't match the previous pages. Please forward the correct Moveset page (from the same original message).")
        bot.register_next_step_handler(message, process_moveset_pic_forward)
        return

    # Store data
    user_cache[user_id]['moveset_caption'] = message.caption
    user_states[user_id]['step'] = 'ask_boosted_stat'

    bot.send_message(
        chat_id,
        f"✅ Moveset page received.\n\n"
        f"➡️ **Next:** Is any stat on this Pokémon **boosted** (e.g., using Orbs)?\n\n"
        f"*(Type the boosted stat like `Attack`, `SPA`, `Speed`, etc., or type `No` if none)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_boosted_stat)


# Handles Boosted Stat Input (for Pokémon)
def process_boosted_stat(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_boosted_stat': return

    boosted_stat = message.text.strip()
    user_cache[user_id]['boosted_stat'] = boosted_stat # Store 'No' or the stat name
    user_states[user_id]['step'] = 'ask_base_price'

    bot.send_message(
        chat_id,
        f"✅ Boosted Stat info recorded: `{escape(boosted_stat)}`\n\n"
        f"➡️ **Final Step:** Please enter the **Starting Bid (Base Price)** for this Pokémon.\n\n"
        f"*(Examples: `1k`, `5000`, `2.5k`, `100pd`, `50pds`)*\n"
        f"*(Minimum base price is usually 500 or 1k, check rules if unsure)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_pokemon_base_price)


# Handles Base Price Input (for Pokémon)
def process_pokemon_base_price(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_base_price': return

    base_price_str = message.text.strip()
    # Basic validation (numeric part exists)
    if not re.search(r'\d', base_price_str):
        bot.reply_to(message, "⚠️ Invalid base price format. Please include a number (e.g., `1k`, `5000`, `100pd`).")
        bot.register_next_step_handler(message, process_pokemon_base_price)
        return

    numeric_base = parse_bid_amount(base_price_str)
    if numeric_base < 500: # Example minimum
         bot.reply_to(message, "⚠️ Minimum base price is 500. Please enter a higher value.")
         bot.register_next_step_handler(message, process_pokemon_base_price)
         return

    user_cache[user_id]['base_price_str'] = base_price_str
    # --- Show Preview and Ask for Final Confirmation ---
    show_submission_preview(user_id, 'pokemon')


# Handles Team Name Input
def process_team_name(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id].get('category') != 'teams' or user_states[user_id]['step'] != 'ask_details': return

    team_name = message.text.strip()
    if not team_name:
        bot.reply_to(message, "⚠️ Please enter a name for your team.")
        bot.register_next_step_handler(message, process_team_name)
        return

    user_cache[user_id]['team_name'] = team_name
    user_states[user_id]['step'] = 'ask_team_details' # Next step

    bot.send_message(
        chat_id,
        f"Got team name: **{escape(team_name)}**\n\n"
        f"➡️ **Next:** Please **forward** the team details message from @HexamonBot.\n\n"
        f"*(Make sure it includes the levels, like `1. Pokémon - Lv. 100`)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_team_details_forward)


# Handles Team Details Forward
def process_team_details_forward(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_team_details': return

    # Validations
    if not message.forward_date:
        bot.reply_to(message, "❌ Please *forward* the team details message.")
        bot.register_next_step_handler(message, process_team_details_forward)
        return
    if not is_valid_forwarded_message(message):
        bot.reply_to(message, f"❌ Please forward the message directly from @HexamonBot.")
        bot.register_next_step_handler(message, process_team_details_forward)
        return
    if not message.text:
        bot.reply_to(message, "❌ The forwarded message must contain the team text details.")
        bot.register_next_step_handler(message, process_team_details_forward)
        return
    # Check for level format (basic)
    if not re.search(r"-\s+Lv\.\s+\d+", message.text):
         bot.reply_to(message, "❌ The team details format seems incorrect or is missing levels (`- Lv. XX`). Please forward the correct message.")
         bot.register_next_step_handler(message, process_team_details_forward)
         return

    # Store data
    user_cache[user_id]['team_details_text'] = message.text
    user_states[user_id]['step'] = 'ask_team_base_price'

    bot.send_message(
        chat_id,
        f"✅ Team details received.\n\n"
        f"➡️ **Final Step:** Please enter the **Starting Bid (Base Price)** for this Team.\n\n"
        f"*(Examples: `1k`, `5000`, `2.5k`, `100pd`, `50pds`)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_team_base_price)

# Handles Base Price Input (for Teams)
def process_team_base_price(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_team_base_price': return

    base_price_str = message.text.strip()
    if not re.search(r'\d', base_price_str):
        bot.reply_to(message, "⚠️ Invalid base price format. Please include a number (e.g., `1k`, `5000`, `100pd`).")
        bot.register_next_step_handler(message, process_team_base_price)
        return

    # Optional: Minimum price check for teams
    numeric_base = parse_bid_amount(base_price_str)
    if numeric_base < 1000: # Example minimum
         bot.reply_to(message, "⚠️ Minimum base price for teams is 1000. Please enter a higher value.")
         bot.register_next_step_handler(message, process_team_base_price)
         return

    user_cache[user_id]['base_price_str'] = base_price_str
    # --- Show Preview and Ask for Final Confirmation ---
    show_submission_preview(user_id, 'team')


# Handles TM Details Forward
def process_tm_details_forward(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check state - should be ask_details with category tms
    if user_id not in user_states or user_states[user_id].get('step') != 'ask_details' or user_states[user_id].get('category') != 'tms':
        logger.warning(f"Ignoring TM details forward for user {user_id} due to incorrect state: {user_states.get(user_id)}")
        return

    # Validations
    if not message.forward_date:
        bot.reply_to(message, "❌ Please *forward* the TM details message.")
        bot.register_next_step_handler(message, process_tm_details_forward)
        return
    if not is_valid_forwarded_message(message):
        bot.reply_to(message, f"❌ Please forward the message directly from @HexamonBot.")
        bot.register_next_step_handler(message, process_tm_details_forward)
        return
    if not message.text:
        bot.reply_to(message, "❌ The forwarded message must contain the TM text details.")
        bot.register_next_step_handler(message, process_tm_details_forward)
        return

    # FIX: Adjusted Regex to match Hexamon format better
    # Extracts "TM<digits>" and the text immediately following it until common delimiters
    # Example: "TM30 💿 Shadow Ball [Ghost ⦿ ] Power: 80..." -> tm_code='TM30', tm_name='💿 Shadow Ball'
    tm_match = re.match(r"(TM\d+)\s+(.*?)(?:\s+\[|\s+Power:|\s+Accuracy:|\s+You can sell)", message.text, re.IGNORECASE | re.DOTALL)

    if not tm_match:
         logger.warning(f"TM regex failed for user {user_id}. Text: {repr(message.text)}")
         bot.reply_to(message, "❌ This doesn't look like a standard TM details format from HexamonBot. Please forward the correct message.")
         bot.register_next_step_handler(message, process_tm_details_forward)
         return

    # Store data
    tm_code = tm_match.group(1).upper().strip()
    tm_name = tm_match.group(2).strip()
    # Clean up potential emoji/extra chars if needed, basic cleaning:
    tm_name = re.sub(r'^\W+\s*', '', tm_name) # Remove leading non-word characters and space

    user_cache[user_id]['tm_details_text'] = message.text # Store original forwarded text
    user_cache[user_id]['pokemon_name'] = tm_code # Use TM code as the 'name' for consistency
    user_cache[user_id]['tm_move_name'] = tm_name # Store extracted name

    user_states[user_id]['step'] = 'ask_tm_base_price' # Set next step

    bot.send_message(
        chat_id,
        f"✅ TM details received: **{escape(tm_code)} - {escape(tm_name)}**\n\n"
        f"➡️ **Final Step:** Please enter the **Starting Bid (Base Price)** for this TM.\n\n"
        f"*(Examples: `1k`, `500`, `2.5k`, `100pd`, `50pds`)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_tm_base_price)


# Handles Base Price Input (for TMs)
def process_tm_base_price(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id not in user_states or user_states[user_id]['step'] != 'ask_tm_base_price': return

    base_price_str = message.text.strip()
    if not re.search(r'\d', base_price_str):
        bot.reply_to(message, "⚠️ Invalid base price format. Please include a number (e.g., `1k`, `500`, `100pd`).")
        bot.register_next_step_handler(message, process_tm_base_price)
        return

    # Optional: Minimum price check for TMs
    numeric_base = parse_bid_amount(base_price_str)
    if numeric_base < 100: # Example minimum
         bot.reply_to(message, "⚠️ Minimum base price for TMs is 100. Please enter a higher value.")
         bot.register_next_step_handler(message, process_tm_base_price)
         return

    user_cache[user_id]['base_price_str'] = base_price_str
    # --- Show Preview and Ask for Final Confirmation ---
    show_submission_preview(user_id, 'tm')


# --- Preview and Final Submit ---

def show_submission_preview(user_id, item_kind):
    """Generates and sends a preview message before final submission."""
    if user_id not in user_cache:
        logger.warning(f"User cache not found for {user_id} during preview.")
        bot.send_message(user_id, "An error occurred building the preview. Please try /add again.")
        return

    cache = user_cache[user_id]
    category = cache.get('category', 'unknown')
    base_price_str = cache.get('base_price_str', 'N/A')
    photo_id = cache.get('nature_pic_id') # For Pokémon
    preview_caption = "📝 **Submission Preview**\n\n"

    # Build caption based on item type
    user_doc = get_user_doc(user_id)
    display_username = format_username_html(user_doc) if user_doc else f"User {user_id}"

    if item_kind == 'pokemon':
        poke_name = cache.get('pokemon_name', 'N/A')
        nature_cap = cache.get('nature_caption', 'N/A')
        iv_ev_cap = cache.get('iv_ev_caption', 'N/A')
        moveset_cap = cache.get('moveset_caption', 'N/A')
        boosted = cache.get('boosted_stat', 'N/A')

        # Create a cleaner, more structured caption for approval/post
        # Using HTML for better formatting control
        preview_caption = (
            f"<b>Category:</b> #{category.capitalize()}\n"
            f"<b>Submitted by:</b> {display_username}\n"
            # f"<b>User ID:</b> <code>{user_id}</code>\n" # Maybe hide ID from public post?
            f"<b>Pokémon:</b> {escape(poke_name)}\n"
            f"<b>Nature:</b> {escape(cache.get('nature', 'Unknown'))}\n" # Show extracted nature
            f"<b>Boosted:</b> {escape(boosted)}\n"
            f"<b>Base Price:</b> {escape(base_price_str)}\n\n"
            f"--- Details ---\n"
            f"<i>Nature Page:</i>\n{escape(nature_cap)}\n\n"
            f"<i>IVs/EVs Page:</i>\n<code>{escape(iv_ev_cap)}</code>\n\n" # Use code for fixed-width
            f"<i>Moveset Page:</i>\n{escape(moveset_cap)}\n"
        )
        cache['final_caption'] = preview_caption # Store the HTML formatted caption

    elif item_kind == 'team':
        team_name = cache.get('team_name', 'N/A')
        details = cache.get('team_details_text', 'N/A')
        preview_caption = (
            f"<b>Category:</b> #Teams\n" # Hardcode category tag
            f"<b>Submitted by:</b> {display_username}\n"
            # f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Team Name:</b> {escape(team_name)}\n"
            f"<b>Base Price:</b> {escape(base_price_str)}\n\n"
            f"--- Team Details ---\n<pre>{escape(details)}</pre>\n" # Use <pre> for better formatting
        )
        cache['final_caption'] = preview_caption
        photo_id = None # Teams don't have a photo

    elif item_kind == 'tm':
        tm_code = cache.get('pokemon_name', 'N/A') # Reused field for TM code
        tm_move = cache.get('tm_move_name', 'N/A')
        details = cache.get('tm_details_text', 'N/A') # Original forwarded text
        preview_caption = (
            f"<b>Category:</b> #Tms\n" # Hardcode category tag
            f"<b>Submitted by:</b> {display_username}\n"
            # f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Item:</b> {escape(tm_code)} - {escape(tm_move)}\n"
            f"<b>Base Price:</b> {escape(base_price_str)}\n\n"
            f"--- TM Details (Forwarded) ---\n<pre>{escape(details)}</pre>\n"
        )
        cache['final_caption'] = preview_caption
        photo_id = None # TMs don't have a photo

    else:
        bot.send_message(user_id, "Error: Unknown item type for preview.")
        return

    # --- Send Preview Message with Buttons ---
    markup = InlineKeyboardMarkup().row(
        InlineKeyboardButton("✅ Submit", callback_data="final_submit"),
        InlineKeyboardButton("❌ Discard", callback_data="cancel_submission")
    )

    try:
        # Use the newly formatted HTML caption
        final_preview_caption = cache['final_caption'] + "\n\n<i>Please review carefully. Click Submit to send for approval, or Discard to cancel.</i>"

        if photo_id:
            # Ensure caption length is within Telegram limits (1024 chars)
            if len(final_preview_caption) > 1024:
                 final_preview_caption = final_preview_caption[:1020] + "\n..."
            bot.send_photo(user_id, photo_id, caption=final_preview_caption, parse_mode='HTML', reply_markup=markup)
        else:
             # Ensure caption length is within limits (4096 chars)
            if len(final_preview_caption) > 4096:
                 final_preview_caption = final_preview_caption[:4092] + "\n..."
            bot.send_message(user_id, final_preview_caption, parse_mode='HTML', reply_markup=markup)
        # Clear state, wait for final submit/cancel callback
        if user_id in user_states: del user_states[user_id]
    except Exception as e:
        logger.error(f"Error sending submission preview to {user_id}: {e}")
        bot.send_message(user_id, "An error occurred displaying the preview. Your submission might be incomplete. Please try /add again or use /cancel.")


@bot.callback_query_handler(func=lambda call: call.data in ["final_submit", "cancel_submission"])
def handle_final_submission_action(call):
    """Handles the final Submit or Discard button press."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "cancel_submission":
        # Clear cache and state
        if user_id in user_cache: del user_cache[user_id]
        if user_id in user_states: del user_states[user_id]
        try:
            bot.edit_message_text("❌ Submission discarded.", chat_id, message_id, reply_markup=None)
        except Exception: # Handle potential message already deleted etc.
            bot.send_message(chat_id,"Submission discarded.")
        bot.answer_callback_query(call.id, "Submission cancelled.")
        return

    if call.data == "final_submit":
        if user_id not in user_cache or 'final_caption' not in user_cache[user_id]:
            logger.warning(f"User cache missing or incomplete for final submit: {user_id}")
            bot.edit_message_text("❌ Error: Submission data lost. Please start over with /add.", chat_id, message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "Error: Data missing", show_alert=True)
            return

        # --- Process the Submission (Insert into Pending DB) ---
        submission_data = user_cache.pop(user_id) # Get and remove data from cache
        category = submission_data.get('category', 'unknown')
        final_caption = submission_data.get('final_caption') # HTML formatted caption
        photo_file_id = submission_data.get('nature_pic_id') # Pokémon photo ID
        base_price_str = submission_data.get('base_price_str', '0')
        item_name = submission_data.get('pokemon_name', 'Unknown') # Includes TM code, Pokémon name
        if category == 'teams':
             item_name = submission_data.get('team_name', 'Unknown Team')

        pending_doc = {
            "user_id": str(user_id),
            "item_type": category, # Use category directly
            "submission_time": datetime.datetime.utcnow(),
            "details_text": final_caption, # Store the formatted HTML caption
            "photo_file_id": photo_file_id, # Will be None for TM/Team
            "status": "pending",
            "item_name": item_name, # Store extracted name
            "base_price_str": base_price_str,
            # Include nature/boosted if pokemon for easier admin view?
            "nature": submission_data.get('nature') if category in ['legendary', 'non_legendary', 'shiny'] else None,
            "boosted_stat": submission_data.get('boosted_stat') if category in ['legendary', 'non_legendary', 'shiny'] else None,
        }

        try:
            insert_result = pending_items_col.insert_one(pending_doc)
            pending_id = insert_result.inserted_id
        except Exception as e:
            logger.error(f"Failed to insert pending item for user {user_id}: {e}")
            bot.edit_message_text("❌ There was a database error submitting your item. Please try again later or contact admin.", chat_id, message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "Database Error", show_alert=True)
            # Optional: Put data back in cache if insert fails? Difficult state to recover.
            return

        # --- Notify User ---
        success_message = (
            f"✅ Your **{escape(item_name)}** has been submitted for approval!\n\n"
            f"You will receive a notification once it's reviewed by an administrator.\n"
            f"(Approval usually takes a few hours, max 1 day).\n\n"
            f"Track status or view approved items later using /myitems (coming soon)." # Update command name if needed
        )
        try:
            # Edit the preview message to show success
            bot.edit_message_text(success_message, chat_id, message_id, reply_markup=None, parse_mode="Markdown")
        except Exception: # Message might have been deleted
             bot.send_message(chat_id, success_message, parse_mode="Markdown")


        # --- Send to Admin Approval Channel ---
        admin_markup = types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('Approve', callback_data=f'approve_{pending_id}_{user_id}'),
            types.InlineKeyboardButton('Reject', callback_data=f'reject_{pending_id}_{user_id}')
        )
        # Send the same preview caption admins saw
        admin_caption_to_send = f"👇 Pending Submission | ID: `{pending_id}`\n"+ final_caption # Add pending ID

        try:
            # Ensure caption length limits
            if photo_file_id:
                 if len(admin_caption_to_send) > 1024: admin_caption_to_send = admin_caption_to_send[:1020] + "\n..."
                 bot.send_photo(APPROVE_CHANNEL, photo_file_id, caption=admin_caption_to_send, parse_mode='HTML', reply_markup=admin_markup)
            else:
                 if len(admin_caption_to_send) > 4096: admin_caption_to_send = admin_caption_to_send[:4092] + "\n..."
                 bot.send_message(APPROVE_CHANNEL, admin_caption_to_send, parse_mode='HTML', reply_markup=admin_markup)
            logger.info(f"Submission {pending_id} from {user_id} sent to admin channel.")
        except Exception as e:
            logger.error(f"Failed to send pending item {pending_id} to admin channel {APPROVE_CHANNEL}: {e}")
            # Consider notifying admins via another method if this fails

        bot.answer_callback_query(call.id, "Item Submitted for Approval!")

# === Admin Actions (Approve/Reject/Reason) ===
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_admin_actions(call):
    """Handles the initial Approve or Reject button press from the admin channel."""
    admin_user_id = call.from_user.id
    if not is_mod(admin_user_id): # Check if admin/mod
        bot.answer_callback_query(call.id, "You are not authorized.")
        return

    try:
        parts = call.data.split("_")
        action = parts[0] # approve or reject
        pending_id_str = parts[1]
        original_user_id = parts[2] # User who submitted

        pending_id = ObjectId(pending_id_str) # Convert string to ObjectId

        # --- Fetch the pending item ---
        # Use find_one for both initially, delete only after successful processing or rejection selection
        pending_item = pending_items_col.find_one({"_id": pending_id, "status": "pending"})

        if not pending_item:
            bot.answer_callback_query(call.id, "⚠️ Item already processed or not found.", show_alert=True)
            try: # Remove buttons if possible
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception: pass
            return

        # --- Basic Info ---
        userd = int(original_user_id)
        item_type = pending_item.get('item_type', 'unknown')
        item_details_text = pending_item.get('details_text', 'No details available.') # This is HTML formatted
        item_photo_id = pending_item.get('photo_file_id')
        item_name = pending_item.get('item_name', 'Unknown Item')
        base_price_str = pending_item.get('base_price_str', '0')
        admin_mention = f"@{call.from_user.username}" if call.from_user.username else f"Admin {admin_user_id}"


        # --- Handle Approval ---
        if action == 'approve':
            # 1. Post to Auction Channel (Main Item Post)
            try:
                 # Use the *original submission caption* for the main post
                 main_post_caption = item_details_text # Already HTML formatted
                 # Add approved by info? Optional.
                 # main_post_caption += f"\n\n<i>Approved by: {admin_mention}</i>"

                 # Limit caption length
                 if item_photo_id:
                      if len(main_post_caption) > 1024: main_post_caption = main_post_caption[:1020] + "\n..."
                      posted_msg = bot.send_photo(POST_CHANNEL, item_photo_id, caption=main_post_caption, parse_mode='HTML')
                 else:
                      if len(main_post_caption) > 4096: main_post_caption = main_post_caption[:4092] + "\n..."
                      posted_msg = bot.send_message(POST_CHANNEL, main_post_caption, parse_mode='HTML')

                 auction_post_link = f"https://t.me/c/{str(POST_CHANNEL)[4:]}/{posted_msg.message_id}"
                 logger.info(f"Posted item {pending_id} to auction channel. Link: {auction_post_link}")
            except Exception as post_err:
                 logger.error(f"Failed to post approved item {pending_id} to channel {POST_CHANNEL}: {post_err}")
                 bot.send_message(userd, f"❌ Error posting your approved item '{escape(item_name)}' to auction. Please contact admin.")
                 # Don't delete pending yet, maybe try again later? Or mark as failed.
                 # pending_items_col.update_one({"_id": pending_id}, {"$set": {"status":"post_failed", "error": str(post_err)}})
                 bot.answer_callback_query(call.id, "Error posting to auction channel.", show_alert=True)
                 return # Stop processing

            # 2. Add to Approved Items Collection (for /myitems)
            try:
                 approved_items_col.insert_one({
                     "user_id": str(userd),
                     "category": item_type, # Use the category from pending_item
                     "name": item_name,
                     "link": auction_post_link,
                     "approval_time": datetime.datetime.utcnow(),
                     "approved_by": str(admin_user_id),
                     "pending_item_id": pending_id # Link back to original submission
                 })
            except Exception as db_err:
                 logger.error(f"Failed to insert approved item {pending_id} into approved_items_col: {db_err}")
                 # Item posted but not tracked well. Notify admin.
                 bot.send_message(APPROVE_CHANNEL, f"🚨 DB ERROR: Failed to track approved item {item_name} ({auction_post_link}) in approved list.")
                 # Continue processing, but log the error.

            # 3. Get Next Bid ID
            bid_id = get_next_bid_id() # Use helper

            # 4. Parse Base Price
            base_price_numeric = parse_bid_amount(base_price_str)

            # 5. Create Bid Message in Auction Channel
            bot_username = bot.get_me().username
            bid_markup = InlineKeyboardMarkup().row(
                InlineKeyboardButton("🔄 Refresh", callback_data=f"ref_{bid_id}"),
                InlineKeyboardButton("🔗 Place Bid", url=f"https://t.me/{bot_username}?start=bid-{bid_id}")
            )
            # Use helper to create initial bid text
            bid_text = create_bid_message(bid_id, None, base_price_numeric, base_price_numeric)
            try:
                 bid_msg = bot.send_message(POST_CHANNEL, bid_text, reply_markup=bid_markup, parse_mode="Markdown")
                 logger.info(f"Sent bid message for {bid_id} to channel {POST_CHANNEL}")
            except Exception as bid_msg_err:
                 logger.error(f"Failed to send bid message for {bid_id} to channel {POST_CHANNEL}: {bid_msg_err}")
                 bot.send_message(userd, f"❌ Error setting up bidding for your item '{escape(item_name)}'. Please contact admin.")
                 # Item posted, but bidding setup failed. Critical. Attempt cleanup?
                 try: bot.delete_message(posted_msg.chat.id, posted_msg.message_id) # Delete main post
                 except: pass
                 approved_items_col.delete_one({"link": auction_post_link}) # Delete from approved list
                 # pending_items_col.update_one({"_id": pending_id}, {"$set": {"status":"bid_setup_failed", "error": str(bid_msg_err)}}) # Mark pending as failed
                 bot.answer_callback_query(call.id, "Error creating bid message.", show_alert=True)
                 return # Stop processing

            # 6. Create Bid Document in DB
            # Fetch owner details for mention
            owner_doc = get_user_doc(userd)
            owner_mention = format_username_html(owner_doc) if owner_doc else f"User {userd}"

            # *** ADD nature to the bid_doc ***
            item_nature = pending_item.get('nature') # Get nature from the pending item document

            bid_doc = {
                "bid_id": bid_id,
                "owner_id": str(userd),
                "owner_mention": owner_mention, # Store owner mention
                "base_price": base_price_numeric,
                "current_bid": base_price_numeric,
                "highest_bidder_id": None,
                "highest_bidder_mention": None,
                "message_id": bid_msg.message_id,
                "chat_id": bid_msg.chat.id,
                "auction_post_link": auction_post_link, # Link to the item post
                "item_type": item_type,
                "item_name": item_name,
                "nature": item_nature, # <-- ADDED THIS FIELD
                "status": "active",
                "history": {},
                "creation_time": datetime.datetime.utcnow(),
                "approved_by": str(admin_user_id)
            }
            # **** ADD LOGGING HERE FOR DIAGNOSIS ****
            logger.info(f"Creating bid document for {bid_id}. Item Type: {item_type}, Name: {item_name}, Nature: {item_nature}") # Log included nature
            try:
                 bids_col.insert_one(bid_doc)
                 logger.info(f"Created bid document for {bid_id}")
            except Exception as bids_db_err:
                 logger.error(f"CRITICAL: Failed to insert bid document for {bid_id}: {bids_db_err}")
                 # Very critical. Item posted, bid msg sent, but DB record failed. Needs admin fix.
                 bot.send_message(APPROVE_CHANNEL, f"🚨 CRITICAL DB ERROR: Failed to save bid data for {bid_id}. Item {item_name} is live but DB record missing! Please use /remo {bid_id} and re-approve. @admin")
                 try: bot.delete_message(bid_msg.chat.id, bid_msg.message_id)
                 except: pass
                 bot.answer_callback_query(call.id, "CRITICAL DB ERROR creating bid record.", show_alert=True)
                 return

            # 7. Delete the successfully processed pending item
            pending_items_col.delete_one({"_id": pending_id})

            # 8. Award Points & Notify User
            add_points(str(userd), 500, f"item_approval_{item_type}")
            try:
                 bot.send_message(userd, f"🎉 Your **{escape(item_name)}** Submission Has Been Approved!\n\nCheck the auction channel: {AUCTION_GROUP_LINK}", parse_mode='markdown', reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('View Auction', url=AUCTION_GROUP_LINK)))
            except Exception as notify_err:
                 logger.warning(f"Could not notify user {userd} about approval: {notify_err}")

            # 9. Log Approval in Admin Channel & Edit Original Admin Message
            try:
                 # Try editing caption first (for photo items)
                 bot.edit_message_caption(
                      chat_id=call.message.chat.id,
                      message_id=call.message.message_id,
                      caption=call.message.caption + f"\n\n✅ Approved by {admin_mention}. Bid ID: `{bid_id}`",
                      parse_mode='HTML', # Keep original parse mode
                      reply_markup=None # Remove buttons
                 )
            except telebot.apihelper.ApiTelegramException as edit_caption_err:
                 if "message is not modified" in str(edit_caption_err): pass # Ignore
                 elif "there is no caption in the message to edit" in str(edit_caption_err):
                      # Fallback to editing text if original was text-only
                      try:
                          bot.edit_message_text(
                               chat_id=call.message.chat.id,
                               message_id=call.message.message_id,
                               text=call.message.html_text + f"\n\n✅ Approved by {admin_mention}. Bid ID: `{bid_id}`", # Use html_text
                               parse_mode='HTML',
                               reply_markup=None # Remove buttons
                          )
                      except Exception as edit_text_err:
                           logger.warning(f"Could not edit approval message text (fallback) {call.message.message_id}: {edit_text_err}")
                           # Send separate confirmation if all edits fail
                           bot.send_message(APPROVE_CHANNEL, f"✅ Item '{escape(item_name)}' (`{pending_id_str}`) approved by {admin_mention}. Bid ID: `{bid_id}`")
                 else:
                      logger.warning(f"Could not edit approval message caption {call.message.message_id}: {edit_caption_err}")
                      bot.send_message(APPROVE_CHANNEL, f"✅ Item '{escape(item_name)}' (`{pending_id_str}`) approved by {admin_mention}. Bid ID: `{bid_id}`")
            except Exception as edit_err: # Catch other potential errors
                 logger.warning(f"Could not edit approval message {call.message.message_id}: {edit_err}")
                 bot.send_message(APPROVE_CHANNEL, f"✅ Item '{escape(item_name)}' (`{pending_id_str}`) approved by {admin_mention}. Bid ID: `{bid_id}`")


            bot.answer_callback_query(call.id, f"Item Approved. Bid ID: {bid_id}")

        # --- Handle Rejection ---
        elif action == 'reject':
            # Show rejection reasons to the admin who clicked reject
            markup = InlineKeyboardMarkup(row_width=2)
            # FIX: Truncate item_name in callback data to avoid exceeding limits (64 bytes)
            safe_item_name = item_name[:25].replace("_", "-") # Limit length further, replace problematic chars

            reasons = []
            if item_type in ['shiny', 'legendary', 'non_legendary']:
                 reasons = [
                     ('Nature Bad', 'n'), ('IVs Ded', 'i'), ('Move Missing', 'm'),
                     ('Poke Useless', 'd'), ('Base High', 'b'), ('Other', 'o')
                 ]
            elif item_type == 'tms':
                 reasons = [('Waste TM', 't'), ('Base High', 'b'), ('Other', 'o')]
            elif item_type == 'teams':
                 reasons = [('Level High', 'h'), ('Base High', 'b'), ('Other', 'o')]
            else: # Fallback
                 reasons = [('Base High', 'b'), ('Other', 'o')]

            buttons = [InlineKeyboardButton(text, callback_data=f'rejreason_{code}_{pending_id_str}_{userd}_{safe_item_name}') for text, code in reasons]
            # Add buttons to markup, respecting row_width
            for i in range(0, len(buttons), 2):
                 markup.row(*buttons[i:i+2])

            # Edit the original admin message to ask for reason
            try:
                 # Try editing caption first
                 bot.edit_message_caption(
                     chat_id=call.message.chat.id,
                     message_id=call.message.message_id,
                     caption=call.message.caption + f"\n\n✍️ Select reason for rejecting (by {admin_mention}):",
                     parse_mode='HTML',
                     reply_markup=markup
                 )
            except telebot.apihelper.ApiTelegramException as e:
                 if "there is no caption in the message to edit" in str(e):
                      # Fallback to editing text
                      try:
                           bot.edit_message_text(
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text=call.message.html_text + f"\n\n✍️ Select reason for rejecting (by {admin_mention}):",
                                parse_mode='HTML',
                                reply_markup=markup
                           )
                      except Exception as text_err:
                           logger.warning(f"Could not edit message text to ask for rejection reason: {text_err}")
                           # Send new message if edits fail
                           bot.send_message(call.message.chat.id, f"Select reason for rejecting '{escape(item_name)}' (`{pending_id_str}`):", reply_markup=markup)
                 else:
                      logger.warning(f"Could not edit caption to ask for rejection reason: {e}")
                      bot.send_message(call.message.chat.id, f"Select reason for rejecting '{escape(item_name)}' (`{pending_id_str}`):", reply_markup=markup)
            except Exception as e: # Catch other errors
                 logger.warning(f"Could not edit message to ask for rejection reason: {e}")
                 bot.send_message(call.message.chat.id, f"Select reason for rejecting '{escape(item_name)}' (`{pending_id_str}`):", reply_markup=markup)

            bot.answer_callback_query(call.id, "Select rejection reason.")
            # DO NOT delete from pending_items yet. It's deleted after reason is selected.

    except ObjectId.InvalidId:
         bot.answer_callback_query(call.id, "❌ Invalid item ID format.", show_alert=True)
    except Exception as e:
         logger.error(f"Error in handle_admin_actions for data {call.data}: {e}", exc_info=True) # Log traceback
         bot.answer_callback_query(call.id, "An error occurred processing the action.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rejreason_"))
def handle_rejection_reason(call):
    """Handles the callback when an admin selects a rejection reason."""
    admin_user_id = call.from_user.id
    if not is_mod(admin_user_id):
         bot.answer_callback_query(call.id, "You are not authorized.")
         return

    try:
        parts = call.data.split("_")
        if len(parts) < 5: raise IndexError("Callback data incomplete")
        reason_code = parts[1] # n, i, m, d, b, t, h, o
        pending_id_str = parts[2]
        userd = int(parts[3])
        item_name_safe = parts[4] # Safe item name from callback

        pending_id = ObjectId(pending_id_str)
        admin_mention = f"@{call.from_user.username}" if call.from_user.username else f"Admin {admin_user_id}"

        # --- Update the item status to 'rejected' and DELETE ---
        # Find the item again to get full name before deleting (safe name might be truncated)
        pending_item = pending_items_col.find_one({"_id": pending_id})
        full_item_name = pending_item.get('item_name', item_name_safe) if pending_item else item_name_safe

        delete_result = pending_items_col.delete_one({"_id": pending_id})

        if delete_result.deleted_count == 0:
            bot.answer_callback_query(call.id, "⚠️ Item already processed or removed.", show_alert=True)
            try: bot.delete_message(call.message.chat.id, call.message.message_id) # Delete reason buttons message
            except Exception: pass
            return

        # --- Determine rejection text ---
        reason_text_map = {
            'n': 'Nature Is Rip.', 'i': 'IVs Are Rip.', 'm': 'Main Move Missing.',
            'd': 'Pokémon Is Useless.', 'b': 'Base Price Too High.', 't': 'Useless TM.',
            'h': 'Team Level Too High.', 'o': 'Other/Admin Discretion.' # Changed 'Other' slightly
        }
        reason_full_text = reason_text_map.get(reason_code, 'Reason not specified.')

        # --- Notify User and Log Rejection ---
        notification_text = (
            f"🔴 Your submission for **{escape(full_item_name)}** was rejected.\n\n"
            f"**Reason:** {reason_full_text}"
        )

        try:
            bot.send_message(userd, notification_text, parse_mode='Markdown')
        except Exception as notify_err:
            logger.warning(f"Could not notify user {userd} about rejection: {notify_err}")

        # Log in reject channel (can be same as approve channel)
        user_doc_rejected = get_user_doc(userd)
        rejected_user_mention = format_username_html(user_doc_rejected) if user_doc_rejected else f"User {userd}"

        log_text = (
            f"🚫 Item Rejected: '{escape(full_item_name)}' (ID: `{pending_id_str}`)\n"
            f"👤 Submitter: {rejected_user_mention}\n"
            f"🛡️ Rejected By: {admin_mention}\n"
            f"💬 Reason: {reason_full_text}"
        )
        try:
            bot.send_message(REJECT_CHANNEL, log_text, parse_mode='HTML', disable_web_page_preview=True)
        except Exception as log_err:
            logger.error(f"Failed to log rejection to channel {REJECT_CHANNEL}: {log_err}")

        # --- Clean up admin message (the reason selection message) ---
        try:
            # Edit the message that had the reason buttons
             bot.edit_message_caption(
                 chat_id=call.message.chat.id,
                 message_id=call.message.message_id,
                 # Original caption might be lost if edit failed before, reconstruct:
                 caption=f"👇 Pending Submission | ID: `{pending_id_str}`\n ... (Original Details) ... \n\n"
                         f"🚫 Rejected by {admin_mention}. Reason: {reason_full_text}",
                 reply_markup=None
             )
            # Or simpler:
            # bot.edit_message_text(
            #     chat_id=call.message.chat.id,
            #     message_id=call.message.message_id,
            #     text=f"Rejection reason '{reason_full_text}' selected for item `{pending_id_str}` by {admin_mention}.",
            #     reply_markup=None
            # )
        except Exception as edit_err:
            logger.warning(f"Could not edit rejection reason message: {edit_err}")

        bot.answer_callback_query(call.id, f"Rejection ({reason_full_text}) processed.")
        logger.info(f"Item {pending_id_str} rejected by {admin_user_id}. Reason code: {reason_code}")

    except ObjectId.InvalidId:
        bot.answer_callback_query(call.id, "❌ Invalid item ID format.", show_alert=True)
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "❌ Invalid callback data format.", show_alert=True)
        logger.error(f"Invalid rejection reason callback data: {call.data}")
    except Exception as e:
        logger.error(f"Error processing rejection reason {call.data}: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "An error occurred.", show_alert=True)


# === Bidding System ===

def handle_bid_link(message, command_param):
    """Handles the click on a bid link (?start=bid-P123)."""
    user_id = message.from_user.id
    user_id_str = str(user_id)

    # --- Pre-checks ---
    if is_banned(user_id):
        bot.reply_to(message, "You are banned and cannot place bids.")
        return

    user_doc = get_user_doc(user_id)
    if not user_doc:
        bot.reply_to(message, "Please /start the bot first.")
        return
    if not is_user_updated(user_doc):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update'))
        bot.reply_to(message, '<blockquote><b>Please update the bot first.</b></blockquote>', parse_mode='html', reply_markup=markup, disable_web_page_preview=True)
        return

    if not bid_ji: # Check global bidding status flag
        bot.reply_to(message, "Bidding is currently closed.")
        return

    # --- Process Bid Link ---
    try:
        bid_id = command_param.split('-')[1].upper() # Ensure P is uppercase
    except IndexError:
        bot.reply_to(message, "Invalid bid link format.")
        return

    # Fetch bid data from DB
    bid_data = bids_col.find_one({"bid_id": bid_id})

    if not bid_data:
        bot.reply_to(message, f"⚠️ Auction `{bid_id}` not found or is invalid.")
        return

    if bid_data.get("status") != "active":
        bot.reply_to(message, f"⚠️ Auction `{bid_id}` has ended and is no longer active.")
        return

    # Check if bidder is the owner
    owner_id = bid_data.get('owner_id')
    if user_id_str == owner_id:
        bot.reply_to(message, "❌ You cannot bid on your own item!")
        return

    # Prompt for bid amount
    item_name_display = escape(bid_data.get('item_name', bid_id))
    current_bid = bid_data.get('current_bid', bid_data.get('base_price', 0))
    current_bid_display = f"{current_bid:,.0f}" # Format with comma, no decimals

    min_increment = get_min_bid_increment(current_bid)
    required_bid_display = f"{current_bid + min_increment:,.0f}"

    msg = bot.send_message(
        message.chat.id,
        f"🛒 Placing bid on: **{item_name_display}** (`{bid_id}`)\n"
        f"💰 Current Highest Bid: `{current_bid_display}`\n"
        f"📈 Minimum Next Bid: `{required_bid_display}`\n\n"
        f"➡️ Please enter your bid amount (e.g., `1k`, `5500`, `2.5k`, `100pd`).\n"
        f"*(See /brules for increment rules)*",
        parse_mode="Markdown"
        )

    # Register next step handler to capture the bid amount
    # Pass necessary context: bid_id, user's full name, current bid (for validation)
    bot.register_next_step_handler(msg, process_bid_amount_input, bid_id, message.from_user.full_name, current_bid)


def process_bid_amount_input(message, bid_id, bidder_full_name, current_bid_at_prompt):
    """Handles the message containing the user's bid amount."""
    user_id = message.from_user.id
    user_id_str = str(user_id)
    bid_amount_str = message.text.strip()

    # --- Validation ---
    # Re-fetch bid data to get the absolute latest status and bid
    bid_data = bids_col.find_one({"bid_id": bid_id})
    if not bid_data or bid_data.get("status") != "active":
        bot.reply_to(message, "❌ Auction not found or has ended.")
        return

    # Parse the entered bid amount
    bid_amount_numeric = parse_bid_amount(bid_amount_str)
    if bid_amount_numeric <= 0:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Try Again', url=f"https://t.me/{bot.get_me().username}?start=bid-{bid_id}"))
        bot.reply_to(message, "❌ Invalid bid amount. Please enter a positive value (e.g., `1k`, `5500`).", reply_markup=markup)
        return

    # --- Get Current Bid Info ---
    current_bid_latest = bid_data.get('current_bid', 0.0)
    highest_bidder_id = bid_data.get('highest_bidder_id')

    # --- Check Rules ---
    if user_id_str == highest_bidder_id:
        bot.reply_to(message, "⚠️ You are already the highest bidder on this item.")
        return

    # Use the latest current bid for increment calculation
    min_increment = get_min_bid_increment(current_bid_latest)
    required_bid = current_bid_latest + min_increment
    required_bid_display = f"{required_bid:,.0f}"
    current_bid_latest_display = f"{current_bid_latest:,.0f}"
    min_increment_display = f"{min_increment:,.0f}"


    if bid_amount_numeric < required_bid:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Try Again', url=f"https://t.me/{bot.get_me().username}?start=bid-{bid_id}"))
        bot.reply_to(message, f"❌ Bid too low! Your bid must be at least `{required_bid_display}` (Current: `{current_bid_latest_display}` + Min Increment: `{min_increment_display}`). See /brules.", parse_mode="Markdown", reply_markup=markup)
        return

    # --- Ask for Confirmation ---
    # Store bid details in a temporary cache for confirmation
    # Include bidder's mention format here
    bidder_mention_md = f"[{escape(bidder_full_name)}](tg://user?id={user_id})"
    confirmation_key = f"{user_id}_{bid_id}_{int(time.time())}"
    pending_bids[confirmation_key] = {
        'user_id': user_id,
        'bidder_mention': bidder_mention_md, # Store the formatted mention
        'bid_id': bid_id,
        'bid_amount': bid_amount_numeric, # Store numeric value
        'previous_bidder_id': highest_bidder_id, # Store previous bidder ID string
        'original_message_id': message.message_id # ID of the message where they typed the bid
    }

    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Confirm Bid", callback_data=f"confirmbid_{confirmation_key}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancelbid_{confirmation_key}")
    )

    item_name_display = escape(bid_data.get('item_name', bid_id))
    bid_amount_display = f"{bid_amount_numeric:,.0f}"
    bot.reply_to(
        message,
        f"🔔 **Bid Confirmation**\n\n"
        f"Item: **{item_name_display}** (`{bid_id}`)\n"
        f"Your Bid: `{bid_amount_display}`\n"
        f"Current Highest: `{current_bid_latest_display}`\n\n"
        f"Please confirm your bid:",
        parse_mode="Markdown",
        reply_markup=markup
    )

    # Schedule expiration for the pending confirmation
    schedule_bid_expiration(confirmation_key, 120) # 2 minutes expiration


def schedule_bid_expiration(confirmation_key, timeout=120):
    """Schedules the expiration of a pending bid confirmation."""
    def expire_bid():
        if confirmation_key in pending_bids:
             bid_details = pending_bids.pop(confirmation_key) # Get and remove
             logger.info(f"Pending bid {confirmation_key} expired.")
             # Try to edit the confirmation message
             try:
                 bot.edit_message_text(
                     "⏰ Bid confirmation expired. Please try bidding again if you're still interested.",
                     chat_id=bid_details['user_id'], # Send to user's chat
                     message_id=bid_details['original_message_id'] + 1, # The ID of the confirmation message sent by the bot
                     reply_markup=None
                 )
             except Exception as e:
                 logger.warning(f"Could not edit expired bid confirmation message: {e}")


    threading.Timer(timeout, expire_bid).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith(("confirmbid_", "cancelbid_")))
def handle_bid_confirmation(call):
    """Handles the Confirm Bid or Cancel callback."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id # ID of the confirmation message

    try:
        action, confirmation_key = call.data.split("_", 1)
    except ValueError:
         logger.error(f"Invalid bid confirmation callback data: {call.data}")
         bot.answer_callback_query(call.id, "Error: Invalid data")
         return

    # Check if the confirmation is still valid and retrieve details
    if confirmation_key not in pending_bids:
        bot.answer_callback_query(call.id, "⚠️ This confirmation has expired or is invalid.", show_alert=True)
        try: bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        except Exception: pass
        return

    # Use pop to get details AND remove from pending atomically (prevents race conditions)
    bid_details = pending_bids.pop(confirmation_key)

    # Ensure the user clicking is the one who initiated
    if user_id != bid_details['user_id']:
         pending_bids[confirmation_key] = bid_details # Put it back if wrong user clicked
         bot.answer_callback_query(call.id, "This confirmation is not for you.")
         return

    # --- Handle Cancellation ---
    if action == "cancelbid":
        # It was already removed by pop
        bot.answer_callback_query(call.id, "❌ Bid cancelled.")
        try:
            bot.edit_message_text("❌ Bid cancelled.", chat_id=chat_id, message_id=message_id, reply_markup=None)
        except Exception: pass # Ignore if message already gone
        return

    # --- Handle Confirmation ---
    if action == "confirmbid":
        try:
            # Retrieve details from the popped dictionary
            bidder_id = bid_details['user_id']
            bidder_id_str = str(bidder_id)
            bidder_mention = bid_details['bidder_mention'] # Already formatted Markdown mention
            bid_id = bid_details['bid_id']
            bid_amount = bid_details['bid_amount']
            previous_bidder_id_str = bid_details['previous_bidder_id'] # Already a string or None

            # --- Re-verify bid validity against DB ---
            bid_data = bids_col.find_one({"bid_id": bid_id})
            if not bid_data or bid_data.get("status") != "active":
                bot.answer_callback_query(call.id, "❌ Auction ended or was removed while confirming.", show_alert=True)
                try: bot.edit_message_text("❌ Auction ended or was removed.", chat_id=chat_id, message_id=message_id, reply_markup=None)
                except Exception: pass
                # No need to remove from pending_bids, already popped
                return

            current_bid_db = bid_data.get('current_bid', 0.0)
            bid_amount_display = f"{bid_amount:,.0f}"
            current_bid_db_display = f"{current_bid_db:,.0f}"

            if bid_amount <= current_bid_db:
                bot.answer_callback_query(call.id, "⚠️ Someone placed a higher bid while you were confirming!", show_alert=True)
                try: bot.edit_message_text(f"❌ Your bid of `{bid_amount_display}` is no longer the highest. Current bid is `{current_bid_db_display}`.", chat_id=chat_id, message_id=message_id, reply_markup=None, parse_mode="Markdown")
                except Exception: pass
                # No need to remove from pending_bids, already popped
                return

            # --- Update Bid in Database ---
            # Use find_one_and_update for atomicity
            update_result = bids_col.find_one_and_update(
                {"bid_id": bid_id, "status": "active", "current_bid": current_bid_db}, # Ensure current bid hasn't changed again
                {"$set": {
                    "current_bid": bid_amount,
                    "highest_bidder_id": bidder_id_str,
                    "highest_bidder_mention": bidder_mention, # Use the MD formatted mention
                    "last_bid_time": datetime.datetime.utcnow(),
                    # Add/update bidder in history using user ID as key
                    f"history.{bidder_id_str}": {'mention': bidder_mention, 'amount': bid_amount, 'time': datetime.datetime.utcnow()}
                   }
                },
                return_document=pymongo.ReturnDocument.AFTER # Return the updated doc
            )


            if not update_result:
                 # This means the bid status changed OR current_bid changed between find_one and update_one
                 logger.warning(f"Bid {bid_id} status or amount changed before final update confirmation.")
                 bot.answer_callback_query(call.id, "❌ Auction status or bid amount changed before confirming.", show_alert=True)
                 try: bot.edit_message_text("❌ Auction status or bid changed. Please try again.", chat_id=chat_id, message_id=message_id, reply_markup=None)
                 except Exception: pass
                 # No need to remove from pending_bids, already popped
                 return

            # --- Bid Successfully Placed ---
            # No need to remove from pending_bids, already popped

            # 1. Log bid to admin channel
            log_bid_to_admin_channel(bidder_id, bidder_mention, bid_id, bid_amount)

            # 2. Award Points
            add_points(bidder_id_str, 100, f"successful_bid_{bid_id}")

            # 3. Update the main bid message in the auction channel
            update_bid_message_in_channel(bid_id) # Update message with new info

            # 4. Edit the confirmation message for the user
            # Get the updated bid message link from the update_result
            bid_link_url = "#"
            if update_result:
                 msg_link_chat_id = update_result.get('chat_id')
                 msg_link_msg_id = update_result.get('message_id')
                 if msg_link_chat_id and msg_link_msg_id:
                      bid_link_url = f"https://t.me/c/{str(msg_link_chat_id)[4:]}/{msg_link_msg_id}"

            confirmation_text = (
                 f"✅ Your bid of `{bid_amount_display}` on `{bid_id}` has been placed!\n"
                 f"📌 [View Bid Message]({bid_link_url})\n\n"
                 f"💰 +100 Points Awarded!"
            )
            try:
                bot.edit_message_text(
                    confirmation_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="markdown",
                    reply_markup=None,
                    disable_web_page_preview=True
                )
            except Exception as edit_err:
                 logger.warning(f"Could not edit bid confirmation success message: {edit_err}")
                 # Send new message if edit fails
                 bot.send_message(chat_id, confirmation_text, parse_mode="markdown", disable_web_page_preview=True)

            # 5. Notify previous highest bidder if they exist
            if previous_bidder_id_str and previous_bidder_id_str != bidder_id_str:
                notify_outbid_user(previous_bidder_id_str, bid_amount, bid_id)

            bot.answer_callback_query(call.id, "✅ Bid confirmed successfully!")
            logger.info(f"User {bidder_id_str} successfully bid {bid_amount} on {bid_id}")

        except Exception as e:
            logger.error(f"Error confirming bid {confirmation_key}: {e}", exc_info=True)
            bot.answer_callback_query(call.id, "❌ An error occurred while confirming your bid.", show_alert=True)
            try: # Try to remove buttons from confirmation message on error
                 bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
            except Exception: pass
            # If an error occurred after pop but before completion, the bid is lost from pending.
            # This case should be rare with find_one_and_update.


def log_bid_to_admin_channel(user_id, user_mention, bid_id, bid_amount):
    """Logs successful bid details to the admin bid log channel."""
    try:
        bid_amount_display = f"{bid_amount:,.0f}"
        log_text = (
            f" Bidding Log \n"
            f"👤 User: {user_mention} (`{user_id}`)\n" # User mention is already formatted
            f"🏷️ Item ID: `{bid_id}`\n"
            f"💰 Bid Amount: `{bid_amount_display}`\n"
            f"🕒 Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        bot.send_message(ADMIN_BID_LOG_CHANNEL, log_text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
         logger.error(f"Failed to log successful bid to admin channel {ADMIN_BID_LOG_CHANNEL}: {e}")


def notify_outbid_user(previous_bidder_id_str, new_bid_amount, bid_id):
    """Notifies the previously highest bidder they were outbid."""
    try:
        # Fetch bid data to get item name and message link
        bid_data = bids_col.find_one({"bid_id": bid_id}, {"item_name": 1, "chat_id": 1, "message_id": 1})
        if not bid_data: return # Should not happen if called correctly

        item_name = escape(bid_data.get("item_name", bid_id))
        msg_chat_id = bid_data.get("chat_id")
        msg_message_id = bid_data.get("message_id")
        view_link = f"https://t.me/c/{str(msg_chat_id)[4:]}/{msg_message_id}" if msg_chat_id and msg_message_id else "#"
        bot_username = bot.get_me().username
        new_bid_amount_display = f"{new_bid_amount:,.0f}"


        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔗 Place New Bid", url=f'https://t.me/{bot_username}?start=bid-{bid_id}')
        )

        bot.send_message(
            int(previous_bidder_id_str),
            f"⚠️ You've been outbid on **{item_name}** (`{bid_id}`)!\n\n"
            f"🔹 New Highest Bid: `{new_bid_amount_display}`\n"
            f"🔗 [View Item Bid]({view_link})",
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=markup
        )
        logger.info(f"Notified user {previous_bidder_id_str} they were outbid on {bid_id}")
    except telebot.apihelper.ApiTelegramException as e:
         logger.error(f"Failed to notify previous bidder {previous_bidder_id_str} (API Error {e.error_code}): {e.description}")
    except Exception as e:
        logger.error(f"Unexpected error notifying previous bidder {previous_bidder_id_str}: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("ref_"))
def refresh_bid(call):
    """Refreshes the bid message in the auction channel."""
    try:
        bid_id = call.data.split("_")[1]
        update_bid_message_in_channel(bid_id) # Use the helper function
        bot.answer_callback_query(call.id, f"✅ Bid info for {bid_id} refreshed!")
    except IndexError:
         bot.answer_callback_query(call.id, "Error: Invalid refresh data.")
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" in str(e):
              bot.answer_callback_query(call.id, "ℹ️ Bid info is already up-to-date.")
         else:
              logger.error(f"Error refreshing bid {call.data}: {e}")
              bot.answer_callback_query(call.id, "Error refreshing bid info.")
    except Exception as e:
        logger.error(f"Error refreshing bid {call.data}: {e}")
        bot.answer_callback_query(call.id, "Error refreshing bid info.")


@bot.message_handler(commands=['removebid'])
def remove_last_bid(message):
    """Admin command to remove the last bid on an item, reverting to the previous bidder."""
    if not is_mod(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage: `/removebid <bid_id>` (e.g., `/removebid P123`)")
        return

    bid_id_to_modify = args[1].strip().upper()

    try:
        # --- Find the bid ---
        bid_data = bids_col.find_one({"bid_id": bid_id_to_modify})
        if not bid_data:
            bot.reply_to(message, f"❌ No auction found with Bid ID: `{bid_id_to_modify}`")
            return
        if bid_data.get("status") != "active":
             bot.reply_to(message, f"⚠️ Auction `{bid_id_to_modify}` is not active.")
             return

        # --- Identify current and previous bidder ---
        current_bidder_id = bid_data.get('highest_bidder_id')
        history = bid_data.get('history', {})

        if not current_bidder_id:
            bot.reply_to(message, f"⚠️ There are no bids to remove on `{bid_id_to_modify}`.")
            return

        # Remove the current highest bidder from history temporarily to find the previous one
        if current_bidder_id in history:
             last_bid_info = history.pop(current_bidder_id) # Remove and store last bid info
             removed_bid_amount = last_bid_info.get('amount', 'N/A')
             removed_bid_amount_display = f"{removed_bid_amount:,.0f}" if isinstance(removed_bid_amount, (int, float)) else "N/A"
        else:
             logger.warning(f"Highest bidder {current_bidder_id} not found in history for {bid_id_to_modify}")
             last_bid_info = None # Cannot determine previous bid accurately
             removed_bid_amount_display = "N/A"

        # Find the new highest bid from the remaining history
        new_highest_bidder_id = None
        new_bid_amount = bid_data.get('base_price', 0.0) # Default to base price
        new_highest_bidder_mention = None

        if history: # If there are previous bidders
            # Find the user ID with the maximum amount in the remaining history
            new_highest_bidder_id = max(history, key=lambda k: history[k].get('amount', 0.0))
            new_bid_amount = history[new_highest_bidder_id].get('amount', new_bid_amount)
            new_highest_bidder_mention = history[new_highest_bidder_id].get('mention')

        new_bid_amount_display = f"{new_bid_amount:,.0f}"
        base_price_display = f"{bid_data.get('base_price', 0.0):,.0f}"


        # --- Update the bid document in DB ---
        update_result = bids_col.update_one(
            {"bid_id": bid_id_to_modify},
            {"$set": {
                "current_bid": new_bid_amount,
                "highest_bidder_id": new_highest_bidder_id,
                "highest_bidder_mention": new_highest_bidder_mention,
                "history": history, # Save the history *without* the removed bidder
                "last_bid_time": datetime.datetime.utcnow() # Update timestamp
               }
            }
        )

        if update_result.modified_count > 0:
            # --- Update the bid message ---
            update_bid_message_in_channel(bid_id_to_modify)

            # --- Notify Admin ---
            admin_notification = f"✅ Last bid (`{removed_bid_amount_display}`) removed from `{bid_id_to_modify}` by @{message.from_user.username}.\n"
            if new_highest_bidder_mention:
                admin_notification += f" reinstated bidder: {new_highest_bidder_mention} at `{new_bid_amount_display}`."
            else:
                admin_notification += f" No previous bidders. Bid reset to base price `{base_price_display}`."
            bot.reply_to(message, admin_notification, parse_mode="Markdown", disable_web_page_preview=True)
            logger.info(f"Last bid removed from {bid_id_to_modify} by {message.from_user.id}.")

            # --- Notify the removed bidder ---
            if last_bid_info:
                try:
                    bot.send_message(
                        int(current_bidder_id),
                        f"ℹ️ Your last bid of `{removed_bid_amount_display}` on item `{bid_id_to_modify}` was removed by an administrator.",
                         parse_mode="Markdown"
                         )
                except Exception as e:
                    logger.warning(f"Could not notify user {current_bidder_id} about bid removal: {e}")

            # --- Notify the new highest bidder (if any) ---
            if new_highest_bidder_id:
                try:
                    bot.send_message(
                        int(new_highest_bidder_id),
                        f"🎉 The last bid on item `{bid_id_to_modify}` was removed. You are now the highest bidder again with `{new_bid_amount_display}`!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"Could not notify new highest bidder {new_highest_bidder_id}: {e}")

        else:
             bot.reply_to(message, f"⚠️ Could not remove bid from `{bid_id_to_modify}`. Bid might have already been removed or an error occurred.")
             # Put removed history back if needed?
             if current_bidder_id and last_bid_info:
                  history[current_bidder_id] = last_bid_info # Restore popped item if update failed

    except Exception as e:
        logger.error(f"Error removing last bid for {bid_id_to_modify}: {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while removing the bid.")

# === User Information Commands (/mybids, /myphg, /mysold) ===
# Placeholder for /myitems (to view approved/pending items)
@bot.message_handler(commands=['myitems'])
def my_items(message):
    """Shows the user their submitted items (pending and approved)."""
    user_id = message.from_user.id
    user_id_str = str(user_id)

    # --- Pre-checks ---
    if is_banned(user_id):
        bot.reply_to(message, "You are banned.")
        return

    user_doc = get_user_doc(user_id)
    if not user_doc:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Start Bot', url=f'https://t.me/{bot.get_me().username}?start=start'))
        bot.reply_to(message, "You need to /start the bot first.", reply_markup=markup)
        return

    if not is_user_updated(user_doc):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update'))
        bot.reply_to(message, 'Please update the bot first.', reply_markup=markup)
        return

    # --- Fetch Items ---
    pending_items = []
    approved_items = []
    try:
        # Fetch Pending Items
        pending_cursor = pending_items_col.find(
            {"user_id": user_id_str, "status": "pending"},
            {"item_name": 1, "item_type": 1, "submission_time": 1, "_id": 1} # Project fields
        ).sort("submission_time", pymongo.DESCENDING)
        pending_items = list(pending_cursor)

        # Fetch Approved Items
        approved_cursor = approved_items_col.find(
            {"user_id": user_id_str},
            {"name": 1, "category": 1, "link": 1, "approval_time": 1} # Project fields
        ).sort("approval_time", pymongo.DESCENDING)
        approved_items = list(approved_cursor)

    except Exception as e:
        logger.error(f"Error fetching /myitems for user {user_id}: {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while fetching your submitted items.")
        return

    # --- Format Message ---
    text_lines = ["📦 **Your Submitted Items**\n"]
    markup = InlineKeyboardMarkup()
    has_items = False

    # Pending Items Section
    if pending_items:
        has_items = True
        text_lines.append("⏳ **Pending Approval:**")
        for item in pending_items:
            name = escape(item.get('item_name', f"ID {item.get('_id')}"))
            item_type = escape(item.get('item_type', 'Unknown').capitalize())
            sub_time = item.get('submission_time').strftime('%Y-%m-%d %H:%M') if item.get('submission_time') else 'N/A'
            # Add a way to report/cancel pending item? Link to /report?
            text_lines.append(f"  - {name} ({item_type}) | Submitted: {sub_time}")
            # Example button to request cancellation via report (optional)
            # markup.add(InlineKeyboardButton(f"Request Cancel: {name}", callback_data=f"req_cancel_{item.get('_id')}"))
        text_lines.append("") # Add spacing

    # Approved Items Section
    if approved_items:
        has_items = True
        text_lines.append("✅ **Approved & Auctioned:**")
        for item in approved_items:
            name = escape(item.get('name', 'Unknown'))
            category = escape(item.get('category', 'Unknown').capitalize())
            link = item.get('link', '#')
            text_lines.append(f"  - [{name} ({category})]({link})")
            # Add button linking directly
            markup.add(InlineKeyboardButton(f"View: {name}", url=link))
        text_lines.append("") # Add spacing

    if not has_items:
        text_lines.append("You haven't submitted any items yet, or none are currently pending/approved.")
        text_lines.append("\nUse /add to submit an item!")

    markup.add(InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id}"))

    full_text = "\n".join(text_lines)
    if len(full_text) > 4096:
        full_text = full_text[:4092] + "\n..."

    bot.reply_to(message, full_text, reply_markup=markup, parse_mode="Markdown", disable_web_page_preview=True)


@bot.message_handler(commands=['mybids'])
def my_bids(message):
    """Shows the user their active bids."""
    user_id = message.from_user.id
    user_id_str = str(user_id)

    user_doc = get_user_doc(user_id)
    if not user_doc or not is_user_updated(user_doc):
        if not user_doc: bot.reply_to(message, "Please /start the bot first.")
        else:
             markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update'))
             bot.reply_to(message, 'Please update the bot first.', reply_markup=markup)
        return

    # Find bids where the user is the highest bidder OR is in the history
    try:
        # Query for bids where user is highest OR in history, and status is active
        bids_cursor = bids_col.find(
            {
             "status": "active",
             "$or": [
                 {"highest_bidder_id": user_id_str},
                 {f"history.{user_id_str}": {"$exists": True}}
             ]
            },
            {"bid_id": 1, "item_name": 1, "current_bid": 1, "highest_bidder_id": 1, "chat_id": 1, "message_id": 1, f"history.{user_id_str}.amount": 1} # Project fields
        ).sort("last_bid_time", pymongo.DESCENDING) # Sort by most recent activity

        user_bids_info = []
        for bid in bids_cursor:
            bid_id = bid['bid_id']
            item_name = escape(bid.get('item_name', bid_id))
            current_bid_amount = bid.get('current_bid', 0.0)
            is_highest = (bid.get('highest_bidder_id') == user_id_str)
            # Get the user's specific bid amount from history if they aren't highest
            user_bid_amount = bid.get('history', {}).get(user_id_str, {}).get('amount', current_bid_amount) if not is_highest else current_bid_amount
            user_bid_amount_display = f"{user_bid_amount:,.0f}"


            # Create message link
            msg_chat_id = bid.get('chat_id')
            msg_message_id = bid.get('message_id')
            link = f"https://t.me/c/{str(msg_chat_id)[4:]}/{msg_message_id}" if msg_chat_id and msg_message_id else "#"

            user_bids_info.append({
                "bid_id": bid_id,
                "name": item_name,
                "amount_display": user_bid_amount_display,
                "amount_numeric": user_bid_amount, # For sorting
                "is_highest": is_highest,
                "link": link
            })

        # Add pending bids from memory
        pending_count = 0
        for key, pending_bid_details in list(pending_bids.items()): # Use list to avoid modification during iteration issues
            if str(pending_bid_details['user_id']) == user_id_str:
                 pending_count += 1
                 # Find the corresponding bid data for link (might fail if bid removed)
                 bid_data_pending = bids_col.find_one({"bid_id": pending_bid_details['bid_id']}, {"chat_id": 1, "message_id": 1, "item_name": 1})
                 link_pending = "#"
                 item_name_pending = f"Item {pending_bid_details['bid_id']}"
                 if bid_data_pending:
                      msg_chat_id_p = bid_data_pending.get('chat_id')
                      msg_message_id_p = bid_data_pending.get('message_id')
                      link_pending = f"https://t.me/c/{str(msg_chat_id_p)[4:]}/{msg_message_id_p}" if msg_chat_id_p and msg_message_id_p else "#"
                      item_name_pending = escape(bid_data_pending.get('item_name', item_name_pending))

                 pending_amount = pending_bid_details['bid_amount']
                 pending_amount_display = f"{pending_amount:,.0f}"

                 user_bids_info.append({
                     "bid_id": pending_bid_details['bid_id'],
                     "name": item_name_pending,
                     "amount_display": pending_amount_display,
                     "amount_numeric": pending_amount, # For sorting
                     "is_highest": False, # It's pending, not highest yet
                     "link": link_pending,
                     "is_pending": True
                 })


        if not user_bids_info:
            bot.reply_to(message, "❌ You haven't placed any active bids yet.")
            return

        # --- Format and Send ---
        markup = InlineKeyboardMarkup()
        text_lines = ["📜 **Your Active Bids:**\n"]
        if pending_count > 0:
             text_lines[0] = f"📜 **Your Active Bids ({pending_count} Pending Confirmation):**\n"


        # Sort: Pending first, then Highest bids, then others by amount descending
        user_bids_info.sort(key=lambda x: (not x.get('is_pending', False), not x['is_highest'], -x['amount_numeric']))

        for bid_info in user_bids_info:
            status_indicator = "⏳ Pending" if bid_info.get('is_pending') else ("⭐ Highest" if bid_info['is_highest'] else "📉 Outbid")
            line = f"- `{bid_info['bid_id']}` ({bid_info['name']}): `{bid_info['amount_display']}` {status_indicator}"
            text_lines.append(line)
            # Add button linking to bid section (or confirmation message if pending?)
            button_text = f"{bid_info['name']} ({bid_info['bid_id']}) - {'Confirm?' if bid_info.get('is_pending') else 'View'}"
            markup.add(InlineKeyboardButton(button_text, url=bid_info['link']))

        markup.add(InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id}"))

        full_text = "\n".join(text_lines)
        # Handle potential message length issues
        if len(full_text) > 4096:
             full_text = full_text[:4092] + "\n... (list truncated)"

        bot.reply_to(message, full_text, reply_markup=markup, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error fetching /mybids for {user_id}: {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while fetching your bids.")


@bot.message_handler(commands=['myphg'])
def myphg_command(message):
    """Shows items where the user is the highest bidder (intended for *after* auction ends)."""
    user_id = message.from_user.id
    user_id_str = str(user_id)

    user_doc = get_user_doc(user_id)
    if not user_doc or not is_user_updated(user_doc):
        if not user_doc: bot.reply_to(message, "Please /start the bot first.")
        else:
             markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update'))
             bot.reply_to(message, 'Please update the bot first.', reply_markup=markup)
        return

    # Check if auction is still marked as active by the global flag
    if bid_ji:
        bot.reply_to(message, "⚠️ The auction appears to be ongoing. This command shows results after bidding closes. Use /mybids for active bids.")
        return

    try:
        # Find bids where user is highest bidder and status is 'closed' (or just highest if bid_ji is False)
        won_bids_cursor = bids_col.find(
            {"highest_bidder_id": user_id_str},
            # Project needed fields
            {"bid_id": 1, "item_name": 1, "current_bid": 1, "owner_mention": 1, "chat_id": 1, "message_id": 1} # Get owner_mention
        ).sort("current_bid", pymongo.DESCENDING)

        won_items = list(won_bids_cursor)

        if not won_items:
            bot.reply_to(message, "❌ You haven't won any items in the concluded auctions yet.")
            return

        # --- Format and Send ---
        text_lines = ["🏆 **Items Won (Auction Concluded):**\n"]
        markup = InlineKeyboardMarkup()
        total_cost = 0

        for item in won_items:
            bid_id = item['bid_id']
            item_name = escape(item.get('item_name', bid_id))
            bid_amount = item.get('current_bid', 0.0)
            total_cost += bid_amount
            bid_amount_display = f"{bid_amount:,.0f}"
            owner_display = item.get('owner_mention', 'Unknown Seller') # Use stored mention

            # Get bid message link
            msg_chat_id = item.get('chat_id')
            msg_message_id = item.get('message_id')
            link = f"https://t.me/c/{str(msg_chat_id)[4:]}/{msg_message_id}" if msg_chat_id and msg_message_id else "#"

            line = (f"• `{bid_id}`: **{item_name}**\n"
                    f"  Bid: `{bid_amount_display}`\n"
                    f"  Seller: {owner_display}\n" # Owner mention is already formatted
                    f"  [View Bid Message]({link})")
            text_lines.append(line)

        total_cost_display = f"{total_cost:,.0f}"
        text_lines.append(f"\n---\n💰 **Total Cost:** `{total_cost_display}`")

        markup.add(InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id}"))

        full_text = "\n\n".join(text_lines)

        # Handle message length limit
        if len(full_text) > 4096:
            full_text = full_text[:4092] + "\n\n... (list truncated)"

        bot.reply_to(message, full_text, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)


    except Exception as e:
        logger.error(f"Error fetching /myphg for {user_id}: {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while fetching your won items.")


@bot.message_handler(commands=['mysold'])
def handle_mysold(message):
    """Shows items sold by the user (where they were owner and someone bid)."""
    user_id = message.from_user.id
    user_id_str = str(user_id)

    user_doc = get_user_doc(user_id)
    if not user_doc or not is_user_updated(user_doc):
        if not user_doc: bot.reply_to(message, "Please /start the bot first.")
        else:
             markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update'))
             bot.reply_to(message, 'Please update the bot first.', reply_markup=markup)
        return

    # Check if auction is still marked as active
    if bid_ji:
        bot.reply_to(message, "⚠️ The auction appears to be ongoing. This command shows results after bidding closes.")
        return

    try:
        # Find bids owned by the user that have a highest bidder (implying sold)
        sold_bids_cursor = bids_col.find(
            {"owner_id": user_id_str, "highest_bidder_id": {"$ne": None}}, # Filter by owner and having a bidder
            # Project fields
            {"bid_id": 1, "item_name": 1, "current_bid": 1, "highest_bidder_mention": 1, "chat_id": 1, "message_id": 1}
        ).sort("current_bid", pymongo.DESCENDING)

        sold_items = list(sold_bids_cursor)

        if not sold_items:
            bot.reply_to(message, "❌ You haven't sold any items in the concluded auctions yet.")
            return

        # --- Format and Send ---
        text_lines = ["🏷️ **Your Sold Items (Auction Concluded):**\n"]
        markup = InlineKeyboardMarkup()
        total_earned = 0

        for item in sold_items:
            bid_id = item['bid_id']
            item_name = escape(item.get('item_name', bid_id))
            bid_amount = item.get('current_bid', 0.0)
            total_earned += bid_amount
            bid_amount_display = f"{bid_amount:,.0f}"
            buyer_mention = item.get('highest_bidder_mention', 'Unknown Buyer') # Already formatted HTML/MD link

            # Get bid message link
            msg_chat_id = item.get('chat_id')
            msg_message_id = item.get('message_id')
            link = f"https://t.me/c/{str(msg_chat_id)[4:]}/{msg_message_id}" if msg_chat_id and msg_message_id else "#"

            line = (f"• `{bid_id}`: **{item_name}**\n"
                    f"  Sold For: `{bid_amount_display}`\n"
                    f"  Buyer: {buyer_mention}\n" # Use mention directly
                    f"  [View Bid Message]({link})")
            text_lines.append(line)

        total_earned_display = f"{total_earned:,.0f}"
        text_lines.append(f"\n---\n📈 **Total Earned:** `{total_earned_display}`")

        markup.add(InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id}"))

        full_text = "\n\n".join(text_lines)

        if len(full_text) > 4096:
            full_text = full_text[:4092] + "\n\n... (list truncated)"
            bot.reply_to(message, full_text, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)
        else:
            bot.reply_to(message, full_text, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error fetching /mysold for {user_id}: {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while fetching your sold items.")


# === Leaderboard and Points ===

@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    """Displays the points leaderboard."""
    try:
        # Fetch top users sorted by points
        leaderboard_cursor = users_col.find(
            {"points": {"$gt": 0}, "is_banned": {"$ne": True}}, # Only non-banned users with points > 0
            {"user_id": 1, "name": 1, "username_tg": 1, "points": 1}
        ).sort("points", pymongo.DESCENDING).limit(20) # Top 20

        leaderboard_data = list(leaderboard_cursor)

        if not leaderboard_data:
            bot.reply_to(message, "No leaderboard data available yet.")
            return

        text = "<b>🏆 Points Leaderboard (Top 20)</b>\n\n"
        for i, user_doc in enumerate(leaderboard_data, start=1):
            points = user_doc.get("points", 0)
            points_display = f"{points:,.0f}" # Format points
            user_display = format_username_html(user_doc) # Use helper
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{rank_emoji} {user_display} — <code>{points_display}</code> pts\n"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Close", callback_data=f"close_{message.from_user.id}"))

        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="html", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error generating leaderboard: {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while generating the leaderboard.")


@bot.message_handler(commands=['removepoints'])
def remove_user_points(message):
    """Admin command to reset points for a specific user."""
    if not is_admin(message.from_user.id):
        bot.reply_to(message,"You are not authorized.")
        return

    args = message.text.split()[1:]
    user_id_to_reset = None

    if message.reply_to_message:
        user_id_to_reset = str(message.reply_to_message.from_user.id)
    elif args:
        user_id_to_reset = get_user_id_from_arg(args[0])
        if not user_id_to_reset:
             bot.reply_to(message, f"Could not find user '{args[0]}'.")
             return
    else:
        bot.reply_to(message, "Reply to a user or provide their User ID / @Username.")
        return

    try:
        result = users_col.update_one(
            {"user_id": user_id_to_reset},
            {"$set": {"points": 0, "notified_5000pts": False}} # Reset points and notification flag
        )
        if result.matched_count > 0 and result.modified_count > 0:
            bot.reply_to(message, f"✅ Points reset to 0 for user `{user_id_to_reset}`.", parse_mode="Markdown")
            logger.info(f"Points reset for {user_id_to_reset} by {message.from_user.id}")
        elif result.matched_count > 0:
             bot.reply_to(message, f"User `{user_id_to_reset}` found, but points were already 0.", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"User `{user_id_to_reset}` not found.", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error resetting points for {user_id_to_reset}: {e}")
        bot.reply_to(message, "An error occurred while resetting points.")


@bot.message_handler(commands=['clearpoints'])
def clear_all_points(message):
    """Admin command to reset points for ALL users."""
    if not is_admin(message.from_user.id):
         bot.reply_to(message,"You are not authorized.")
         return

    markup = InlineKeyboardMarkup().row(
         InlineKeyboardButton("⚠️ YES, Clear ALL Points ⚠️", callback_data="confirm_clear_all_points"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel_clear_points")
    )
    bot.reply_to(message, "🚨 **WARNING!** Are you absolutely sure you want to reset points for **ALL** users to 0?", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_clear_all_points", "cancel_clear_points"])
def handle_clear_points_confirmation(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
         bot.answer_callback_query(call.id, "Unauthorized")
         return

    if call.data == "cancel_clear_points":
         bot.edit_message_text("Point clearing cancelled.", call.message.chat.id, call.message.message_id, reply_markup=None)
         bot.answer_callback_query(call.id, "Cancelled.")
         return

    if call.data == "confirm_clear_all_points":
         try:
             result = users_col.update_many(
                 {}, # Empty filter matches all documents
                 {"$set": {"points": 0, "notified_5000pts": False}}
             )
             bot.edit_message_text(f"✅ All user points ({result.modified_count} users) have been reset to 0.", call.message.chat.id, call.message.message_id, reply_markup=None)
             bot.answer_callback_query(call.id, "All points cleared.")
             logger.warning(f"All user points cleared by {user_id}")
         except Exception as e:
             logger.error(f"Error clearing all points: {e}")
             bot.edit_message_text("❌ An error occurred while clearing points.", call.message.chat.id, call.message.message_id, reply_markup=None)
             bot.answer_callback_query(call.id, "Error clearing points.")


# === Profile Commands ===

@bot.message_handler(commands=["profile"])
def view_profile(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)

    # --- Fetch user data ---
    user_doc = get_user_doc(user_id)
    if not user_doc:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Start Bot', url=f"https://t.me/{bot.get_me().username}?start=start"))
        bot.reply_to(message, "<b>You need to start the bot first.</b>", parse_mode='html', reply_markup=markup)
        return

    if not is_user_updated(user_doc):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f"https://t.me/{bot.get_me().username}?start=update"))
        bot.reply_to(message, "<b>Please update the bot first.</b>", parse_mode='html', reply_markup=markup)
        return

    # --- Get Data for Profile ---
    try:
        template_id = user_doc.get("template_id", 1)
        template_url = TEMPLATES.get(template_id, TEMPLATES[1])

        # User details
        display_name = escape(user_doc.get("name", f"User {user_id_str}"))
        display_username = format_username_html(user_doc) # Already HTML

        # Approved item counts using aggregation
        pipeline = [
            {"$match": {"user_id": user_id_str}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        counts_cursor = approved_items_col.aggregate(pipeline)
        approved_data = {item['_id']: item['count'] for item in counts_cursor}

        # Map DB categories to display names if needed
        shiny = approved_data.get("shiny", 0)
        leg = approved_data.get("legendary", 0)
        nonleg = approved_data.get("non_legendary", 0)
        tm = approved_data.get("tms", 0)
        team = approved_data.get("teams", 0)
        total_approved = sum(approved_data.values())

        # Points
        total_points = user_doc.get("points", 0)
        total_points_display = f"{total_points:,.0f}"


        # --- Construct Message ---
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🎨 Change Card", callback_data=f"ask_template_{user_id_str}"),
            InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id_str}")
        )

        text = (
            f"<b>═══════ User Profile ═══════</b>\n\n"
            f"➤ <b>Name:</b> {display_name}\n"
            f"➤ <b>User:</b> {display_username}\n" # User mention link
            f"➤ <b>User ID:</b> <code>{user_id}</code>\n\n"
            f"<b>📊 Approved Items:</b>\n"
            f"  Shiny: <code>{shiny}</code> | Legendary: <code>{leg}</code>\n"
            f"  Non-Leg: <code>{nonleg}</code> | TMs: <code>{tm}</code> | Teams: <code>{team}</code>\n"
            f"  <b>Total:</b> <code>{total_approved}</code>\n\n"
            f"<b>⭐ Points Summary:</b>\n"
            f"  Auction Points: <code>{total_points_display}</code>\n\n"
            # Remove direct link to image, maybe show thumbnail if possible or just ID
            f"<b>🖼️ Profile Card:</b> #{template_id}\n"
            # f"  <a href='{template_url}'>[Tap to View]</a>\n" # Removed direct link
            f"<b>───────────────────────</b>\n"
        )

        # Send profile text, potentially with the selected template photo
        try:
             bot.send_photo(
                 message.chat.id,
                 photo=template_url, # Send the chosen template photo
                 caption=text,
                 parse_mode="HTML",
                 reply_markup=markup,
             )
        except Exception as photo_err:
             logger.warning(f"Could not send profile photo {template_url} for user {user_id}: {photo_err}")
             # Fallback to sending text only
             bot.send_message(
                 message.chat.id,
                 text,
                 parse_mode="HTML",
                 reply_markup=markup,
                 disable_web_page_preview=True
             )

    except Exception as e:
        logger.error(f"Error in /profile for user {user_id}: {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while loading your profile.")


# Handler for the "Change Card" button
@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_template_"))
def ask_template_change(call):
     user_id_str = call.data.split("_")[-1]
     if str(call.from_user.id) != user_id_str:
         bot.answer_callback_query(call.id, "This button isn't for you.")
         return
     # Edit the profile message to show template options
     send_template_options(int(user_id_str), call.message)
     bot.answer_callback_query(call.id)


# Sends template options, potentially editing an existing message
def send_template_options(user_id, original_message=None):
    """Sends template options to the user in a structured row format."""
    try:
        markup = InlineKeyboardMarkup()
        # Create buttons for each template ID
        buttons = [
            InlineKeyboardButton(f"{tid}", callback_data=f"set_template_{user_id}_{tid}")
            for tid in TEMPLATES
        ]
        # Arrange buttons in rows (e.g., 4 per row)
        rows = [buttons[i:i+4] for i in range(0, len(buttons), 4)]
        for row in rows:
            markup.row(*row)

        markup.add(InlineKeyboardButton("🔙 Cancel Change", callback_data=f"cancel_template_{user_id}")) # Back button

        text_to_send = "🎨 Select a new template for your profile card:"

        if original_message:
             # Edit the profile message (caption of the photo) to show options
             try:
                 bot.edit_message_caption(
                     chat_id=original_message.chat.id,
                     message_id=original_message.message_id,
                     caption=text_to_send,
                     reply_markup=markup
                 )
             except Exception as edit_caption_err:
                  logger.warning(f"Could not edit profile caption for template options: {edit_caption_err}")
                  # If editing caption fails (e.g., original was text only), edit text
                  try:
                      bot.edit_message_text(
                           chat_id=original_message.chat.id,
                           message_id=original_message.message_id,
                           text=text_to_send,
                           reply_markup=markup
                      )
                  except Exception as edit_text_err:
                       logger.error(f"Failed to edit profile message text for template options: {edit_text_err}")
                       # Fallback: Send new message
                       bot.send_message(user_id, text_to_send, reply_markup=markup)

        else:
             # Send as a new message if called directly (e.g., from /setpfp)
             bot.send_message(user_id, text_to_send, reply_markup=markup)

    except Exception as e:
        logger.error(f"Error in send_template_options for user {user_id}: {e}")
        if not original_message: # Only send error if it wasn't an edit attempt
             bot.send_message(user_id, "Error displaying template options.")


# Handler for selecting a template
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_template_"))
def handle_template_selection(call):
    user_id = call.from_user.id
    try:
        parts = call.data.split("_")
        target_user_id = int(parts[2])
        template_id = int(parts[3])

        if user_id != target_user_id:
            bot.answer_callback_query(call.id, "You cannot change this setting for another user.")
            return

        if template_id in TEMPLATES:
            # Update template ID in the database
            result = users_col.update_one(
                {"user_id": str(user_id)},
                {"$set": {"template_id": template_id}}
            )
            if result.matched_count > 0:
                 logger.info(f"User {user_id} selected template {template_id}")
                 bot.answer_callback_query(call.id, f"Template {template_id} selected!", show_alert=False)
                 # Edit the message to confirm and offer to view profile again
                 markup = InlineKeyboardMarkup().row(
                     InlineKeyboardButton("View Updated Profile", callback_data=f"view_profile_again_{user_id}"),
                     InlineKeyboardButton("Close", callback_data=f"close_{user_id}")
                 )
                 new_photo_url = TEMPLATES[template_id]
                 confirmation_caption = f"<b>✅ Template {template_id} selected!</b>"
                 try:
                     # Edit the message media to show the new template photo and confirmation caption
                     bot.edit_message_media(
                          media=types.InputMediaPhoto(new_photo_url, caption=confirmation_caption, parse_mode='HTML'),
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=markup
                     )
                 except Exception as e:
                      logger.warning(f"Could not edit message media for template change: {e}")
                      # Fallback to editing text/caption only
                      try:
                           bot.edit_message_caption(
                                chat_id=call.message.chat.id, message_id=call.message.message_id,
                                caption=confirmation_caption, parse_mode='HTML', reply_markup=markup
                            )
                      except Exception:
                           # If that fails too, just edit the text
                           bot.edit_message_text(
                                chat_id=call.message.chat.id, message_id=call.message.message_id,
                                text=confirmation_caption, parse_mode='HTML', reply_markup=markup
                           )

            else:
                 bot.answer_callback_query(call.id, "Error updating template. User not found?", show_alert=True)
                 logger.error(f"Failed to update template for user {user_id} - user not found in DB.")
        else:
            bot.answer_callback_query(call.id, "Invalid template ID selected.")

    except (IndexError, ValueError):
         logger.error(f"Invalid template callback data: {call.data}")
         bot.answer_callback_query(call.id, "Error processing selection.")
    except Exception as e:
         logger.error(f"Error setting template for user {user_id}: {e}", exc_info=True)
         bot.answer_callback_query(call.id, "An error occurred.")


# Handler for cancelling template selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_template_"))
def cancel_template_selection(call):
    user_id_str = call.data.split("_")[-1]
    if str(call.from_user.id) != user_id_str:
         bot.answer_callback_query(call.id, "This isn't for you.")
         return
    try:
        # Edit message back to the user's profile view
        bot.answer_callback_query(call.id, "Template change cancelled.")
        # Simulate the /profile command to show the profile again
        dummy_message = types.Message(
            message_id = call.message.message_id, # Use original message ID for context
            from_user = call.from_user,
            date = int(time.time()),
            chat = call.message.chat,
            content_type = 'text', options = {}, json_string = ""
        )
        view_profile(dummy_message) # Call the profile handler
        # Try deleting the now-redundant template selection message? Risky if view_profile fails.
        # Let view_profile replace the content instead.
    except Exception as e:
         logger.error(f"Error cancelling template selection: {e}")
         bot.answer_callback_query(call.id) # Still acknowledge


# Callback to re-trigger profile view after template set
@bot.callback_query_handler(func=lambda call: call.data.startswith("view_profile_again_"))
def handle_view_profile_again(call):
     user_id_str = call.data.split("_")[-1]
     if str(call.from_user.id) != user_id_str:
          bot.answer_callback_query(call.id, "This isn't for you.")
          return
     # Simulate the /profile command for the user
     # Create a dummy message object to pass to view_profile
     dummy_message = types.Message(
          message_id = call.message.message_id, # Use original message ID
          from_user = call.from_user,
          date = int(time.time()),
          chat = call.message.chat,
          content_type = 'text', options = {}, json_string = ""
     )
     view_profile(dummy_message) # Call the profile handler to replace the current message content
     bot.answer_callback_query(call.id)


# Command to initiate changing profile card (calls send_template_options)
@bot.message_handler(commands=["setpfp", "changecard"]) # Added alias
def set_profile_pic(message):
    user_id = message.from_user.id

    user_doc = get_user_doc(user_id)
    if not user_doc:
        markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Start Bot',url=f'https://t.me/{bot.get_me().username}?start=start'))
        bot.reply_to(message, '<blockquote><b>Start the bot first.</b></blockquote>', parse_mode='html',reply_markup=markup,disable_web_page_preview=True)
        return

    if not is_user_updated(user_doc):
        markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot',url=f'https://t.me/{bot.get_me().username}?start=update'))
        bot.reply_to(message, '<blockquote><b>Update the bot first.</b></blockquote>', parse_mode='html',reply_markup=markup,disable_web_page_preview=True)
        return

    if message.chat.type == 'private':
        # Send options directly in private chat
        send_template_options(user_id)
    else:
        # Ask user to go to PM
         bot.reply_to(message, "Please use this command in our private chat to change your profile card.",
                      reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🎨 Change Card in PM",url=f"https://t.me/{bot.get_me().username}?start=profile"))) # Deep link to profile setting


# === Bot Control Commands ===

@bot.message_handler(commands=['sub'])
def subon(message):
    """Admin command to enable/disable item submissions."""
    global sub_process
    if not is_mod(message.from_user.id):
        bot.send_sticker(message.chat.id, ANGRY_STICKER_ID)
        bot.reply_to(message, "You are not authorised to use this.")
        return

    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ['on', 'off']:
        current_status = "ON" if sub_process else "OFF"
        bot.reply_to(message, f"Usage: /sub <on|off>\nCurrent status: {current_status}")
        return

    action = args[1].lower()
    if action == 'on':
        sub_process = True
        bot.reply_to(message, '✅ Submissions are now **ENABLED**.')
        logger.info(f"Submissions ENABLED by {message.from_user.id}")
    elif action == 'off':
        sub_process = False
        bot.reply_to(message, '❌ Submissions are now **DISABLED**.')
        logger.info(f"Submissions DISABLED by {message.from_user.id}")


@bot.message_handler(commands=['bid'])
def biddy(message):
    """Admin command to enable/disable bidding."""
    global bid_ji
    if not is_mod(message.from_user.id):
        bot.send_sticker(message.chat.id, ANGRY_STICKER_ID)
        bot.reply_to(message, "You are not authorised to use this.")
        return

    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ['on', 'off']:
        current_status = "ON" if bid_ji else "OFF"
        bot.reply_to(message, f"Usage: /bid <on|off>\nCurrent status: {current_status}")
        return

    action = args[1].lower()
    if action == 'on':
        if bid_ji:
             bot.reply_to(message, 'ℹ️ Bidding is already **ENABLED**.')
             return
        bid_ji = True
        bot.reply_to(message, '✅ Bidding is now **ENABLED**.')
        logger.info(f"Bidding ENABLED by {message.from_user.id}")
        # Optionally, find all bids with status 'closed' and reopen them? Complex.
        # Maybe just announce in channel?
        try: bot.send_message(POST_CHANNEL, "--- Bidding is now OPEN ---")
        except: pass
    elif action == 'off':
        if not bid_ji:
             bot.reply_to(message, 'ℹ️ Bidding is already **DISABLED**.')
             return
        bid_ji = False
        bot.reply_to(message, '❌ Bidding is now **DISABLED**. Active auctions are closing.')
        logger.info(f"Bidding DISABLED by {message.from_user.id}")
        # Mark all 'active' bids as 'closed' in DB
        try:
             close_result = bids_col.update_many(
                 {"status": "active"},
                 {"$set": {"status": "closed", "closed_time": datetime.datetime.utcnow()}}
             )
             logger.info(f"Marked {close_result.modified_count} active bids as closed.")
             # Announce in channel
             try: bot.send_message(POST_CHANNEL, "--- Bidding is now CLOSED ---")
             except: pass
             # Send final results? Maybe trigger /myphg and /mysold messages? Complex.
        except Exception as e:
             logger.error(f"Error marking bids as closed: {e}")


# === Update Command ===
@bot.message_handler(commands=['update'])
def update_prompt(message):
    """Prompts the user to update their bot version status."""
    user_id = message.from_user.id
    user_id_str = str(user_id)

    # Check if user exists, no need to prompt if they haven't started
    user_doc = get_user_doc(user_id)
    if not user_doc:
         markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Start Bot',url=f'https://t.me/{bot.get_me().username}?start=start'))
         bot.reply_to(message, 'Please /start the bot first.', reply_markup=markup)
         return

    if message.chat.type != 'private':
        bot.reply_to(
            message,
            "✨ Please click the button below to update the bot in our private chat! ⚙️",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('🔄 Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update')
            )
        )
        return

    # Check if already updated
    if is_user_updated(user_doc):
        bot.send_message(message.chat.id, "✅ You are already using the latest version!")
        return

    # Send update prompt with button
    # --- GET A NEW FILE ID FOR THIS IMAGE ---
    # 1. Send the image to your bot in a private chat.
    # 2. Reply to the image with /getid
    # 3. Copy the file_id the bot gives you and paste it below.
    pic = 'BQACAgUAAyEFAASF0gJtAAK5RmgQzq7bEA7XST2uwVQKCQyCpTp_AAIxFQACyVWAVC7JzctAQeinNgQ' # <--- UPDATE THIS
    text = "✨ A new version of the bot is available! Click below to update your profile and access the latest features! 🛠️"
    chat_id = message.chat.id
    # user_id_str is already defined above

    try:
        bot.send_photo(
            chat_id,
            photo=pic,
            caption=text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('🔄 Update Now', callback_data=f'confirm_update_{user_id_str}')
            )
        )
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Failed to send update prompt photo (ID: {pic}): {e}. Sending text fallback.")
        # Fallback to text message if photo sending fails
        bot.send_message(
            chat_id,
            text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('🔄 Update Now', callback_data=f'confirm_update_{user_id_str}')
            )
        )
    except Exception as e:
         logger.error(f"Unexpected error sending update prompt for user {user_id_str}: {e}")
         bot.send_message(chat_id, "An error occurred trying to show the update prompt. Please try clicking the update button again if you see one, or use /start.")
         
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_update_"))
def handle_confirm_update(call):
    """Handles the confirmation to update the user's version."""
    user_id = call.from_user.id
    user_id_str = str(user_id)
    target_user_id = call.data.split("_")[-1]

    if user_id_str != target_user_id:
        bot.answer_callback_query(call.id, "This button isn't for you.")
        return

    # Fetch user doc again to be sure
    user_doc = get_user_doc(user_id)
    if not user_doc:
         bot.answer_callback_query(call.id, "Error: User not found.", show_alert=True)
         return

    # Check if already updated between prompt and click
    if is_user_updated(user_doc):
        bot.answer_callback_query(call.id, "You are already updated!", show_alert=True)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: pass
        return

    # Perform the update in the database
    try:
        # Fetch user's current TG info again for freshness
        try:
             user_info = bot.get_chat(user_id)
             full_name = user_info.full_name
             username_tg = f"@{user_info.username}" if user_info.username else ""
             first_name = user_info.first_name
        except Exception as e:
             logger.warning(f"Could not fetch user info during update for {user_id}: {e}. Using DB data.")
             full_name = user_doc.get("name", f"User {user_id}")
             username_tg = user_doc.get("username_tg", "")
             first_name = user_doc.get("first_name", "")


        update_result = users_col.update_one(
            {"user_id": user_id_str},
            {"$set": {
                "version": CURRENT_BOT_VERSION,
                "name": full_name, # Update name/username on update too
                "username_tg": username_tg,
                "first_name": first_name,
                "last_updated": datetime.datetime.utcnow()
                }
            }
        )

        if update_result.modified_count > 0:
            logger.info(f"User {user_id_str} updated to version {CURRENT_BOT_VERSION}")
            bot.answer_callback_query(call.id, "Update successful!")
            # Send confirmation visual
            try:
                 bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass # Ignore if delete fails

            # --- GET A NEW FILE ID FOR THIS IMAGE ---
            # 1. Send the image to your bot in a private chat.
            # 2. Reply to the image with /getid
            # 3. Copy the file_id the bot gives you and paste it below.
            confirmation_pic = 'AgACAgUAAyEFAASF0gJtAAK5QmgQzlxgiBxajyIfdE7U830rp8HYAAI8yTEbyVWAVK73PbcTz-lkAQADAgADeQADNgQ' # <--- UPDATE THIS
            confirmation_caption = "🎉 Bot update complete! ✅\nYou can now enjoy the latest features! 🚀"
            confirmation_markup = InlineKeyboardMarkup().add(
                     InlineKeyboardButton('🌐 Join Trade Group', url='https://t.me/phg_hexa')
                 )

            try:
                bot.send_photo(
                     call.message.chat.id,
                     photo=confirmation_pic,
                     caption=confirmation_caption,
                     reply_markup=confirmation_markup
                 )
            except telebot.apihelper.ApiTelegramException as e:
                 logger.error(f"Failed to send update confirmation photo (ID: {confirmation_pic}): {e}. Sending text fallback.")
                 # Fallback to text message if photo fails
                 bot.send_message(
                      call.message.chat.id,
                      confirmation_caption,
                      reply_markup=confirmation_markup
                 )
            except Exception as e:
                  logger.error(f"Unexpected error sending update confirmation for user {user_id_str}: {e}")


        else:
            # This case means the user doc exists but wasn't modified (maybe already updated?)
            bot.answer_callback_query(call.id, "You seem to be already updated.", show_alert=True)
            logger.warning(f"Update triggered for user {user_id_str} but DB was not modified.")
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass


    except Exception as e:
         logger.error(f"Error updating user {user_id_str} version: {e}", exc_info=True)
         bot.answer_callback_query(call.id, "An error occurred during the update.", show_alert=True)

# === Utility & Info Commands ===

@bot.message_handler(commands=['getid'])
def get_file_id(message):
    """Replies with the file_id of a replied-to photo or sticker."""
    if not message.reply_to_message:
        bot.reply_to(message, "Please reply to a sticker or photo to get its ID.")
        return

    replied = message.reply_to_message
    file_id = None
    file_type = None
    file_unique_id = None

    if replied.sticker:
        file_id = replied.sticker.file_id
        file_unique_id = replied.sticker.file_unique_id
        file_type = "Sticker"
    elif replied.photo:
        # Photos have multiple sizes, get the highest resolution one (last in list)
        file_id = replied.photo[-1].file_id
        file_unique_id = replied.photo[-1].file_unique_id
        file_type = "Photo"
    elif replied.animation:
        file_id = replied.animation.file_id
        file_unique_id = replied.animation.file_unique_id
        file_type = "Animation (GIF)"
    elif replied.video:
         file_id = replied.video.file_id
         file_unique_id = replied.video.file_unique_id
         file_type = "Video"
    elif replied.document: # Some images/gifs might be sent as documents
         file_id = replied.document.file_id
         file_unique_id = replied.document.file_unique_id
         file_type = f"Document ({replied.document.mime_type})"

    if file_id:
        response = f"<b>{file_type} ID:</b>\n<code>{escape(file_id)}</code>"
        if file_unique_id:
             response += f"\n\n<b>File Unique ID:</b>\n<code>{escape(file_unique_id)}</code>"
        bot.reply_to(message, response, parse_mode='HTML')
    else:
        bot.reply_to(message, "Could not find a file ID in the replied message. Please reply to a sticker, photo, GIF, or video.")


@bot.message_handler(commands=['brules'])
def prules(msg):
    """Displays the bidding rules."""
    text = """
<b>📜 Bidding Rules</b>

➡️ **Minimum Bid Increments:**
   • ≤ 30k: min +1k (<code>1000</code>)
   • ≤ 60k: min +2k (<code>2000</code>)
   • ≤ 100k: min +3k (<code>3000</code>)
   • > 100k: min +4k (<code>4000</code>)

➡️ **Bid Removal Penalty:** Removing your confirmed bid requires paying a fine (40% of your bid) to admins. Contact an admin to request removal.

➡️ **Group Membership:** You **MUST** be a member of both the <a href="https://t.me/phg_pokes">Auction Channel</a> and the <a href="https://t.me/phg_hexa">Trade Group</a> for your bids to be valid.

➡️ **Issues:** If you encounter problems, tag an admin in the trade group or use /report command here.
"""
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton('❌ Close', callback_data=f'close_{msg.from_user.id}'))
    bot.reply_to(msg, text, reply_markup=markup, parse_mode='html', disable_web_page_preview=True)


@bot.message_handler(commands=['subrules'])
def subrule(msg):
    """Displays the submission rules."""
    text = """
<b>📜 Submission Rules</b>

➡️ **Cancellation (During Auction):** If you cancel your submitted item *after* it has been approved and bidding has started, you pay a fine: 80% of the highest bid to the highest bidder, and 10% to admins. Contact an admin to request cancellation.

➡️ **Buyer Failure:** If the highest bidder fails to complete the purchase after the auction ends, they pay a fine: 20% of their bid to admins, and 50% to the seller.

➡️ **Cancellation (Pending):** Items can be cancelled for free while they are still pending approval (before being posted to the auction). Use /report replying to your submission preview message to request cancellation.

➡️ **Item Hold Limit:** If your item remains pending for more than 5 hours without admin action, please use /report replying to your submission preview message to inquire.

➡️ **Group Membership:** Ensure you are in the <a href="https://t.me/phg_pokes">Auction Channel</a> and <a href="https://t.me/phg_hexa">Trade Group</a>.
"""
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton('❌ Close', callback_data=f'close_{msg.from_user.id}'))
    bot.reply_to(msg, text, reply_markup=markup, parse_mode='html', disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith("close_"))
def closed(call):
    """Handles the 'Close' button on various messages."""
    try:
        target_user_id = int(call.data.split("_")[1])
        # Allow closing only if the clicker is the target user or an admin
        if call.from_user.id == target_user_id or is_mod(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id) # Acknowledge silently
        else:
            bot.answer_callback_query(call.id, "This button isn't for you.")
    except (IndexError, ValueError):
         bot.answer_callback_query(call.id, "Error processing close action.")
    except Exception as e:
        # Ignore if message already deleted etc.
        logger.debug(f"Minor error closing message: {e}")
        bot.answer_callback_query(call.id)


@bot.message_handler(commands=['report'])
def report_command(msg):
    """Allows users to report a message (e.g., pending item, rule violation) to admins."""
    user_id = msg.from_user.id
    chat_id = msg.chat.id

    if not msg.reply_to_message:
        bot.reply_to(msg, "⚠️ Please reply to the message you want to report (e.g., your pending submission, a problematic bid).")
        return

    # Get details about the message being replied to
    replied_msg = msg.reply_to_message
    replied_msg_link = f"https://t.me/c/{str(replied_msg.chat.id)[4:]}/{replied_msg.message_id}" if replied_msg.chat.id < 0 else f"https://t.me/{replied_msg.chat.username}/{replied_msg.message_id}" if replied_msg.chat.username else "#" # Link to the message being reported
    preview_text = replied_msg.text[:50] if replied_msg.text else replied_msg.caption[:50] if replied_msg.caption else "[Media]"


    # Ask for confirmation
    markup = InlineKeyboardMarkup().row(
        InlineKeyboardButton("✅ Confirm Report", callback_data=f"confir_report:{replied_msg.message_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data="cance_report")
    )
    bot.reply_to(
        msg,
        f"📝 Are you sure you want to report the replied-to message?\n"
        f"Preview: \"<i>{escape(preview_text)}...</i>\"\n"
        f"<a href='{replied_msg_link}'>[Link to Message]</a>",
        reply_markup=markup,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("confir_report:") or call.data == "cance_report")
def handle_report_confirmation(call):
    """Handles the confirmation for the /report command."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id # ID of the confirmation message
    user_id = call.from_user.id

    if call.data == "cance_report":
        bot.answer_callback_query(call.id, "❌ Report canceled.")
        try: bot.delete_message(chat_id, message_id)
        except Exception: pass
        return

    # Handle confirmed report
    try:
        reported_message_id = int(call.data.split(":")[1])

        # Prepare report content
        reporter_user_info = call.from_user
        reporter_mention = f"[{escape(reporter_user_info.full_name)}](tg://user?id={user_id})"
        report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Link to the original command message that triggered the report
        # The confirmation message replies to the /report command message
        original_command_link = f"https://t.me/c/{str(chat_id)[4:]}/{call.message.reply_to_message.message_id}" if chat_id < 0 else "#"

        # We already generated the link to the reported message in report_command
        # Try to get it from the confirmation message text if possible
        reported_message_link = "#"
        if call.message.html_text:
             link_match = re.search(r'<a href=["\'](.*?)["\']>\[Link to Message\]</a>', call.message.html_text)
             if link_match:
                 reported_message_link = link_match.group(1)


        report_text = (
            f"🚨 **New Report** 🚨\n\n"
            f"👤 **Reported By:** {reporter_mention} (`{user_id}`)\n"
            f"🕒 **Time:** {report_time}\n"
            f"🔗 **Report Context:** [Link to /report command]({original_command_link})\n"
            f"🔗 **Reported Message:** [Link]({reported_message_link})\n\n"
            f"👇 Forwarded message below:"
        )

        # Send the info text to the admin channel
        bot.send_message(APPROVE_CHANNEL, report_text, parse_mode="Markdown", disable_web_page_preview=True)
        # Forward the reported message itself
        bot.forward_message(APPROVE_CHANNEL, chat_id, reported_message_id)

        bot.answer_callback_query(call.id, "✅ Report sent successfully.", show_alert=True)
        logger.info(f"Report submitted by {user_id} regarding message {reported_message_id} in chat {chat_id}")

    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "⚠️ Invalid report data.")
        logger.error(f"Invalid report callback data: {call.data}")
    except Exception as e:
        bot.answer_callback_query(call.id, "⚠️ Failed to send the report.")
        logger.error(f"Error in reporting process: {e}", exc_info=True)

    # Delete the confirmation message ("Are you sure...")
    try: bot.delete_message(chat_id, message_id)
    except Exception: pass


# === Info Command ===

@bot.message_handler(commands=['info'])
def info_command(message):
    """Provides info about an active auction item by its name or Bid ID."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Please provide an item name or Bid ID.\nUsage: `/info Charizard` or `/info P123`", parse_mode="Markdown")
        return

    query = args[1].strip()
    query_lower = query.lower()
    query_upper_bid = query.upper() if query.startswith(('P', 'p')) else query # For Bid ID matching

    try:
        # Search active bids by item name (case-insensitive partial match) or exact Bid ID
        search_condition = {
            "status": "active",
            "$or": [
                 {"item_name": {"$regex": re.escape(query_lower), "$options": "i"}}, # Case-insensitive substring search
                 {"bid_id": query_upper_bid} # Match bid ID like P123
            ]
        }
        # Project fields needed for display
        projection = {
            "bid_id": 1, "item_name": 1, "current_bid": 1,
            "highest_bidder_mention": 1, "auction_post_link": 1,
            "chat_id": 1, "message_id": 1
        }
        matches_cursor = bids_col.find(search_condition, projection).limit(10) # Limit results
        matches = list(matches_cursor)

        if not matches:
            bot.reply_to(message, f"❌ No active auction found matching *{escape(query)}*.", parse_mode="Markdown")
            return

        # --- Format Results ---
        text_lines = [f"🔍 Found active auction(s) for **{escape(query)}**:\n"]
        markup = InlineKeyboardMarkup()

        for match in matches:
            bid_id = match['bid_id']
            item_name = escape(match.get('item_name', bid_id))
            current_bid = match.get('current_bid', 0.0)
            current_bid_display = f"{current_bid:,.0f}"
            highest_bidder = match.get('highest_bidder_mention', 'None') # Already formatted

            # Get links
            bid_message_link = "#"
            main_post_link = match.get('auction_post_link', '#')
            msg_chat_id = match.get('chat_id')
            msg_message_id = match.get('message_id')
            if msg_chat_id and msg_message_id:
                 bid_message_link = f"https://t.me/c/{str(msg_chat_id)[4:]}/{msg_message_id}"

            line = (
                f"🔹 **{item_name}** (`{bid_id}`)\n"
                f"   Current Bid: `{current_bid_display}`\n"
                f"   Highest Bidder: {highest_bidder}\n"
                f"   [View Main Post]({main_post_link}) | [View Bid Section]({bid_message_link})"
            )
            text_lines.append(line)

            # Add button linking to bid section
            markup.add(InlineKeyboardButton(f"View Bid: {item_name} ({bid_id})", url=bid_message_link))

        markup.add(InlineKeyboardButton("❌ Close", callback_data=f"close_{message.from_user.id}"))

        full_text = "\n\n".join(text_lines)
        if len(full_text) > 4096: full_text = full_text[:4092] + "\n..."

        bot.reply_to(message, full_text, reply_markup=markup, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error during /info command for query '{query}': {e}", exc_info=True)
        bot.reply_to(message, "An error occurred while searching.")


# === Item List Command (/elements) ===

@bot.message_handler(commands=['elements'])
def send_elements_menu(message):
    """Sends the main menu to browse items by category."""
    user_id = message.from_user.id
    user_doc = get_user_doc(user_id) # Check if user started/updated
    if not user_doc:
        bot.reply_to(message, "Please /start the bot first.")
        return
    if not is_user_updated(user_doc):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton('Update Bot', url=f'https://t.me/{bot.get_me().username}?start=update'))
        bot.reply_to(message, 'Please update the bot first.', reply_markup=markup)
        return

    # Send the category selection menu
    elements_items_list_menu(message.chat.id, msg_id_to_reply=message.message_id)


def elements_items_list_menu(chat_id, msg_id_to_reply=None, edit_message_id=None):
    """Sends or edits the message showing item categories."""
    photo = 'AgACAgUAAxkBAAK05Gfr-uNsVdnN4KeINoEaoJ_hWU34AAKexTEbqB5gV8XdQ3I27heCAQADAgADeAADNgQ' # Your existing photo ID
    text = "📦 Browse Auction Items by Category:"
    markup = types.InlineKeyboardMarkup(row_width=3) # Adjust row width as needed
    markup.add(
            types.InlineKeyboardButton('6ls⚡️', callback_data='listcat_legendary'),
            types.InlineKeyboardButton('0ls🌪', callback_data='listcat_non_legendary'),
            types.InlineKeyboardButton('Shiny✨', callback_data='listcat_shiny')
    )
    markup.add(
            types.InlineKeyboardButton('TMs💿', callback_data='listcat_tms'),
            types.InlineKeyboardButton('Teams🎯', callback_data='listcat_teams'),
            types.InlineKeyboardButton('❌ Close', callback_data=f'close_{chat_id if chat_id > 0 else 0}') # Use 0 if group chat
        )

    try:
        if edit_message_id:
             bot.edit_message_caption(chat_id=chat_id, message_id=edit_message_id, caption=text, reply_markup=markup)
        else:
             # Send as a new message, possibly replying
             send_params = {
                 "chat_id": chat_id, "photo": photo, "caption": text, "reply_markup": markup
             }
             if msg_id_to_reply: send_params["reply_to_message_id"] = msg_id_to_reply
             bot.send_photo(**send_params)
    except Exception as e:
        logger.error(f"Error sending/editing elements menu: {e}")
        if not edit_message_id: # Send plain text if photo send failed
             try:
                 bot.send_message(chat_id, text, reply_markup=markup)
             except Exception as send_text_err:
                 logger.error(f"Failed even sending text for elements menu: {send_text_err}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('listcat_'))
def handle_list_category(call):
    """Handles category selection from the /elements menu."""
    # Map category keys to display names and check if nature should be shown
    category_map = {
        'legendary': {'display': 'Legendary', 'show_nature': True},
        'non_legendary': {'display': 'Non-Legendary', 'show_nature': True},
        'shiny': {'display': 'Shiny', 'show_nature': True},
        'tms': {'display': 'TMs', 'show_nature': False},
        'teams': {'display': 'Teams', 'show_nature': False},
    }

    category_key = call.data.split('_', 1)[1]
    if category_key not in category_map:
        logger.warning(f"Unknown category key received in listcat: {category_key}")
        bot.answer_callback_query(call.id, "Unknown category.")
        return

    category_info = category_map[category_key]
    category_display = category_info['display']
    show_nature = category_info['show_nature']

    chat_id = call.message.chat.id
    message_id = call.message.message_id
    original_message = call.message

    try:
        # --- Fetch items ---
        # Project the 'nature' field ONLY if needed for this category
        projection = {"item_name": 1, "bid_id": 1, "chat_id": 1, "message_id": 1}
        if show_nature:
            projection["nature"] = 1 # Add nature to projection

        items_cursor = bids_col.find(
            {"status": "active", "item_type": category_key},
            projection # Use the dynamic projection
        ).limit(50)
        items_list = list(items_cursor)

        if not items_list:
            text = f"😕 No active **{category_display}** items found in the auction right now."
        else:
            text = f"🔎 Active **{category_display}** items:\n\n"
            item_lines = []
            for item in items_list:
                name = escape(item.get('item_name', item.get('bid_id', 'N/A')))
                bid_id = item.get('bid_id', 'N/A')
                nature = escape(item.get('nature', '')) if show_nature else '' # Get nature if applicable

                # Construct display string with or without nature
                display_string = name
                if nature: # Add nature in parentheses if it exists
                    display_string += f" ({nature})"

                # Create link to bid message
                msg_chat_id = item.get('chat_id')
                msg_message_id = item.get('message_id')
                link = f"https://t.me/c/{str(msg_chat_id)[4:]}/{msg_message_id}" if msg_chat_id and msg_message_id else "#"

                item_lines.append(f"• [{display_string} (`{bid_id}`)]({link})") # Updated line format

            text += "\n".join(item_lines)

        # --- Navigation buttons (Keep existing logic) ---
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔙 Back to Categories', callback_data='back_to_elements_menu'))
        markup.add(types.InlineKeyboardButton('❌ Close', callback_data=f'close_{call.from_user.id}'))

        # Ensure text length limit for caption/text
        max_len = 1024 if original_message.content_type == 'photo' else 4096
        if len(text) > max_len: text = text[:max_len - 4] + "\n..."

        # --- EDITING LOGIC (Keep existing improved logic) ---
        try:
            if original_message.content_type == 'photo':
                 bot.edit_message_caption(
                     chat_id=chat_id, message_id=message_id, caption=text,
                     reply_markup=markup, parse_mode='Markdown'
                 )
                 logger.info(f"Edited caption for category list {category_key}")
            else:
                 bot.edit_message_text(
                      chat_id=chat_id, message_id=message_id, text=text,
                      reply_markup=markup, parse_mode='Markdown', disable_web_page_preview=True
                 )
                 logger.info(f"Edited text for category list {category_key}")
        except telebot.apihelper.ApiTelegramException as e:
            if "there is no caption in the message to edit" in str(e):
                 logger.warning(f"Attempted to edit caption on text msg for {category_key}. Trying edit_text.")
                 try:
                      bot.edit_message_text(
                           chat_id=chat_id, message_id=message_id, text=text,
                           reply_markup=markup, parse_mode='Markdown', disable_web_page_preview=True
                      )
                      logger.info(f"Edited text (fallback) for category list {category_key}")
                 except Exception as text_edit_err:
                      logger.error(f"Failed fallback text edit for category {category_key}: {text_edit_err}")
            elif "message is not modified" in str(e):
                 logger.debug(f"Category list message for {category_key} was not modified.")
            else:
                 logger.error(f"Failed to edit category list message for {category_key}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error editing category list for {category_key}: {e}", exc_info=True)

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Error listing category {category_key}: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error fetching items.")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_elements_menu')
def handle_back_to_elements_menu(call):
     """Handles the 'Back to Categories' button."""
     # Edit the message back to the main category menu
     elements_items_list_menu(call.message.chat.id, edit_message_id=call.message.message_id)
     bot.answer_callback_query(call.id)


# === Reset Commands (Admin Only) ===

@bot.message_handler(commands=['resetd'])
def reset_bid_data(message):
    """Admin: Clears ALL bid data and resets the bid counter."""
    if not is_admin(message.from_user.id): # Make this owner/admin only
        bot.reply_to(message, "❌ Unauthorized. Only Bot Admins.")
        return

    markup = InlineKeyboardMarkup().row(
         InlineKeyboardButton("⚠️ YES, Clear ALL Bids ⚠️", callback_data="confirm_reset_bids"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel_reset_bids")
    )
    bot.reply_to(message, "🚨 **DANGER ZONE!** This will delete ALL active and past bid information AND reset the Bid ID counter (P1, P2...). This is irreversible. Are you absolutely sure?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_reset_bids", "cancel_reset_bids"])
def handle_reset_bids_confirmation(call):
    user_id = call.from_user.id
    if not is_admin(user_id): # Make this owner/admin only
         bot.answer_callback_query(call.id, "Unauthorized")
         return

    if call.data == "cancel_reset_bids":
         bot.edit_message_text("Bid data reset cancelled.", call.message.chat.id, call.message.message_id, reply_markup=None)
         bot.answer_callback_query(call.id, "Cancelled.")
         return

    if call.data == "confirm_reset_bids":
         try:
             # Delete all documents from the bids collection
             delete_result = bids_col.delete_many({})
             # Reset the counter in the config collection
             config_col.update_one({"_id": "bid_counter"}, {"$set": {"value": 0}}, upsert=True)

             bot.edit_message_text(f"✅ All bid data cleared ({delete_result.deleted_count} documents removed) and counter reset to 0.", call.message.chat.id, call.message.message_id, reply_markup=None)
             bot.answer_callback_query(call.id, "All bid data cleared.")
             logger.warning(f"All bid data cleared by {user_id}")
         except Exception as e:
             logger.error(f"Error resetting bid data: {e}")
             bot.edit_message_text("❌ An error occurred while clearing bid data.", call.message.chat.id, call.message.message_id, reply_markup=None)
             bot.answer_callback_query(call.id, "Error clearing data.")


@bot.message_handler(commands=['reseti'])
def reset_item_lists(message):
    """Admin: Clears approved and pending item lists."""
    if not is_admin(message.from_user.id): # Make this owner/admin only
        bot.reply_to(message, "❌ Unauthorized. Only Bot Admins.")
        return

    markup = InlineKeyboardMarkup().row(
         InlineKeyboardButton("⚠️ YES, Clear Items ⚠️", callback_data="confirm_reset_items"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel_reset_items")
    )
    bot.reply_to(message, "🚨 **DANGER ZONE!** This will delete ALL approved and pending item records. This does NOT delete auction posts or bids, but breaks links from `/myitems` etc. Are you sure?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_reset_items", "cancel_reset_items"])
def handle_reset_items_confirmation(call):
    user_id = call.from_user.id
    if not is_admin(user_id): # Make this owner/admin only
         bot.answer_callback_query(call.id, "Unauthorized")
         return

    if call.data == "cancel_reset_items":
         bot.edit_message_text("Item list reset cancelled.", call.message.chat.id, call.message.message_id, reply_markup=None)
         bot.answer_callback_query(call.id, "Cancelled.")
         return

    if call.data == "confirm_reset_items":
        try:
            approved_deleted = approved_items_col.delete_many({})
            pending_deleted = pending_items_col.delete_many({})

            bot.edit_message_text(f"✅ Cleared {approved_deleted.deleted_count} approved items and {pending_deleted.deleted_count} pending items.", call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "Item lists cleared.")
            logger.warning(f"Approved and pending item lists cleared by {user_id}")
        except Exception as e:
            logger.error(f"Error resetting item lists: {e}")
            bot.edit_message_text("❌ An error occurred while clearing item lists.", call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "Error clearing lists.")


@bot.message_handler(commands=["remo"])
def remove_auction_item(message):
    """Admin: Removes an active auction item by its Bid ID (e.g., /remo P123)."""
    if not is_mod(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized.")
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage: `/remo <bid_id>` (e.g., `/remo P123`)")
        return

    bid_id_to_remove = args[1].strip().upper() # Ensure consistent format

    try:
        # Find the bid document to get message IDs and link
        bid_doc = bids_col.find_one({"bid_id": bid_id_to_remove})

        if not bid_doc:
            bot.reply_to(message, f"❌ No auction found with Bid ID: `{bid_id_to_remove}`")
            return

        item_name = escape(bid_doc.get("item_name", bid_id_to_remove))
        item_status = bid_doc.get("status", "unknown")
        main_post_link = bid_doc.get('auction_post_link') # Get link for approved_items deletion

        deleted_bid_msg = False
        deleted_post_msg = False

        # --- Delete Messages ---
        # 1. Delete the bid status message
        bid_msg_chat_id = bid_doc.get('chat_id')
        bid_msg_id = bid_doc.get('message_id')
        if bid_msg_chat_id and bid_msg_id:
            try:
                bot.delete_message(bid_msg_chat_id, bid_msg_id)
                logger.info(f"Deleted bid message {bid_msg_id} for {bid_id_to_remove}")
                deleted_bid_msg = True
            except Exception as e:
                logger.warning(f"Could not delete bid message {bid_msg_id} for {bid_id_to_remove}: {e}")
        else:
             logger.warning(f"Missing chat/message ID for bid message of {bid_id_to_remove}")


        # 2. Delete the main item post message (using link)
        if main_post_link and main_post_link != '#':
            try:
                link_parts = main_post_link.split('/')
                post_msg_id = int(link_parts[-1])
                post_chat_id_str = link_parts[-2]
                post_chat_id = int(f"-100{post_chat_id_str}")
                bot.delete_message(post_chat_id, post_msg_id)
                logger.info(f"Deleted main post message {post_msg_id} for {bid_id_to_remove}")
                deleted_post_msg = True
            except Exception as e:
                logger.warning(f"Could not delete main post message for {bid_id_to_remove} from link {main_post_link}: {e}")
        else:
             logger.warning(f"Missing or invalid auction_post_link for {bid_id_to_remove}")


        # --- Delete Database Records ---
        # 3. Delete the bid document itself
        bids_delete_result = bids_col.delete_one({"bid_id": bid_id_to_remove})

        # 4. Delete from approved_items collection (using the link)
        approved_delete_result = approved_items_col.delete_one({"link": main_post_link}) if main_post_link else None

        # --- Notify Admin ---
        admin_msg = f"✅ Attempted removal of auction **{item_name}** (`{bid_id_to_remove}`) by @{message.from_user.username}.\n"
        if deleted_bid_msg: admin_msg += "- Bid message deleted.\n"
        else: admin_msg += "- Bid message NOT deleted (error or missing ID).\n"
        if deleted_post_msg: admin_msg += "- Main post deleted.\n"
        else: admin_msg += "- Main post NOT deleted (error or missing link).\n"
        if bids_delete_result.deleted_count > 0: admin_msg += "- Bid DB record deleted.\n"
        else: admin_msg += f"- Bid DB record NOT deleted (status was '{item_status}').\n"
        if approved_delete_result and approved_delete_result.deleted_count > 0: admin_msg += "- Approved item DB record deleted.\n"
        elif main_post_link: admin_msg += "- Approved item DB record NOT deleted (or not found).\n"

        bot.reply_to(message, admin_msg, parse_mode="Markdown")
        logger.info(f"Auction {bid_id_to_remove} removal process executed by {message.from_user.id}. Success flags - BidMsg: {deleted_bid_msg}, PostMsg: {deleted_post_msg}, BidDB: {bids_delete_result.deleted_count>0}, ApprovedDB: {approved_delete_result.deleted_count>0 if approved_delete_result else False}")


    except Exception as e:
        logger.error(f"Error removing item {bid_id_to_remove}: {e}", exc_info=True)
        bot.reply_to(message, f"❌ An error occurred while removing item `{bid_id_to_remove}`.")

@bot.message_handler(commands=['refresh'])
def handle_refresh(message):
    """
    Clears any ongoing multi-step operation or cached data for the user.
    Acts similarly to /cancel.
    """
    if is_banned(message.from_user.id):
        # No need to reply if banned
        return

    if message.chat.type == 'private':
        user_id = message.from_user.id
        state_cancelled = False
        cache_cleared = False
        action_taken = False # Flag to check if anything was cleared

        if user_id in user_states:
            del user_states[user_id]
            action_taken = True
            logger.info(f"State cancelled for user {user_id} via /refresh")
        if user_id in user_cache:
             del user_cache[user_id] # Clear any cached submission data
             action_taken = True
             logger.info(f"Submission cache cleared for user {user_id} via /refresh.")
        if user_id in pending_bids:
            # Find and remove pending bids specifically for this user
            keys_to_remove = [k for k, v in list(pending_bids.items()) if v.get('user_id') == user_id] # Use list() for safe iteration
            if keys_to_remove:
                action_taken = True
                for key in keys_to_remove:
                    # Try to edit the pending bid message first
                    try:
                        bid_details = pending_bids[key]
                        # The pending bid message ID is the original user message + 1
                        pending_msg_id = bid_details.get('original_message_id', 0) + 1
                        if pending_msg_id > 0:
                            bot.edit_message_text("❌ Operation cancelled by /refresh.", chat_id=user_id, message_id=pending_msg_id, reply_markup=None)
                    except Exception:
                        pass # Ignore if editing fails
                    # Remove from dict
                    del pending_bids[key]
                logger.info(f"Cleared {len(keys_to_remove)} pending bid confirmations for user {user_id} via /refresh")


        if action_taken:
            bot.send_message(message.chat.id, "✅ Bot refreshed. Any active command process has been cancelled.", parse_mode="html")
            bot.send_sticker(message.chat.id, OK_STICKER_ID) # <-- ADDED STICKER
        else:
            bot.send_message(message.chat.id, "✅ Bot refreshed. No active process found to cancel.")
            bot.send_sticker(message.chat.id, OK_STICKER_ID) # <-- ADDED STICKER (optional here, but consistent)


    else:
        # Suggest using it in PM if used in a group
        bot.send_sticker(message.chat.id, WARNING_STICKER_ID)
        markup=InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Refresh Bot State', url=f'https://t.me/{bot.get_me().username}?start=refresh')) # You could add a deep link if desired
        bot.reply_to(message, "<blockquote>Please use /refresh in our private chat to clear any stuck process.</blockquote>", parse_mode="html", reply_markup=markup, disable_web_page_preview=True)


# === Polling Start ===
if __name__ == '__main__':
    logger.info(f"Bot starting... Version: {CURRENT_BOT_VERSION}")
    # Set bot commands for UI
    try:
        bot.set_my_commands([
            BotCommand("start", "Start/Restart the bot"),
            BotCommand("add", "Submit an item for auction"),
            BotCommand("elements", "Browse active auction items"),
            BotCommand("refresh", "Refresh bot state / Cancel command"),
            BotCommand("mybids", "View your current bids"),
            BotCommand("myphg", "View items you won (after auction)"),
            BotCommand("mysold", "View items you sold (after auction)"),
            BotCommand("profile", "View/Edit your profile"),
            BotCommand("leaderboard", "Show top points earners"),
            BotCommand("brules", "View bidding rules"),
            BotCommand("subrules", "View submission rules"),
            BotCommand("report", "Report an issue/message to admins"),
            BotCommand("cancel", "Cancel current operation"),
        ])
        logger.info("Bot commands updated.")
    except Exception as cmd_err:
        logger.error(f"Could not set bot commands: {cmd_err}")

    # More robust polling
    bot.infinity_polling(logger_level=logging.INFO, timeout=20, long_polling_timeout=30)
    logger.info("Bot stopped.")

# --- END OF REFACTORED FILE broad.txt ---
