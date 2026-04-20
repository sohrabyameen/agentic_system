# =============================================================================
# sheets.py — Google Sheets Reader with Caching
# =============================================================================
# This module is responsible for ONE thing:
#   "Give me the latest data from the Google Sheet."
#
# How caching works:
#   - First request → fetch from Google Sheets API → store in memory
#   - Next requests → return stored data instantly (no API call)
#   - Every CACHE_TTL seconds → fetch fresh data from API again
#
# This means no matter how many Flask requests come in (50–100/min),
# we only call the Google API once every 10 seconds.
# =============================================================================

# Import required libraries
import time
import logging
import gspread
from google.oauth2.service_account import Credentials

# Configure module logger
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

# The exact name of your Google Sheet tab (bottom tab in Google Sheets)
SHEET_NAME = "Sheet1"

# How long to keep cached data before fetching fresh data (in seconds)
# 10 = refresh every 10 seconds. Increase to 60 or 300 if your data
# doesn't need to be that fresh.
CACHE_TTL = 10

# Path to your downloaded service account JSON key file
CREDENTIALS_FILE = "cred.json"

# These are the exact Google API permissions we need.
# read-only scope is enough since we never write from Flask.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

class SheetClient:
    """
    Manages the connection to Google Sheets and caches the data.

    Usage:
        sheet = SheetClient(spreadsheet_id="your-sheet-id")
        data  = sheet.get_data()   # Returns list of dicts
    """

    def __init__(self, spreadsheet_id: str):
        """
        Initialize the SheetClient with a spreadsheet ID.
        
        spreadsheet_id: The long ID in your Google Sheet URL.
            URL:  https://docs.google.com/spreadsheets/d/THIS_PART_HERE/edit
        """
        self.spreadsheet_id = spreadsheet_id

        # Cache storage
        self._cached_data      = None   # The actual data (list of dicts)
        self._last_fetched_at  = 0   
        self.numbers   = []   # List to store the "Number" values
        self.name_lookup  = {}   # Dict to map "Number" to "Name"
        self.stock_lookup = {}   # Dict to map "Number" to "Available"
        self.price_lookup = {}   # Dict to map "Number" to "Price"  

        # Connect to Google Sheets API once on startup
        self._client = self._build_client()

    def _build_client(self):
        """
        Authenticates with Google using the service account credentials.
        This only runs once when the app starts.
        """
        try:
            # Load credentials from the service account JSON file
            creds = Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=SCOPES
            )
            # Authorize the gspread client with the credentials
            client = gspread.authorize(creds)
            logger.info("✅ Connected to Google Sheets API")
            return client

        except FileNotFoundError:
            logger.error(
                "❌ credentials.json not found. "
                "Download it from Google Cloud Console → Service Accounts → Keys."
            )
            raise

        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            raise

    def _is_cache_stale(self) -> bool:
        """
        Check if the cached data needs to be refreshed.
        Returns True if the cache is empty or older than CACHE_TTL seconds.
        """
        if self._cached_data is None:
            return True
        return (time.time() - self._last_fetched_at) > CACHE_TTL

    def _fetch_from_api(self) -> list[dict]:
        """
        Fetches all rows from the Google Sheet.
        Returns a list of dicts where keys are column headers (Row 1 in your sheet).

        Example return value:
            [
                {"Name": "Apple",  "Price": "1.99", "Stock": "100"},
                {"Name": "Banana", "Price": "0.99", "Stock": "250"},
            ]
        """
        try:
            spreadsheet = self._client.open_by_key(self.spreadsheet_id)
            worksheet   = spreadsheet.worksheet(SHEET_NAME)

            records = worksheet.get_all_records()

            logger.info(f"✅ Fetched {len(records)} rows from Google Sheets")
            return records

        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(
                "❌ Spreadsheet not found. Check your SPREADSHEET_ID "
                "and make sure you shared the sheet with the service account email."
            )
            return self._cached_data or []   

        except gspread.exceptions.WorksheetNotFound:
            logger.error(
                f"❌ Sheet tab '{SHEET_NAME}' not found. "
                "Check the SHEET_NAME matches the tab name in Google Sheets."
            )
            return self._cached_data or []

        except Exception as e:
            logger.error(f"❌ Error fetching sheet data: {e}")

            return self._cached_data or []

    def get_data(self) -> tuple:
        """
        Main method — call this from your Flask routes.

        Returns cached data if fresh, otherwise fetches from API first.
        Never raises an exception — returns empty data on total failure.
        
        Returns:
            tuple: (numbers_list, name_lookup_dict, stock_lookup_dict, price_lookup_dict)
        """
        if self._is_cache_stale():
            logger.debug("Cache stale — fetching fresh data from Google Sheets")
            fresh_data = self._fetch_from_api()

            # Only update cache if we got real data back
            # (avoids wiping good cache with an empty error response)
            if fresh_data is not None:
                self._cached_data     = fresh_data
                self._last_fetched_at = time.time()
                # Build lookup dictionaries for quick access
                for rows in self._cached_data:
                    self.numbers.append(rows["Number"])
                self.name_lookup = {item["Number"]: item["Name"] for item in self._cached_data}
                self.stock_lookup = {item["Number"]: item["Available"] for item in self._cached_data}
                self.price_lookup = {item["Number"]: item["Price"] for item in self._cached_data}
        

        return self.numbers, self.name_lookup, self.stock_lookup, self.price_lookup


    @property
    def cache_age_seconds(self) -> float:
        """
        Property that returns how many seconds ago the cache was last updated.
        Returns infinity if cache has never been updated.
        """
        if self._last_fetched_at == 0:
            return float("inf")
        return time.time() - self._last_fetched_at
