
# Import required libraries
import os
import logging
import threading
from flask import Flask, jsonify, request, make_response
from dotenv import load_dotenv

# Import custom modules
from sheets import SheetClient
from whatsapp import mark_as_read
from whatsapp import send_text_message, order_confirm, out_of_stock, check_perfume_number, test_reply

# Load environment variables from .env file
load_dotenv()



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# Initialize Flask app
app = Flask(__name__)

# Load WhatsApp webhook configuration from environment variables
VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.environ.get("APP_SECRET", "")

# Load Google Sheets ID from environment
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")

# Initialize Google Sheets client
sheet = SheetClient(spreadsheet_id=SPREADSHEET_ID)



@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Verify webhook endpoint for Meta/Facebook.
    Called by Meta when setting up the webhook to confirm ownership.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Verify the token matches our configured verify token
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    # Return 400 if verification fails
    return 400


@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Receive incoming WhatsApp messages from Meta webhook.
    Processes messages asynchronously in a separate thread.
    """
    data = request.get_json()

    # Process webhook in background thread to avoid blocking
    thread = threading.Thread(target=process_webhook, args=(data,))
    thread.start()

    # Return immediately to Meta (must respond within 3 seconds)
    return make_response(jsonify({"status": "ok"}), 200)


def process_webhook(data: dict):
    """
    Process incoming webhook data from WhatsApp Business API.
    Extracts messages and handles customer interactions.
    """
    numbers = []
    try:
        # Verify the webhook is from WhatsApp Business Account
        if data.get("object") != "whatsapp_business_account":
            return

        # Iterate through entries and changes to find messages
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                # Process each message
                for message in messages:
                    phone = message.get("from")  # Customer's phone number
                    msg_id = message.get("id")     # Message ID
                    msg_type = message.get("type") # Message type (text, button, etc.)

                    try:
                        # Fetch perfume data from Google Sheets
                        numbers, name_lookup, stock_lookup, price_lookup = sheet.get_data()
 
                        # Validate that we got all required data
                        if name_lookup is None or stock_lookup is None or price_lookup is None:
                            print("Error: Missing expected columns in sheet data.")
                            return

                    except Exception as e:
                        print(f"Error fetching sheet data Or making lookup data: {e} ")
                    
                    # Mark message as read (shows blue ticks to customer)
                    if msg_id:
                        mark_as_read(msg_id)
                    
                    # Only handle text and button messages
                    if msg_type not in ["text","button"]:
                        send_text_message(phone)
                        return
                    
                    # Extract message text
                    text = message["text"]["body"]

                    # Handle button messages (e.g., confirmation buttons)
                    if msg_type == "button":
                        text = message["button"]["text"]
                        if text == "Yes":
                            test_reply(phone)

                    else:
                        # Handle text messages - try to parse as perfume number
                        try:
                            perfume_number = int(text)
                            # Check if the perfume number exists in our inventory
                            if perfume_number in numbers:
                                name = (name_lookup[perfume_number])
                                price = (price_lookup[perfume_number])
                                # Check if the perfume is in stock
                                if stock_lookup[perfume_number] == "Yes":
                                    order_confirm(phone,perfume_number, name, price)
                                else:
                                    out_of_stock(phone,perfume_number, name)

                            else:
                                # Invalid perfume number
                                check_perfume_number(phone)
                                return


                        except Exception as e:
                            # If text is not a number, send welcome message
                            pass
                    
                    # Send welcome message for non-numeric input
                    send_text_message(phone)
                    return




    except Exception as e:
        # Log any unexpected errors
        pass



# Error handlers for common HTTP errors
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": str(e.description)}), 401

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500



# Run the Flask app when executed directly
if __name__ == "__main__":
    app.run(debug=False, port=5000)
