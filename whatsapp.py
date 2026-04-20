import os
import requests


def _get_url():
    """
    Construct the WhatsApp API URL using environment variables.
    Returns the endpoint for sending messages.
    """
    phone_number_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    api_version = os.environ["API_VERSION"]
    WA_API_URL = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    return WA_API_URL


def _get_headers():
    """
    Construct the HTTP headers for WhatsApp API requests.
    Includes the access token for authentication.
    """
    return {
        "Authorization": f"Bearer {os.environ['WHATSAPP_ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }



def send_text_message(to: str):
    """
    Send a welcome message with the Google Sheets catalog link.
    Used when customers send non-numeric messages or first interact.
    """
    text = "Welcome to our Perfume Store! Please check the google sheet link below to explore our perfumes. If you want to buy one check its perfume number on google sheet. \n\n Google Sheet Link: https://docs.google.com/spreadsheets/d/11r0cPHRVOiD1cPm38a7uj8GSlKOmn50fpSXfh7y6anY/edit?usp=sharing"

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text, "preview_url": False},
    }

    try:
        response = requests.post(_get_url(), json=payload, headers=_get_headers(), timeout=10)

        if response.ok:
            print(f"✅ Successfully sent reply to {to}")
        else:
            print(f"❌ Failed to send reply to {to} in send_text_message()")
            print(f"Status Code: {response.status_code}")
            # THIS is the magic line that exposes Meta's exact error:
            print(f"Meta Error Details: {response.text}")

    except Exception as e:
        print(f"🔥 Request failed entirely: {e}")



def out_of_stock(to: str, perfume_number: str, name: str):
    """
    Send an out-of-stock notification to the customer.
    Called when a requested perfume is not available.
    """
    text = f"Sorry, {name} (Number: {perfume_number}) is currently out of stock. Please check the google sheet link below to explore our available perfumes."
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text, "preview_url": False},
    }

    try:
        response = requests.post(_get_url(), json=payload, headers=_get_headers(), timeout=10)

        if response.ok:
            print(f"✅ Successfully sent reply to {to}")
        else:
            print(f"❌ Failed to send reply to {to} in out_of_stock()")
            print(f"Status Code: {response.status_code}")
            # THIS is the magic line that exposes Meta's exact error:
            print(f"Meta Error Details: {response.text}")

    except Exception as e:
        print(f"🔥 Request failed entirely: {e}")




def check_perfume_number(to: str):
    """
    Send an error message for invalid perfume numbers.
    Called when the customer sends a number that doesn't exist in the catalog.
    """
    text = "Sorry, I couldn't find that perfume number. Please check the google sheet again and send the correct number."
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text, "preview_url": False},
    }

    try:
        response = requests.post(_get_url(), json=payload, headers=_get_headers(), timeout=10)

        if response.ok:
            print(f"✅ Successfully sent reply to {to}")
        else:
            print(f"❌ Failed to send reply to {to} in check_perfume_number()")
            print(f"Status Code: {response.status_code}")
            # THIS is the magic line that exposes Meta's exact error:
            print(f"Meta Error Details: {response.text}")

    except Exception as e:
        print(f"🔥 Request failed entirely: {e}")



def test_reply(to: str):
    """
    Send a test reply for button interactions.
    Used when customer clicks "Yes" on a confirmation button.
    """
    text = "This is a test reply. You will receive a payment link here."
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text, "preview_url": False},
    }

    try:
        response = requests.post(_get_url(), json=payload, headers=_get_headers(), timeout=10)

        if response.ok:
            print(f"✅ Successfully sent reply to {to}")
        else:
            print(f"❌ Failed to send reply to {to} in test_reply()")
            print(f"Status Code: {response.status_code}")
            # THIS is the magic line that exposes Meta's exact error:
            print(f"Meta Error Details: {response.text}")

    except Exception as e:
        print(f"🔥 Request failed entirely: {e}")



def order_confirm(to: str, perfume_number: str, perfume_name: str, price: str):
    """
    Send an order confirmation using a WhatsApp template.
    Template must be pre-approved in Meta Business Suite.
    Variables: perfume_number, perfume_name, price
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": {
            "name": "order_confirmation",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body", # This targets the variables in the body text
                    "parameters": [
                        {
                            "type": "text",
                            "text": perfume_number # This replaces {{1}} in the body
                        },
                        {
                            "type": "text",
                            "text": perfume_name # This replaces {{2}} in the body
                        },
                        {
                            "type": "text",
                            "text": price # This replaces {{3}} in the body
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(_get_url(), json=payload, headers=_get_headers(), timeout=10)

        if response.ok:
            print(f"✅ Successfully sent reply to {to}")
        else:
            print(f"❌ Failed to send reply to {to} in order_confirm()")
            print(f"Status Code: {response.status_code}")
            # THIS is the magic line that exposes Meta's exact error:
            print(f"Meta Error Details: {response.text}")

    except Exception as e:
        print(f"🔥 Request failed entirely: {e}")





def mark_as_read(message_id: str):
    """
    Mark an incoming message as read (shows blue ticks to customer).
    This provides visual feedback that the message was received.
    """
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    try:
        response = requests.post(_get_url(), json=payload, headers=_get_headers(), timeout=5)

        if response.ok:
            print(f"✅ Marked message {message_id} as READ.")
        else:
            print(f"❌ Failed to mark as read. Status: {response.status_code}")
            print(f"Meta Error Details: {response.text}")

    except Exception as e:
        print(f"🔥 CRASH IN MARK_AS_READ: {e}")

