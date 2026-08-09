import json
import os
from dataclasses import dataclass, asdict, field

@dataclass
class AppSettings:
    flip_horizontal: bool = False
    flip_vertical: bool = False
    zoom_level: float = 1.0
    brightness: int = 0
    contrast: int = 0
    saturation: int = 0
    camera_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 60
    fast_start: bool = True

class StateManager:
    def __init__(self, config_path="settings.json"):
        self.config_path = config_path
        self._save_timer = None
        self._dirty = False
        self.settings = self.load_settings()

    def load_settings(self) -> AppSettings:
        default_settings = AppSettings()
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Robust validation and fallback to defaults
                validated_data = {}
                for key, default_val in asdict(default_settings).items():
                    if key in data:
                        val = data[key]
                        if key in ["flip_horizontal", "flip_vertical", "fast_start"]:
                            validated_data[key] = val if isinstance(val, bool) else default_val
                        elif key == "zoom_level":
                            try:
                                zoom = float(val)
                                validated_data[key] = zoom if 1.0 <= zoom <= 3.0 else default_val
                            except (ValueError, TypeError):
                                validated_data[key] = default_val
                        elif key in ["brightness", "contrast", "saturation"]:
                            try:
                                ival = int(val)
                                validated_data[key] = ival if -100 <= ival <= 100 else default_val
                            except (ValueError, TypeError):
                                validated_data[key] = default_val
                        elif key in ["camera_index", "width", "height", "fps"]:
                            try:
                                ival = int(val)
                                if key == "camera_index":
                                    validated_data[key] = ival if ival >= 0 else default_val
                                elif key == "width":
                                    validated_data[key] = ival if 320 <= ival <= 3840 else default_val
                                elif key == "height":
                                    validated_data[key] = ival if 240 <= ival <= 2160 else default_val
                                elif key == "fps":
                                    validated_data[key] = ival if 1 <= ival <= 120 else default_val
                            except (ValueError, TypeError):
                                validated_data[key] = default_val
                        else:
                            validated_data[key] = default_val
                    else:
                        validated_data[key] = default_val
                
                return AppSettings(**validated_data)
            except Exception as e:
                print(f"Error loading settings: {e}")
        return default_settings

    def save_settings(self):
        """Immediately write settings to disk."""
        self._write_to_disk()

    def _write_to_disk(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(asdict(self.settings), f, indent=4)
            self._dirty = False
        except Exception as e:
            print(f"Error saving settings: {e}")

    def save_settings_debounced(self):
        """Debounce write operations to prevent disk thrashing on slider movement."""
        from PyQt6.QtCore import QTimer
        # Use single-shot QTimer for 300ms debouncing
        if self._save_timer is None:
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.setInterval(300)
            self._save_timer.timeout.connect(self._write_to_disk)
        self._save_timer.start()

    def update_setting(self, key, value):
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self._dirty = True
            self.save_settings_debounced()

    def flush(self):
        """Flush any pending saves immediately (e.g. on application exit)."""
        if self._dirty:
            if self._save_timer:
                self._save_timer.stop()
            self._write_to_disk()


