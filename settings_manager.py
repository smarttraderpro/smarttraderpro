"""
Manages user settings, particularly for data refresh rates.

Settings are stored in a simple JSON file (`user_settings.json`).
Available refresh rates: 'manual', '30s', '1m', '2m', '5m', '10m', '15m'.
Default is 'manual'.
"""
import json
import os

SETTINGS_FILE = "user_settings.json"
DEFAULT_REFRESH_RATE = "manual"
ALLOWED_REFRESH_RATES = ["manual", "30s", "1m", "2m", "5m", "10m", "15m"]

def get_refresh_rate_seconds(rate_str):
    """Converts refresh rate string to seconds. 'manual' returns None."""
    if rate_str == "manual":
        return None
    if rate_str.endswith('s'):
        return int(rate_str[:-1])
    if rate_str.endswith('m'):
        return int(rate_str[:-1]) * 60
    return None # Should not happen if validation is correct

class SettingsManager:
    def __init__(self, settings_file_path=SETTINGS_FILE):
        self.settings_file_path = settings_file_path
        self.settings = self._load_settings()

    def _load_settings(self):
        """Loads settings from the JSON file."""
        if os.path.exists(self.settings_file_path):
            try:
                with open(self.settings_file_path, 'r') as f:
                    settings = json.load(f)
                    # Validate loaded settings
                    if "refresh_rate" not in settings or \
                       settings["refresh_rate"] not in ALLOWED_REFRESH_RATES:
                        settings["refresh_rate"] = DEFAULT_REFRESH_RATE
                        self._save_settings(settings) # Save corrected settings
                    return settings
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading settings file '{self.settings_file_path}': {e}. Using defaults.")
                return {"refresh_rate": DEFAULT_REFRESH_RATE}
        else:
            # Create default settings if file doesn't exist
            default_settings = {"refresh_rate": DEFAULT_REFRESH_RATE}
            self._save_settings(default_settings)
            return default_settings

    def _save_settings(self, settings_data):
        """Saves settings to the JSON file."""
        try:
            with open(self.settings_file_path, 'w') as f:
                json.dump(settings_data, f, indent=4)
        except IOError as e:
            print(f"Error saving settings to file '{self.settings_file_path}': {e}")

    def get_refresh_rate(self):
        """Returns the current refresh rate setting."""
        return self.settings.get("refresh_rate", DEFAULT_REFRESH_RATE)

    def set_refresh_rate(self, rate):
        """
        Sets the refresh rate.
        Rate must be one of ALLOWED_REFRESH_RATES.
        """
        if rate in ALLOWED_REFRESH_RATES:
            self.settings["refresh_rate"] = rate
            self._save_settings(self.settings)
            print(f"Refresh rate set to: {rate}")
            return True
        else:
            print(f"Invalid refresh rate: {rate}. Allowed rates are: {ALLOWED_REFRESH_RATES}")
            return False

    def get_current_refresh_interval_seconds(self):
        """
        Returns the current refresh interval in seconds.
        Returns None if rate is 'manual'.
        """
        current_rate_str = self.get_refresh_rate()
        return get_refresh_rate_seconds(current_rate_str)

# Example Usage (for testing purposes)
if __name__ == '__main__':
    manager = SettingsManager()
    print(f"Default/Current refresh rate: {manager.get_refresh_rate()}")
    print(f"Default/Current refresh interval seconds: {manager.get_current_refresh_interval_seconds()}")

    print("\n--- Setting refresh rate to '5m' ---")
    manager.set_refresh_rate("5m")
    print(f"New refresh rate: {manager.get_refresh_rate()}")
    print(f"New refresh interval seconds: {manager.get_current_refresh_interval_seconds()}")

    print("\n--- Setting refresh rate to 'invalid_rate' ---")
    manager.set_refresh_rate("invalid_rate") # Should fail
    print(f"Current refresh rate after invalid attempt: {manager.get_refresh_rate()}")

    print("\n--- Setting refresh rate to 'manual' ---")
    manager.set_refresh_rate("manual")
    print(f"New refresh rate: {manager.get_refresh_rate()}")
    print(f"New refresh interval seconds: {manager.get_current_refresh_interval_seconds()}")

    # Test persistence by creating another instance
    print("\n--- Testing persistence ---")
    manager2 = SettingsManager()
    print(f"Refresh rate from new instance: {manager2.get_refresh_rate()}") # Should be 'manual'

    # Clean up the created settings file for repeatable tests
    if os.path.exists(SETTINGS_FILE):
        os.remove(SETTINGS_FILE)
        print(f"\nCleaned up {SETTINGS_FILE}")
