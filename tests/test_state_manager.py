import unittest
import os
import json
import tempfile
from src.state_manager import StateManager, AppSettings

class TestStateManager(unittest.TestCase):
    def setUp(self):
        # Create a secure temporary file path for testing JSON configuration
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        # Clean up the temporary file after each test
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def test_default_settings(self):
        # Test that state manager loads defaults when file does not exist
        os.remove(self.temp_file_path) # Ensure file doesn't exist
        manager = StateManager(config_path=self.temp_file_path)
        
        self.assertIsInstance(manager.settings, AppSettings)
        self.assertEqual(manager.settings.zoom_level, 1.0)
        self.assertFalse(manager.settings.flip_horizontal)
        self.assertEqual(manager.settings.brightness, 0)

    def test_save_and_load_settings(self):
        # Save custom settings and verify they are loaded properly
        manager = StateManager(config_path=self.temp_file_path)
        manager.settings.brightness = 25
        manager.settings.contrast = -15
        manager.settings.flip_horizontal = True
        manager.settings.fast_start = False
        manager.save_settings()

        # Instantiate a new manager reading from the same file
        new_manager = StateManager(config_path=self.temp_file_path)
        self.assertEqual(new_manager.settings.brightness, 25)
        self.assertEqual(new_manager.settings.contrast, -15)
        self.assertTrue(new_manager.settings.flip_horizontal)
        self.assertFalse(new_manager.settings.flip_vertical)
        self.assertFalse(new_manager.settings.fast_start)

    def test_update_setting(self):
        # Verify update_setting safely updates in-memory and saves to disk
        manager = StateManager(config_path=self.temp_file_path)
        manager.update_setting("zoom_level", 2.5)
        manager.flush()
        self.assertEqual(manager.settings.zoom_level, 2.5)

        # Check raw file contents to verify write occurred
        with open(self.temp_file_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["zoom_level"], 2.5)

    def test_invalid_json_handling(self):
        # Write corrupted JSON to settings and verify StateManager handles it gracefully by falling back to defaults
        with open(self.temp_file_path, 'w') as f:
            f.write("{corrupt: json...")

        manager = StateManager(config_path=self.temp_file_path)
        self.assertEqual(manager.settings.brightness, 0) # Back to defaults
        self.assertEqual(manager.settings.zoom_level, 1.0)
