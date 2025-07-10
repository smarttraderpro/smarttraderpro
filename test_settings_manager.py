"""
Unit tests for settings_manager.py
"""
import unittest
import os
import json
from settings_manager import SettingsManager, SETTINGS_FILE, DEFAULT_REFRESH_RATE, ALLOWED_REFRESH_RATES

class TestSettingsManager(unittest.TestCase):

    def setUp(self):
        """Ensure a clean state before each test."""
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        self.manager = SettingsManager(settings_file_path=SETTINGS_FILE)

    def tearDown(self):
        """Clean up the settings file after each test."""
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)

    def test_default_settings_creation(self):
        """Test if default settings are created when no file exists."""
        self.assertTrue(os.path.exists(SETTINGS_FILE))
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        self.assertEqual(settings["refresh_rate"], DEFAULT_REFRESH_RATE)
        self.assertEqual(self.manager.get_refresh_rate(), DEFAULT_REFRESH_RATE)

    def test_set_and_get_refresh_rate(self):
        """Test setting and getting a valid refresh rate."""
        test_rate = "5m"
        self.assertTrue(self.manager.set_refresh_rate(test_rate))
        self.assertEqual(self.manager.get_refresh_rate(), test_rate)

        # Verify it's saved to file
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        self.assertEqual(settings["refresh_rate"], test_rate)

    def test_set_invalid_refresh_rate(self):
        """Test setting an invalid refresh rate."""
        initial_rate = self.manager.get_refresh_rate()
        test_rate = "invalid_rate"
        self.assertFalse(self.manager.set_refresh_rate(test_rate))
        self.assertEqual(self.manager.get_refresh_rate(), initial_rate) # Should not change

        # Verify file content also remains unchanged for this key
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        self.assertEqual(settings["refresh_rate"], initial_rate)

    def test_allowed_refresh_rates(self):
        """Test all allowed refresh rates."""
        for rate in ALLOWED_REFRESH_RATES:
            self.assertTrue(self.manager.set_refresh_rate(rate))
            self.assertEqual(self.manager.get_refresh_rate(), rate)

    def test_load_existing_settings(self):
        """Test loading settings from an existing file."""
        # Create a settings file manually
        custom_rate = "10m"
        custom_settings = {"refresh_rate": custom_rate, "other_setting": "test_value"}
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(custom_settings, f)

        # Create a new manager instance to load from this file
        new_manager = SettingsManager(settings_file_path=SETTINGS_FILE)
        self.assertEqual(new_manager.get_refresh_rate(), custom_rate)
        # Check if other settings are preserved (though our manager only uses refresh_rate)
        self.assertEqual(new_manager.settings.get("other_setting"), "test_value")


    def test_load_corrupted_settings_file_json_error(self):
        """Test loading from a corrupted JSON file."""
        with open(SETTINGS_FILE, 'w') as f:
            f.write("this is not json")

        # Suppress print output during this test for cleaner test logs
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        new_manager = SettingsManager(settings_file_path=SETTINGS_FILE)

        sys.stdout = old_stdout # Restore stdout

        self.assertEqual(new_manager.get_refresh_rate(), DEFAULT_REFRESH_RATE)
        self.assertIn("Error loading settings file", captured_output.getvalue())
        self.assertIn("Using defaults", captured_output.getvalue())


    def test_load_settings_file_with_invalid_rate_value(self):
        """Test loading settings with an invalid refresh_rate value."""
        custom_settings = {"refresh_rate": "invalid_config_rate"}
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(custom_settings, f)

        new_manager = SettingsManager(settings_file_path=SETTINGS_FILE)
        self.assertEqual(new_manager.get_refresh_rate(), DEFAULT_REFRESH_RATE) # Should reset to default

        # Verify the file was corrected
        with open(SETTINGS_FILE, 'r') as f:
            corrected_settings = json.load(f)
        self.assertEqual(corrected_settings["refresh_rate"], DEFAULT_REFRESH_RATE)


    def test_get_current_refresh_interval_seconds(self):
        """Test the conversion of refresh rate string to seconds."""
        self.manager.set_refresh_rate("manual")
        self.assertIsNone(self.manager.get_current_refresh_interval_seconds())

        self.manager.set_refresh_rate("30s")
        self.assertEqual(self.manager.get_current_refresh_interval_seconds(), 30)

        self.manager.set_refresh_rate("1m")
        self.assertEqual(self.manager.get_current_refresh_interval_seconds(), 60)

        self.manager.set_refresh_rate("15m")
        self.assertEqual(self.manager.get_current_refresh_interval_seconds(), 15 * 60)

if __name__ == '__main__':
    unittest.main()
