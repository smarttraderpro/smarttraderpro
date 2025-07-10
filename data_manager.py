"""
Manages data fetching and scheduling based on user settings.

Uses AngelOneDataProvider for API interactions and SettingsManager for refresh rate preferences.
Handles manual refresh and scheduled refreshes for market data, portfolio, etc.
"""
import time
import threading
from angelone_data_provider import AngelOneDataProvider # Hypothetical structure
from settings_manager import SettingsManager

# Placeholder for where data would be stored or emitted (e.g., a UI update queue, database)
class DataStore:
    def __init__(self):
        self.live_market_data = {}
        self.portfolio = None
        self.positions = None
        self.pnl = None
        self.last_updated = None

    def update_market_data(self, data):
        # In a real app, this would update specific instrument data
        self.live_market_data.update(data)
        print(f"DataStore: Market data updated - {data}")

    def update_portfolio(self, data):
        self.portfolio = data
        print(f"DataStore: Portfolio updated - {self.portfolio}")

    def update_positions(self, data):
        self.positions = data
        print(f"DataStore: Positions updated - {self.positions}")

    def update_pnl(self, data):
        self.pnl = data
        print(f"DataStore: P&L updated - {self.pnl}")

    def record_update_time(self):
        self.last_updated = time.time()
        print(f"DataStore: Last updated at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_updated))}")


class DataManager:
    def __init__(self, angelone_provider: AngelOneDataProvider, settings_manager: SettingsManager):
        self.provider = angelone_provider
        self.settings = settings_manager
        self.data_store = DataStore() # Simple in-memory store for this example
        self._scheduler_thread = None
        self._stop_scheduler_event = threading.Event()
        self.is_authenticated = False # Track authentication status

        # TODO: Define what instruments to track for live data
        # This would likely come from user input or a predefined list
        self.tracked_instruments = [
            # {"exchange": "NSE", "tradingsymbol": "SBIN-EQ", "symboltoken": "3045"},
            # {"exchange": "NSE", "tradingsymbol": "RELIANCE-EQ", "symboltoken": "2885"}
        ]

    def _perform_authentication(self, totp):
        """Authenticates with the provider."""
        # In a real app, client_code and api_key would be securely managed
        # and totp obtained from the user at login.
        # For this example, we assume provider is pre-configured or handles it.
        if self.provider.authenticate(totp=totp):
            self.is_authenticated = True
            print("DataManager: Authentication successful.")
            return True
        else:
            self.is_authenticated = False
            print("DataManager: Authentication failed.")
            return False

    def fetch_all_data(self, source="Scheduled"):
        """Fetches all relevant data: LTP, portfolio, positions, P&L."""
        if not self.is_authenticated:
            print("DataManager: Cannot fetch data, not authenticated.")
            # Optionally, try to re-authenticate or prompt user.
            # For now, we just skip if not authenticated.
            # A more robust solution would handle re-authentication if tokens expire.
            # self._perform_authentication("USER_TOTP_HERE") # This needs a way to get TOTP
            return

        print(f"DataManager: Fetching all data ({source})...")

        # Fetch Live Market Data for tracked instruments
        if self.tracked_instruments:
            for inst in self.tracked_instruments:
                ltp = self.provider.get_ltp(
                    exchange=inst["exchange"],
                    tradingsymbol=inst["tradingsymbol"],
                    symboltoken=inst["symboltoken"]
                )
                if ltp is not None:
                    # Storing by tradingsymbol for simplicity
                    market_update = {inst["tradingsymbol"]: ltp}
                    self.data_store.update_market_data(market_update)
        else:
            print("DataManager: No instruments tracked for live data.")

        # Fetch Portfolio
        portfolio_data = self.provider.get_portfolio()
        if portfolio_data and portfolio_data.get('status'):
            self.data_store.update_portfolio(portfolio_data['data'])
        else:
            print(f"DataManager: Failed to fetch portfolio - {portfolio_data.get('message') if portfolio_data else 'No response'}")


        # Fetch Positions
        position_data = self.provider.get_positions()
        if position_data and position_data.get('status'):
            self.data_store.update_positions(position_data['data'])
        else:
            print(f"DataManager: Failed to fetch positions - {position_data.get('message') if position_data else 'No response'}")


        # Fetch P&L (assuming it might use position data or be separate)
        pnl_data = self.provider.get_pnl(position_data=self.data_store.positions) # Pass current positions if needed
        if pnl_data and pnl_data.get('status'):
            self.data_store.update_pnl(pnl_data['data'])
        else:
            print(f"DataManager: Failed to fetch P&L - {pnl_data.get('message') if pnl_data else 'No response'}")

        self.data_store.record_update_time()
        print(f"DataManager: Data fetch complete ({source}).")

    def manual_refresh(self):
        """Triggers a manual refresh of all data."""
        print("DataManager: Manual refresh triggered.")
        # Potentially re-authenticate if necessary, or ensure session is valid
        if not self.is_authenticated:
             print("DataManager: Please authenticate first to perform a manual refresh.")
             # Here you might trigger an authentication flow if desired
             # For example: self._perform_authentication(input("Enter TOTP: "))
             # For now, we'll just return if not authenticated.
             return
        self.fetch_all_data(source="Manual")

    def _scheduler_loop(self):
        """
        Internal loop for scheduled data fetching.
        Runs in a separate thread.
        """
        while not self._stop_scheduler_event.is_set():
            interval_seconds = self.settings.get_current_refresh_interval_seconds()
            if interval_seconds is None: # 'manual' mode
                # If switched to manual, just wait and check periodically
                self._stop_scheduler_event.wait(5) # Check every 5s if settings changed
                continue

            print(f"DataManager Scheduler: Next run in {interval_seconds} seconds.")
            # Wait for the interval, but break early if stop event is set or interval changes
            # This makes the scheduler responsive to settings changes.
            wait_start_time = time.monotonic()
            while (time.monotonic() - wait_start_time) < interval_seconds:
                if self._stop_scheduler_event.wait(0.5): # Check every 0.5s
                    return # Exit loop if stop event is set
                # Check if interval changed mid-wait
                current_interval_setting = self.settings.get_current_refresh_interval_seconds()
                if current_interval_setting != interval_seconds:
                    print("DataManager Scheduler: Refresh interval changed. Restarting wait.")
                    break # Restart outer while loop to get new interval
            else: # Executed if the inner while loop wasn't broken by settings change or stop event
                if not self._stop_scheduler_event.is_set():
                    self.fetch_all_data(source="Scheduled")


    def start_scheduler(self):
        """Starts the data fetching scheduler if not in 'manual' mode."""
        if self.settings.get_refresh_rate() == "manual":
            print("DataManager: Refresh rate is 'manual'. Scheduler not started.")
            return

        if not self.is_authenticated:
            print("DataManager: Cannot start scheduler, not authenticated.")
            # Attempt authentication first. This needs a TOTP.
            # For this example, we'll assume authentication must happen before starting scheduler.
            # In a real app, this might be tied to a login process.
            # totp_for_auto_start = input("Enter TOTP to start scheduler: ") # This is not ideal for an automated agent
            # if not self._perform_authentication(totp_for_auto_start):
            #     return
            print("DataManager: Please authenticate before starting the scheduler.")
            return


        if self._scheduler_thread and self._scheduler_thread.is_alive():
            print("DataManager: Scheduler already running.")
            return

        self._stop_scheduler_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        print("DataManager: Scheduler started.")

    def stop_scheduler(self):
        """Stops the data fetching scheduler."""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._stop_scheduler_event.set()
            self._scheduler_thread.join(timeout=5) # Wait for thread to finish
            if self._scheduler_thread.is_alive():
                print("DataManager: Scheduler thread did not stop in time.")
            else:
                print("DataManager: Scheduler stopped.")
        self._scheduler_thread = None


    def update_refresh_settings(self):
        """
        Call this when refresh rate setting changes in SettingsManager.
        It will stop and restart the scheduler if necessary.
        """
        print("DataManager: Refresh settings updated. Restarting scheduler if needed.")
        self.stop_scheduler() # Stop any existing scheduler
        # If new setting is not manual, and we are authenticated, start it again.
        if self.settings.get_refresh_rate() != "manual" and self.is_authenticated:
            self.start_scheduler()
        elif not self.is_authenticated and self.settings.get_refresh_rate() != "manual":
            print("DataManager: Refresh rate is automatic, but not authenticated. Scheduler not started.")


