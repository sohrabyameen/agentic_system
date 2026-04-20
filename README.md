# WhatsApp Perfume Agent

A WhatsApp Business API bot for automating perfume sales through Google Sheets inventory management. Customers can browse perfumes, check availability, and place orders directly through WhatsApp.

## Features

- **Automated Customer Service**: Responds to WhatsApp messages instantly
- **Google Sheets Integration**: Real-time inventory management with caching
- **Stock Checking**: Verifies perfume availability before confirming orders
- **Template Messages**: Uses WhatsApp templates for professional order confirmations
- **Error Handling**: Graceful responses for out-of-stock items and invalid numbers
- **Message Read Receipts**: Automatically marks messages as read

## Architecture

The application consists of three main modules:

- **app.py**: Flask web server handling WhatsApp webhook endpoints
- **whatsapp.py**: WhatsApp Business API integration for sending messages
- **sheets.py**: Google Sheets API client with built-in caching

## Prerequisites

- Python 3.8+
- WhatsApp Business API account
- Google Cloud project with Google Sheets API enabled
- Google Sheet with perfume inventory

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Sheets Setup

1. Create a Google Sheet with the following columns:
   - `Number`: Unique perfume identifier
   - `Name`: Perfume name
   - `Available`: Stock status ("Yes" or "No")
   - `Price`: Perfume price

2. Enable Google Sheets API in Google Cloud Console

3. Create a service account and download the credentials JSON file
   - Rename it to `cred.json` and place it in the project root

4. Share the Google Sheet with the service account email (give it Editor access)

### 3. WhatsApp Business API Setup

1. Create a Meta Developer account
2. Set up a WhatsApp Business App
3. Create a WhatsApp message template named `order_confirmation` with variables for:
   - Perfume number
   - Perfume name
   - Price

### 4. Environment Configuration

Create a `.env` file with the following variables:

```env
SPREADSHEET_ID=your_google_sheet_id
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
PORT=5000
APP_SECRET=your_app_secret
API_VERSION=v19.0
```

## How It Works

1. **Customer sends a message** to the WhatsApp business number
2. **Webhook receives the message** and processes it in a background thread
3. **Bot checks Google Sheets** for perfume data (cached for 10 seconds)
4. **Based on message type**:
   - **Text message**: Sends welcome message with Google Sheet link
   - **Perfume number**: Checks stock and availability
     - If in stock: Sends order confirmation template
     - If out of stock: Sends out-of-stock notification
     - If invalid: Sends error message
   - **Button click**: Handles button interactions (e.g., "Yes" confirmations)

## Google Sheet Format

| Number | Name | Available | Price |
|--------|------|-----------|-------|
| 1 | Rose Perfume | Yes | $50 |
| 2 | Lavender Mist | No | $45 |
| 3 | Ocean Breeze | Yes | $60 |

## Running the Application

### Development

```bash
python app.py
```

The server will start on port 5000.

### Production

Use gunicorn for production deployment:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Webhook Configuration

Set your webhook URL in the Meta Developer Console:

```
https://your-domain.com/webhook
```

The webhook will:
- **GET request**: Verify the webhook with your `WEBHOOK_VERIFY_TOKEN`
- **POST request**: Receive incoming WhatsApp messages

## API Endpoints

### GET /webhook
Verifies the webhook configuration with Meta.

### POST /webhook
Receives incoming WhatsApp messages and processes them asynchronously.

## Caching

The Google Sheets client implements a 10-second cache to reduce API calls. This prevents rate limiting and improves response times. Adjust `CACHE_TTL` in `sheets.py` if needed.

## Error Handling

The application includes comprehensive error handling:
- Google Sheets API failures return cached data if available
- WhatsApp API failures log detailed error messages from Meta
- Invalid perfume numbers trigger helpful error responses
- Missing or malformed data is handled gracefully

## Security

- Never commit `.env` or `cred.json` to version control
- Use environment variables for all sensitive data
- Keep WhatsApp access tokens secure
- Regularly rotate API credentials

## Troubleshooting

### Google Sheets Not Connecting
- Verify `cred.json` exists and is valid
- Ensure the service account email has access to the sheet
- Check that the `SPREADSHEET_ID` is correct

### WhatsApp Messages Not Sending
- Verify `WHATSAPP_ACCESS_TOKEN` is valid
- Check that the phone number ID is correct
- Ensure the message template is approved in Meta Business Suite
- Review Meta's error logs in the console output

### Webhook Not Receiving Messages
- Verify the webhook URL is publicly accessible
- Check that `WEBHOOK_VERIFY_TOKEN` matches in Meta Console
- Ensure your server is running and accessible

## License

This project is provided as-is for perfume business automation.
