# Zabbix to Telegram Webhook

This application serves as a webhook between Zabbix and Telegram, allowing you to:

1. Receive notifications from Zabbix
2. Forward them to Telegram
3. Enable/disable notifications via Telegram commands or API endpoints
4. View notification history


![Schema](/misc/schema.jpg "Zabbix Webhook Schema")


## Setup

### Prerequisites

- Python 3.6+
- A Telegram bot token (create one via [@BotFather](https://t.me/botfather))
- A Zabbix server configured to send webhook notifications

### This Script webhook is customized to be used in a virtual environment and as a Linux Service.

To create a virtual environment in order not to break the OS packages, follow these steps (these steps are in Linux Ubuntu OS):
1. install pip3 packages: </br>
```
sudo apt-get install python3-pip
```

2. install python virtual environment package: </br>
```
sudo apt install python3-venv
```

### Preparing virtual environment
1. First, create your environment with the desired name: </br>
```
python3 -m venv box
```

2. activate your environment: </br>
```
source box/bin/activate
``` 

(You can further deactivate it via the `deactivate` command.)


### Installation

1. Install dependencies (in your created environment):
   ```
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_default_chat_id"
   ```
   
   It is recommended to set these directly in the `.env` file.

### Running the Application

```
python zabbix_webhook.py
```

The application will start a Flask server on port 5000 and also run the Telegram bot in a separate thread.

## Configuring Zabbix

1. In Zabbix, go to Alerts > Media types
2. Create a new media type of type "Webhook"
3. Configure the webhook with the following parameters:
   - Name: Telegram Webhook
   - Type: Webhook
   - Media parameters:
     - Message: {ALERT.MESSAGE}
     - Severity: {TRIGGER.SEVERITY}
     - Subject: {ALERT.SUBJECT}
     - To: {ALERT.SENDTO} # which will be the Telegram ID (by default it reads from .env file)
     - URL: `http://your-server:5000/webhook` (recommended to use User MACRO for defining your URL )
     - HTTP method: POST
     - Content type: application/json
     - Script:
        ```javaScript
            var params = JSON.parse(value);

            var request = new HttpRequest();
            request.addHeader('Content-Type: application/json');

            var data = {
                'chat_id': params.To,
                'subject': params.Subject,
                'message': params.Message,
                'severity': params.Severity
            };

            try {
                var response = request.post(params.URL, JSON.stringify(data));
                var responseData = JSON.parse(response);
                
                // Check if the bot is disabled
                if (responseData.status === "ignored" && responseData.reason === "notifications disabled") {
                    Zabbix.log(4, 'Telegram notification not sent: Bot is currently DISABLED');
                    return 'FAILED: Bot is currently DISABLED. Enable notifications to receive alerts.';
                }
                
                // Check for other errors
                if (responseData.status === "error") {
                    Zabbix.log(4, 'Telegram webhook error: ' + responseData.reason);
                    return 'FAILED: ' + responseData.reason;
                }
                
                // Success case
                return 'OK: Message sent successfully. Bot status: ' + (responseData.bot_status || 'ENABLED');
            }
            catch (error) {
                Zabbix.log(4, 'Telegram webhook error: ' + error);
                throw 'Failed to send message: ' + error;
            }
            
        ```

4. Create a new action in Zabbix and assign this media type to it.
5. Assign the Media Type to the Proper User.


## Telegram Bot Commands

- `/start_zabbix` - Introduction message
- `/enable_zabbix` - Enable notifications
- `/disable_zabbix` - Disable notifications
- `/zabbix_status` - Check if notifications are enabled
- `/zabbix_history` - View recent notification history

## API Endpoints

- `GET /zabbix_status` - Check the current status
- `GET /enable_zabbix` - Enable notifications
- `GET /disable_zabbix` - Disable notifications
- `POST /webhook` - Endpoint for Zabbix to send notifications

## Testing

You can test the webhook by sending a POST request to the `/webhook` endpoint:

```bash
curl -X POST http://(your_IP_address):5000/webhook   -H "Content-Type: application/json"   -d '{"subject":"Test Alert", "message":"This is a test message", "severity":"High", "chat_id":"Telegram_Chat_ID"}'
``` 

## Message Templates

1. Click **Add** to add a template
2. Select the event source (e.g., "Trigger")
3. Select the recovery operation (e.g., "Problem")
4. Enter a subject like: `Problem: {EVENT.NAME}`
5. Enter a message like:
   ```
   Problem started at {EVENT.TIME} on {EVENT.DATE}
   Problem name: {EVENT.NAME}
   Host: {HOST.NAME}
   Severity: {TRIGGER.SEVERITY}
   
   Original problem ID: {EVENT.ID}
   {TRIGGER.URL}
   ```
6. Add another template for recovery operations with an appropriate subject and message 


##### To use it as a service:
1. First create a `.service` file in /etc/systemd/system/ (Ubuntu), for instance:
```sh
nano /etc/systemd/system/Zabbix-Webhook.service
```

Then configure the Service, followed by:
```sh
[Unit]
Description= Description About your Service
After=network.target

[Service]
#User=zabbix  # add user if it needs to be defined in my case not yet
# WorkingDirectory=
ExecStart=/your-path-to-venv-python/box/bin/python yourpath-to-telegram-webhook/zabbix_webhook.py  # Full path of Executer and Python script is 
# Add any other necessary environment variables here if needed
Environment=VAR1=value1
Environment=VAR2=value2

[Install]
WantedBy=multi-user.target
```

Then start your service:
``` systemctl start Zabbix-Webhook.service ```

or view logs via journalctl:
```  journalctl -u Zabbix-Webhook.service ```
