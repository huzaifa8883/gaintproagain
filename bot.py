import logging
import asyncio
import random
from flask import Flask, request
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import nest_asyncio  # Import nest_asyncio to fix event loop issue

# Initialize Flask app
app = Flask(__name__)

# Telegram Bot Token (Hardcoded)
TOKEN = "7710449526:AAFSOXyZl0M61RY9Xxwzvy-UT5O8VFi_oHY"

# Store users who started the bot
subscribed_users = set()

# Set up logging with file handler for production
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Logs to stdout
        logging.FileHandler("bot_logs.log")  # Logs to a file
    ]
)
logger = logging.getLogger(__name__)

# Function to send trade signals
async def send_signal(context: CallbackContext):
    buy_options = ["Big", "Small", "Single", "Double"]
    buy = random.choice(buy_options)

    period = str(int(asyncio.get_event_loop().time() * 1000))  # Generate period
    message = (
        f"⏰Trade Type: 5 Minute⏰\n\n"
        f"👉Period: {period}\n"
        f"👉Buy: {buy}\n"
        f"💰Bet: 1 USDT\n\n"
        f"🔥Earn 30% interest on each bet.\n"
        f"🔥The higher the stage, the more profit you make."
    )

    # Log the list of subscribed users and send the message
    logger.info(f"Subscribed users: {subscribed_users}")
    
    for chat_id in subscribed_users:
        try:
            logger.info(f"Sending message to {chat_id}")
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")

# Handle /start command
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in subscribed_users:
        subscribed_users.add(chat_id)
        await update.message.reply_text("✅ You have subscribed to trade signals. You'll receive updates every 1 minute.")
    else:
        await update.message.reply_text("🔔 You are already subscribed!")

# Function to initialize the bot
async def main():
    application = Application.builder().token(TOKEN).build()
    
    # Add /start command handler
    application.add_handler(CommandHandler("start", start))
    
    # Schedule job to send messages every 1 minute
    job_queue = application.job_queue
    logger.info("Job queue initialized")
    job_queue.run_repeating(send_signal, interval=300, first=5)  # 60 seconds = 1 minute

    # Start bot polling
    await application.run_polling()

# Flask route for testing
@app.route('/')
def home():
    return "Bot is running!"

# Webhook fix
@app.route('/webhook', methods=['POST'])
def webhook():
    return "Webhook received!", 200

# Function to start Flask in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)

# Function to send a manual test message
async def test_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text="Test message!")

# Start Telegram bot in the main thread, Flask in a separate thread
if __name__ == "__main__":
    # Apply nest_asyncio to avoid event loop conflicts
    nest_asyncio.apply()
    
    # Run Flask in a separate thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run Telegram bot in the main thread with proper event loop handling
    asyncio.get_event_loop().run_until_complete(main())
