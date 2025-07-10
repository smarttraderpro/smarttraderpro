"""
Unit tests for data_manager.py
"""
import unittest
from unittest.mock import MagicMock, patch, call
import time
import os

# Ensure modules are discoverable
from data_manager import DataManager, DataStore
from angelone_data_provider import AngelOneDataProvider # Mocked
from settings_manager import SettingsManager, SETTINGS_FILE # Real one, but with controlled file

# Keep a reference to the original time.sleep to avoid infinite loops in tests if not mocked properly
original_time_sleep = time.sleep

class TestDataManager(unittest.TestCase):

    def setUp(self):
        # Clean up settings file before each test if it exists from a previous run
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)

        self.mock_provider = MagicMock(spec=AngelOneDataProvider)
        self.settings_manager = SettingsManager(settings_file_path=SETTINGS_FILE) # Use real settings manager

        self.data_manager = DataManager(
            angelone_provider=self.mock_provider,
            settings_manager=self.settings_manager
        )
        # Define some tracked instruments for tests that need them
        self.data_manager.tracked_instruments = [
            {"exchange": "NSE", "tradingsymbol": "SBIN-EQ", "symboltoken": "3045"},
            {"exchange": "NSE", "tradingsymbol": "RELIANCE-EQ", "symboltoken": "2885"}
        ]

    def tearDown(self):
        """Clean up scheduler thread and settings file."""
        self.data_manager.stop_scheduler()
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        # Ensure any patches on time.sleep are stopped
        patch.stopall()


    def test_initialization(self):
        self.assertIsInstance(self.data_manager.data_store, DataStore)
        self.assertFalse(self.data_manager.is_authenticated)
        self.assertIsNone(self.data_manager._scheduler_thread)

    def test_perform_authentication_success(self):
        self.mock_provider.authenticate.return_value = True
        self.assertTrue(self.data_manager._perform_authentication(totp="123456"))
        self.assertTrue(self.data_manager.is_authenticated)
        self.mock_provider.authenticate.assert_called_once_with(totp="123456")

    def test_perform_authentication_failure(self):
        self.mock_provider.authenticate.return_value = False
        self.assertFalse(self.data_manager._perform_authentication(totp="123456"))
        self.assertFalse(self.data_manager.is_authenticated)

    def test_fetch_all_data_not_authenticated(self):
        self.data_manager.is_authenticated = False
        self.data_manager.fetch_all_data()
        self.mock_provider.get_ltp.assert_not_called()
        self.mock_provider.get_portfolio.assert_not_called()
        self.mock_provider.get_positions.assert_not_called()
        self.mock_provider.get_pnl.assert_not_called()

    def test_fetch_all_data_authenticated_success(self):
        self.data_manager.is_authenticated = True

        # Mock provider responses
        self.mock_provider.get_ltp.side_effect = [
            {"SBIN-EQ": 290.5}, # LTP for SBIN-EQ (mock structure from provider)
            {"RELIANCE-EQ": 2200.75}  # LTP for RELIANCE-EQ
        ]
        self.mock_provider.get_portfolio.return_value = {"status": True, "data": [{"symbol": "INFY", "qty": 10}]}
        self.mock_provider.get_positions.return_value = {"status": True, "data": [{"symbol": "NIFTYFUT", "qty": 1}]}
        self.mock_provider.get_pnl.return_value = {"status": True, "data": {"total_pnl": 100.50}}

        self.data_manager.fetch_all_data()

        # Check LTP calls
        self.mock_provider.get_ltp.assert_any_call(exchange="NSE", tradingsymbol="SBIN-EQ", symboltoken="3045")
        self.mock_provider.get_ltp.assert_any_call(exchange="NSE", tradingsymbol="RELIANCE-EQ", symboltoken="2885")
        self.assertEqual(self.data_manager.data_store.live_market_data["SBIN-EQ"], {"SBIN-EQ": 290.5}) # Provider returns the value, DM stores it as dict
        self.assertEqual(self.data_manager.data_store.live_market_data["RELIANCE-EQ"], {"RELIANCE-EQ": 2200.75})


        self.mock_provider.get_portfolio.assert_called_once()
        self.assertEqual(self.data_manager.data_store.portfolio, [{"symbol": "INFY", "qty": 10}])

        self.mock_provider.get_positions.assert_called_once()
        self.assertEqual(self.data_manager.data_store.positions, [{"symbol": "NIFTYFUT", "qty": 1}])

        self.mock_provider.get_pnl.assert_called_once_with(position_data=self.data_manager.data_store.positions)
        self.assertEqual(self.data_manager.data_store.pnl, {"total_pnl": 100.50})

        self.assertIsNotNone(self.data_manager.data_store.last_updated)

    def test_fetch_all_data_api_failures(self):
        self.data_manager.is_authenticated = True
        self.mock_provider.get_ltp.return_value = None # Simulate LTP failure
        self.mock_provider.get_portfolio.return_value = {"status": False, "message": "Portfolio fetch failed"}
        self.mock_provider.get_positions.return_value = {"status": False, "message": "Positions fetch failed"}
        self.mock_provider.get_pnl.return_value = {"status": False, "message": "PNL fetch failed"}

        initial_market_data = self.data_manager.data_store.live_market_data.copy()

        self.data_manager.fetch_all_data()

        # Data store should not be updated with failed data
        self.assertEqual(self.data_manager.data_store.live_market_data, initial_market_data) # No new LTPs
        self.assertIsNone(self.data_manager.data_store.portfolio) # Assuming it was None before
        self.assertIsNone(self.data_manager.data_store.positions)
        self.assertIsNone(self.data_manager.data_store.pnl)


    def test_manual_refresh(self):
        self.data_manager.is_authenticated = True # Assume authenticated
        with patch.object(self.data_manager, 'fetch_all_data') as mock_fetch:
            self.data_manager.manual_refresh()
            mock_fetch.assert_called_once_with(source="Manual")

    def test_manual_refresh_not_authenticated(self):
        self.data_manager.is_authenticated = False
        with patch.object(self.data_manager, 'fetch_all_data') as mock_fetch:
            self.data_manager.manual_refresh()
            mock_fetch.assert_not_called()

    def test_start_scheduler_manual_mode(self):
        self.settings_manager.set_refresh_rate("manual") # Ensure it's manual
        self.data_manager.is_authenticated = True # Authenticated
        self.data_manager.start_scheduler()
        self.assertIsNone(self.data_manager._scheduler_thread)

    def test_start_scheduler_not_authenticated(self):
        self.settings_manager.set_refresh_rate("30s") # Automatic mode
        self.data_manager.is_authenticated = False # Not authenticated
        self.data_manager.start_scheduler()
        self.assertIsNone(self.data_manager._scheduler_thread)


    @patch('data_manager.DataManager.fetch_all_data')
    @patch('time.monotonic')
    # Removed time.sleep patch as event.wait is now the focus
    def test_scheduler_loop_runs_and_stops(self, mock_monotonic, mock_fetch_all_data):
        self.data_manager.is_authenticated = True
        interval_seconds = 30  # Corresponds to "30s"
        self.settings_manager.set_refresh_rate("30s")

        # Mock monotonic to make the interval pass:
        # 1. Initial call for wait_start_time in _scheduler_loop
        # 2. First call in 'while' condition, time has not passed interval_seconds (loop continues)
        # 3. Second call in 'while' condition, time has passed interval_seconds (loop exits to else)

        class MonotonicMocker:
            def __init__(self, start_time=1000.0, default_increment=0.01):
                self.time = start_time
                self.default_increment = default_increment
                # Specific time points for the first fetch_all_data cycle
                self.defined_points = [
                    start_time,                             # Initial wait_start_time
                    start_time + interval_seconds / 2,      # Inner loop check 1 (true)
                    start_time + interval_seconds + 1       # Inner loop check 2 (false -> fetch)
                ]
                self.call_idx = 0

            def __call__(self):
                if self.call_idx < len(self.defined_points):
                    current_val = self.defined_points[self.call_idx]
                    self.time = current_val # Ensure self.time is updated to the last defined point
                else:
                    # After defined points, just increment from the last known time
                    self.time += self.default_increment
                    current_val = self.time
                self.call_idx += 1
                return current_val

        mock_monotonic.side_effect = MonotonicMocker(start_time=1000.0)

        # Patch the event's wait method directly for this test
        with patch.object(self.data_manager._stop_scheduler_event, 'wait') as mock_event_wait:

            def mock_wait_behavior(timeout_value):
                if self.data_manager._stop_scheduler_event.is_set():
                    return True
                return False

            mock_event_wait.side_effect = mock_wait_behavior

            self.data_manager.start_scheduler()
            self.assertIsNotNone(self.data_manager._scheduler_thread, "Scheduler thread object should exist.")
            self.assertTrue(self.data_manager._scheduler_thread.is_alive(), "Scheduler thread should be alive.")

            # Give the thread a very brief moment to execute the first fetch cycle.
            original_time_sleep(0.01) # Reduced real sleep

            # Stop the scheduler. This will set the event.
            # The mock_wait_behavior should now ensure the thread exits promptly.
            # But our mock_event_wait.return_value = False might override it if not careful.
            # However, stop_scheduler sets the event, then joins. The join is important.
            self.data_manager.stop_scheduler()

            if self.data_manager._scheduler_thread is not None: # Thread might be None if it exited fast
                 # Explicitly wait for the thread to finish.
                 # stop_scheduler already calls join, this is a safeguard for the test.
                self.data_manager._scheduler_thread.join(timeout=0.5)

        self.assertFalse(self.data_manager._scheduler_thread and self.data_manager._scheduler_thread.is_alive(), "Scheduler thread should be stopped and joined.")
        mock_fetch_all_data.assert_called_once_with(source="Scheduled")


    @patch('time.sleep', side_effect=lambda t: original_time_sleep(0.001))
    @patch('data_manager.DataManager.fetch_all_data')
    def test_scheduler_updates_on_settings_change(self, mock_fetch_all_data, mock_sleep):
        self.data_manager.is_authenticated = True
        self.settings_manager.set_refresh_rate("30s") # Use a valid rate
        self.data_manager.start_scheduler()

        self.assertTrue(self.data_manager._scheduler_thread and self.data_manager._scheduler_thread.is_alive(), "Scheduler should be alive after starting with 30s rate")
        original_time_sleep(0.05) # Let it run a bit

        # Change setting to manual
        self.settings_manager.set_refresh_rate("manual")
        self.data_manager.update_refresh_settings() # This should stop the scheduler

        self.assertFalse(self.data_manager._scheduler_thread and self.data_manager._scheduler_thread.is_alive(), "Scheduler should be stopped after setting to manual")

        # Change setting back to an interval
        self.settings_manager.set_refresh_rate("1m") # Different valid interval
        self.data_manager.update_refresh_settings() # This should start it again

        self.assertTrue(self.data_manager._scheduler_thread and self.data_manager._scheduler_thread.is_alive(), "Scheduler should be alive after restarting with 1m rate")

        original_time_sleep(0.05) # Let it run a bit more

        self.data_manager.stop_scheduler()


    def test_update_refresh_settings_starts_scheduler_if_not_manual_and_authenticated(self):
        self.data_manager.is_authenticated = True
        self.settings_manager.set_refresh_rate("5m") # Non-manual

        with patch.object(self.data_manager, 'start_scheduler') as mock_start_scheduler, \
             patch.object(self.data_manager, 'stop_scheduler') as mock_stop_scheduler:
            self.data_manager.update_refresh_settings()
            mock_stop_scheduler.assert_called_once()
            mock_start_scheduler.assert_called_once()

    def test_update_refresh_settings_stops_scheduler_if_manual(self):
        self.data_manager.is_authenticated = True
        self.settings_manager.set_refresh_rate("manual")

        # First start it with a non-manual rate
        self.settings_manager.set_refresh_rate("1m")
        self.data_manager.start_scheduler() # This would start a real thread
        self.assertTrue(self.data_manager._scheduler_thread and self.data_manager._scheduler_thread.is_alive())

        # Now change to manual and update
        self.settings_manager.set_refresh_rate("manual")
        self.data_manager.update_refresh_settings()

        self.assertFalse(self.data_manager._scheduler_thread and self.data_manager._scheduler_thread.is_alive())


if __name__ == '__main__':
    unittest.main()
