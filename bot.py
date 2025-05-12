import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - these will come from GitHub Secrets
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Dictionary to store chat sessions per user
user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_chats[user.id] = model.start_chat(history=[])
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm a chatbot powered by Google Gemini.\n\n"
        "Just send me a message and I'll respond!\n\n"
        "Use /newchat to start a fresh conversation."
    )

async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new chat session."""
    user = update.effective_user
    user_chats[user.id] = model.start_chat(history=[])
    await update.message.reply_text("Started a new conversation. Previous context has been cleared.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate responses using Gemini."""
    user = update.effective_user
    
    # Initialize chat if it doesn't exist for this user
    if user.id not in user_chats:
        user_chats[user.id] = model.start_chat(history=[])
    
    user_message = update.message.text
    
    try:
        # Get response from Gemini
        response = user_chats[user.id].send_message(user_message)
        
        # Send the response back to Telegram
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your message.")

def main():
    """Start the bot."""
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        raise ValueError("Missing required environment variables.")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newchat", new_chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
