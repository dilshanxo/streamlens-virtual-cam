import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state_manager import StateManager
from src.ui_main import StreamLensUI

# Ensure QApplication is initialized for testing
app = QApplication.instance()
if app is None:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication(sys.argv)

class TestStreamLensUI(unittest.TestCase):
    def setUp(self):
        self.state_manager = StateManager(config_path="dummy_settings.json")
        # Clean up any dummy config
        if os.path.exists("dummy_settings.json"):
            try:
                os.remove("dummy_settings.json")
            except OSError:
                pass
        self.ui = StreamLensUI(self.state_manager)

    def tearDown(self):
        self.ui.close()
        if os.path.exists("dummy_settings.json"):
            try:
                os.remove("dummy_settings.json")
            except OSError:
                pass

    def test_ui_components_exist(self):
        # Verify essential UI elements are created and configured correctly
        self.assertIsNotNone(self.ui.video_label)
        self.assertIsNotNone(self.ui.panel_camera)
        self.assertIsNotNone(self.ui.panel_transform)
        self.assertIsNotNone(self.ui.panel_color)
        self.assertIn("Brightness", self.ui._sliders)
        self.assertIn("Contrast", self.ui._sliders)
        self.assertIn("Saturation", self.ui._sliders)

    def test_ui_syncs_with_state_manager(self):
        # Verify that altering UI controls successfully propagates settings back to StateManager
        
        # 1. Flip horizontal toggle click simulation
        self.ui._toggle_flip_h.click()
        self.ui.state_manager.flush()
        self.assertTrue(self.state_manager.settings.flip_horizontal)

        # 2. Brightness slider value change
        self.ui._sliders["Brightness"].setValue(45)
        self.ui.state_manager.flush()
        self.assertEqual(self.state_manager.settings.brightness, 45)

        # 3. Zoom adjustment
        self.ui._adjust_zoom(0.5)
        self.ui.state_manager.flush()
        self.assertAlmostEqual(self.state_manager.settings.zoom_level, 1.5)

        # 4. Fast Camera Start toggle click simulation
        self.ui._toggle_fast_start.click()
        self.ui.state_manager.flush()
        self.assertFalse(self.state_manager.settings.fast_start)

    def test_frame_ready_displays_image(self):
        # Create a dummy QImage and pass to _on_frame_ready
        img = QImage(16, 16, QImage.Format.Format_BGR888)
        img.fill(Qt.GlobalColor.blue)
        
        # Call frame ready slot
        self.ui._on_frame_ready(img)
        
        # The video_label pixmap should be set
        self.assertIsNotNone(self.ui.video_label.pixmap())
