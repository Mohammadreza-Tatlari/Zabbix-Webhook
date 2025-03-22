#!/usr/bin/env python3
# Not a Mandatory file, it is used to test the webhook only
import requests
import json
import argparse
from config import CHAT_ID

def send_test_notification(webhook_url, subject, message, severity, chat_id=None):
    """Send a test notification to the webhook."""
    
    # Prepare the payload
    payload = {
        "subject": subject,
        "message": message,
        "severity": severity,
        "chat_id": chat_id or CHAT_ID
    }
    
    # Send the request
    print(f"Sending test notification to {webhook_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Print the response
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response.status_code == 200
    
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the Zabbix webhook")
    parser.add_argument("--url", default="http://localhost:5000/webhook", help="Webhook URL")
    parser.add_argument("--subject", default="Test Alert", help="Alert subject")
    parser.add_argument("--message", default="This is a test message from the test script.", help="Alert message")
    parser.add_argument("--severity", default="High", help="Alert severity")
    parser.add_argument("--chat-id", default=None, help="Override the default chat ID")
    
    args = parser.parse_args()
    
    # Send the test notification
    success = send_test_notification(
        args.url,
        args.subject,
        args.message,
        args.severity,
        args.chat_id
    )
    
    # Exit with appropriate status code
    exit(0 if success else 1) 