# Example Usage (Conceptual - would need actual provider and UI interaction)
if __name__ == '__main__':
    # 1. Setup (normally done at app startup)
    # These would come from secure storage or user login
    API_KEY = "YOUR_API_KEY"
    CLIENT_CODE = "YOUR_CLIENT_CODE"
    # Password/TOTP would be entered by user during an auth flow

    # Initialize components
    # Actual provider would need real credentials and smartapi library
    mock_provider = AngelOneDataProvider(api_key=API_KEY, client_code=CLIENT_CODE)
    settings_mgr = SettingsManager()
    data_mgr = DataManager(angelone_provider=mock_provider, settings_manager=settings_mgr)

    # --- Authentication Step (simulate user logging in) ---
    print("\n--- Simulating User Authentication ---")
    # In a real app, TOTP is provided by the user.
    # For this test, we'll use a placeholder. The mock provider will "succeed".
    user_totp = "123456" # Placeholder TOTP
    if data_mgr._perform_authentication(totp=user_totp):
        print("Authentication successful. DataManager is now authenticated.")
    else:
        print("Authentication failed. DataManager is not authenticated.")
        # Exit if auth fails, as further operations depend on it
        exit()

    # Add some instruments to track for LTP
    data_mgr.tracked_instruments = [
        {"exchange": "NSE", "tradingsymbol": "SBIN-EQ", "symboltoken": "3045"},
        {"exchange": "NSE", "tradingsymbol": "RELIANCE-EQ", "symboltoken": "2885"}
    ]

    # --- Manual Refresh Example ---
    print("\n--- Simulating Manual Refresh ---")
    data_mgr.manual_refresh()
    print(f"DataStore after manual refresh: Market: {data_mgr.data_store.live_market_data}, Portfolio: {data_mgr.data_store.portfolio is not None}")

    # --- Scheduled Refresh Example ---
    print("\n--- Simulating Scheduled Refresh (30s) ---")
    # User changes setting via a hypothetical UI, which calls settings_mgr.set_refresh_rate()
    # Then, the UI (or a controller) would call data_mgr.update_refresh_settings()

    settings_mgr.set_refresh_rate("30s") # User sets to 30 seconds
    data_mgr.update_refresh_settings()   # Notify DataManager of the change

    try:
        print("Scheduler running for a bit (e.g., 70 seconds to see two fetches)... Press Ctrl+C to stop.")
        time.sleep(70)
    except KeyboardInterrupt:
        print("Manual interruption.")
    finally:
        print("\n--- Simulating Setting to Manual and Stopping Scheduler ---")
        settings_mgr.set_refresh_rate("manual")
        data_mgr.update_refresh_settings() # This will stop the scheduler
        print("DataManager example finished.")

    # Clean up settings file
    if os.path.exists(settings_mgr.settings_file_path):
        os.remove(settings_mgr.settings_file_path)
        print(f"\nCleaned up {settings_mgr.settings_file_path}")
