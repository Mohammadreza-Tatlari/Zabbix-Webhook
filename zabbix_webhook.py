#!/usr/bin/env python3


import telebot
import threading
import time
from flask import Flask, request, jsonify

# Import configuration
from config import BOT_TOKEN, CHAT_ID, PORT, DEBUG, validate_config

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot
bot = telebot.TeleBot(BOT_TOKEN)

# Global variable to track notification status
notifications_enabled = True

# Store the last few notifications for debugging
notification_history = []
MAX_HISTORY = 10

# Telegram bot command handlers
@bot.message_handler(commands=['start_zabbix'])
def start(message):
    bot.reply_to(message, "This is the Zabbix Notification bot. Use /enable_zabbix or /disable_zabbix to control notifications.")

@bot.message_handler(commands=['enable_zabbix'])
def enable_notifications(message):
    global notifications_enabled
    if not notifications_enabled:
        notifications_enabled = True
        bot.reply_to(message, "Zabbix notifications are now enabled.")
    else:
        bot.reply_to(message, "Zabbix notifications are already enabled.")

@bot.message_handler(commands=['disable_zabbix'])
def disable_notifications(message):
    global notifications_enabled
    if notifications_enabled:
        notifications_enabled = False
        bot.reply_to(message, "Zabbix notifications are now disabled. Use /enable_zabbix to turn them back on.")
    else:
        bot.reply_to(message, "Zabbix notifications are already disabled.")

@bot.message_handler(commands=['zabbix_status'])
def status(message):
    status_text = "Zabbix notifications are currently " + ("enabled" if notifications_enabled else "disabled")
    bot.reply_to(message, status_text)

@bot.message_handler(commands=['zabbix_history'])
def show_history(message):
    print(f"Current notification history length: {len(notification_history)}")
    print(f"Notification history contents: {notification_history}")
    
    if not notification_history:
        bot.reply_to(message, "No notification history available.")
        return
    
    history_text = "Recent notifications:\n\n"
    for i, notif in enumerate(notification_history, 1):
        history_text += f"{i}. {notif.get('subject', 'No subject')}\n"
        history_text += f"   Message: {notif.get('message', 'No message')}\n"
        history_text += f"   Severity: {notif.get('severity', 'Unknown')}\n\n"
    
    bot.reply_to(message, history_text)

@bot.message_handler(func=lambda message: True)  # Handles all other messages
def handle_message(message):
    bot.reply_to(message, "Unknown command. Available commands: /enable_zabbix, /disable_zabbix, /zabbix_status, /zabbix_history")

# Flask routes

# main route listening for zabbix notifcations and collect them inside the data variable
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint for Zabbix to send notifications.
    Expected JSON format from Zabbix:
    {
        "subject": "Problem: Host XYZ has an issue",
        "message": "Detailed problem description...",
        "severity": "High",
        "chat_id": "Optional: chat ID will be overwritten by .env"
    }
    """
    try:
        data = request.json
        
        # Log the notification on Terminal
        print(f"Received notification: {data}")
        
        # Add to history and pop the first on if the history Maximum is reached
        if len(notification_history) >= MAX_HISTORY:
            notification_history.pop(0)
        notification_history.append(data)
        print(f"Added to history. Current length: {len(notification_history)}")
        
        # Check if notifications are enabled
        if not notifications_enabled:
            return jsonify({"status": "ignored", "reason": "notifications disabled"})
        
        # Extract notification details and handle Zabbix macros
        subject = data.get('subject', 'No subject')
        if '{' in subject:
            subject = 'Unknown/default Subject Field From zabbix'
            
        message = data.get('message', 'No message')
        if '{' in message:
            message = 'Unknown/default Message Field From zabbix'
            
        severity = data.get('severity', 'Unknown')
        if '{' in severity:
            severity = 'Disaster (default for Unknown or empty data Macros)'
        
        # Determine which chat to send to
        chat_id = data.get('chat_id', CHAT_ID)
        
        # Handle Zabbix macros - if chat_id contains '{' it's likely a macro
        if not chat_id or '{' in chat_id:
            chat_id = CHAT_ID
            
        if not chat_id:
            return jsonify({"status": "error", "reason": "no chat_id specified"})
        
        # Format the message for Telegram
        telegram_message = f"*{subject}*\n\n{message}\n\nSeverity: {severity}"
        
        # Sends to Telegram based on the chat_id and the message
        bot.send_message(chat_id, telegram_message, parse_mode="Markdown") # Markdown is used to format the message (defined in zabbix server)
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route('/enable_zabbix', methods=['GET'])
def api_enable():
    global notifications_enabled
    notifications_enabled = True
    return jsonify({"status": "success", "notifications": "enabled"})

@app.route('/disable_zabbix', methods=['GET'])
def api_disable():
    global notifications_enabled
    notifications_enabled = False
    return jsonify({"status": "success", "notifications": "disabled"})

@app.route('/zabbix_status', methods=['GET'])
def api_status():
    return jsonify({
        "status": "success", 
        "notifications_enabled": notifications_enabled,
        "history_count": len(notification_history)
    })

def start_polling():
    """Start the bot polling in a separate thread"""
    try:
        print("Starting Telegram bot polling...")
        bot.remove_webhook()  # Remove any existing webhook
        # Configure polling with reasonable intervals and timeout
        bot.polling(
            none_stop=True,
            interval=3,  # 3 seconds between updates
            timeout=30,  # Long polling timeout
            allowed_updates=['message']  # Only get message updates
        )
    except Exception as e:
        print(f"Error in polling thread: {e}")
        # Wait before trying to reconnect
        time.sleep(5)
        start_polling()  # Restart polling on error

if __name__ == '__main__':
    # Validate configuration
    if not validate_config():
        print("WARNING: Running with incomplete configuration!")
    
    # Start bot polling in a separate thread
    polling_thread = threading.Thread(target=start_polling, daemon=True)
    polling_thread.start()
    print("Bot polling thread started")
    
    # Start the Flask app
    print("Starting Flask server...")
    app.run(host='172.24.24.12', port=PORT, debug=DEBUG) 


