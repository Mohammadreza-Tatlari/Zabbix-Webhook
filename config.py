import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Flask Configuration
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

# Validate configuration
def validate_config():
    """Validate that required configuration is present."""
    missing = []
    
    if not BOT_TOKEN:
        missing.append('TELEGRAM_BOT_TOKEN')
    
    if not CHAT_ID:
        missing.append('TELEGRAM_CHAT_ID')
    
    if missing:
        print(f"WARNING: Missing required configuration: {', '.join(missing)}")
        print("Please set these in your environment or .env file.")
        return False
    
    return True

if __name__ == "__main__":
    # This allows running this file directly to test configuration
    validate_config()
    print("Configuration:")
    print(f"BOT_TOKEN: {'*' * 8}{BOT_TOKEN[-4:] if BOT_TOKEN else 'Not set'}")
    print(f"CHAT_ID: {CHAT_ID or 'Not set'}")
    print(f"PORT: {PORT}")
    print(f"DEBUG: {DEBUG}") 