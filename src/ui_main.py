"""
StreamLens – Premium Light Theme UI
ui_main.py

Matches the high-fidelity reference designs exactly with Custom SVG Assets.
Includes robust fallback mechanisms for missing icons and perfect aspect ratio scaling.
"""

import sys
import os

# Dynamically add the project root directory to sys.path to resolve 'src' imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QFrame,
    QApplication,
    QAbstractButton,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QSize,
    QRect,
    QPropertyAnimation,
    pyqtProperty,
    QEasingCurve,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QColor,
    QFont,
    QPainter,
    QBrush,
    QPen,
    QFontDatabase,
    QPainterPath,
    QIcon,
)

try:
    from pygrabber.dshow_graph import FilterGraph
except ImportError:
    FilterGraph = None


def get_asset(name: str) -> str:
    """Resolve asset path reliably for both normal run and PyInstaller EXE."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, "assets", name)


# ---------------------------------------------------------------------------
# Font family – dynamically retrieved from the native system default
# ---------------------------------------------------------------------------
_FONT_FAMILY = "Gelion"


# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
CLR_BG = "#FFFFFF"
CLR_WHITE = "#FFFFFF"
CLR_GRAY_BG = "#FBFBFB"
CLR_PANEL_BG = "#FFFFFF"
CLR_BORDER = "#EBEBEB"
CLR_TEXT_DARK = "#151515"
CLR_TEXT_MED = "#6B7280"
CLR_TEXT_LIGHT = "#9CA3AF"
CLR_PLACEHOLDER = "#E5E7EB"
CLR_TOGGLE_ON = "#151515"
CLR_TOGGLE_OFF = "#D1D5DB"
CLR_SLIDER_GRV = "#E5E7EB"
CLR_SLIDER_HDL = "#151515"
CLR_ACTIVE_INDICATOR = "#151515"


# ===========================================================================
# ModernToggle – animated iOS pill toggle
# ===========================================================================
class ModernToggle(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(48, 26)
        self._thumb_x: float = 3.0

        self._anim = QPropertyAnimation(self, b"thumb_x", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    @pyqtProperty(float)
    def thumb_x(self):
        return self._thumb_x

    @thumb_x.setter
    def thumb_x(self, v: float):
        self._thumb_x = v
        self.update()

    def _thumb_end(self) -> float:
        return self.width() - self.height() + 3.0

    def hitButton(self, pos: QPoint) -> bool:
        return self.contentsRect().contains(pos)

    def nextCheckState(self):
        super().nextCheckState()
        start = self._thumb_x
        end = self._thumb_end() if self.isChecked() else 3.0
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self.height() / 2
        track_color = QColor(CLR_TOGGLE_ON if self.isChecked() else CLR_TOGGLE_OFF)
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), r, r)

        thumb_d = self.height() - 6
        p.setBrush(QBrush(QColor(CLR_WHITE)))
        p.drawEllipse(int(self._thumb_x), 3, thumb_d, thumb_d)
        p.end()


# ===========================================================================
# FloatingPanel – white rounded card with drop shadow
# ===========================================================================
class FloatingPanel(QFrame):
    def __init__(self, parent=None, title: str = "", width: int = 290):
        super().__init__(parent)
        self.setObjectName("FloatingPanel")
        self.setFixedWidth(width)

        self.setStyleSheet(f"""
            QFrame#FloatingPanel {{
                background-color: {CLR_PANEL_BG};
                border-radius: 18px;
                border: 1px solid {CLR_BORDER};
            }}
        """)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(40)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self._shadow.setOffset(0, 12)
        self.setGraphicsEffect(self._shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 18, 22, 20)
        outer.setSpacing(14)

        if title:
            hdr = QLabel(title)
            hdr.setStyleSheet(f"""
                color: {CLR_TEXT_MED};
                font-family: '{_FONT_FAMILY}';
                font-size: 12px;
                font-weight: 500;
                letter-spacing: 0.3px;
            """)
            outer.addWidget(hdr)

        self.body_layout = outer
        self.hide()

    def sizeHint(self) -> QSize:
        return self.layout().sizeHint()


# ===========================================================================
# Helper builders
# ===========================================================================
def _label(
    text: str, size: int = 13, weight: int = 500, color: str = CLR_TEXT_DARK
) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {color}; font-family: '{_FONT_FAMILY}'; "
        f"font-size: {size}px; font-weight: {weight}; background: transparent;"
    )
    return lbl


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {CLR_BORDER}; border: none;")
    return line


def _add_shadow(widget, blur=18, dy=5, alpha=22):
    sh = QGraphicsDropShadowEffect(widget)
    sh.setBlurRadius(blur)
    sh.setColor(QColor(0, 0, 0, alpha))
    sh.setOffset(0, dy)
    widget.setGraphicsEffect(sh)


# ===========================================================================
# StreamLensUI – main window
# ===========================================================================
class StreamLensUI(QMainWindow):
    settings_changed = pyqtSignal(
        str, object
    )  # Emit setting key and new value thread-safely

    def __init__(self, state_manager=None):
        super().__init__()
        self.state_manager = state_manager
        self.settings = state_manager.settings if state_manager else _FallbackSettings()
        self.engine = None
        self._cam_active = False

        global _FONT_FAMILY
        font_path = get_asset("Inter_18pt-Regular.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    _FONT_FAMILY = families[0]
                    print(f"Loaded Font Family: {_FONT_FAMILY}")

        app = QApplication.instance()
        if app:
            app.setFont(QFont(_FONT_FAMILY, 10))

        self.setWindowTitle("Stream Lens")
        self._apply_native_light_titlebar()
        self.resize(900, 480)
        self.setMinimumSize(600, 420)

        # Apply global double lock stylesheet to ensure fonts propagate to all child widgets
        self.setStyleSheet(f"""
            * {{
                font-family: '{_FONT_FAMILY}';
            }}
        """)

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.central.setStyleSheet(f"background: {CLR_BG};")

        self.video_label = QLabel(self.central)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet(f"background: {CLR_BG};")

        # We DO NOT use setScaledContents(True) here to prevent aspect ratio stretching

        self._build_floating_panels()
        self._build_bottom_bar()

        # Delay drawing placeholder until layout is initialized to get proper size
        self._draw_placeholder()

        self.panel_camera.raise_()
        self.panel_transform.raise_()
        self.panel_color.raise_()
        self.bottom_bar.raise_()

    def _apply_native_light_titlebar(self):
        """Uses Windows API via ctypes to force the title bar to light mode."""
        if sys.platform != "win32":
            return

        try:
            import ctypes
            from ctypes.wintypes import HWND, DWORD

            # Windows 11 / Windows 10 (Build 17763+) DWMWA_USE_IMMERSIVE_DARK_MODE constant
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            # For older Windows 10 versions, the constant is 19
            # DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19

            # Value to set: 0 = Light Mode, 1 = Dark Mode
            set_theme_value = ctypes.c_int(0)

            hwnd = HWND(int(self.winId()))

            # Call DwmSetWindowAttribute
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE),
                ctypes.byref(set_theme_value),
                ctypes.sizeof(set_theme_value),
            )
        except Exception as e:
            print(f"[StreamLens] Failed to set native title bar theme: {e}")

    def _draw_placeholder(self):
        """Load and display the user placeholder SVG/PNG asset with correct aspect ratio and spacing."""
        placeholder = get_asset("user_placeholder_light.jpg")

        if placeholder and os.path.exists(placeholder):
            # Fallback size if window hasn't properly resized yet
            label_w = (
                self.video_label.width() if self.video_label.width() > 100 else 900
            )
            label_h = (
                self.video_label.height() if self.video_label.height() > 100 else 480
            )

            # --- Spacing (Padding) Logic ---
            # 0.7 kiyanne full size eken 70% k witharak image eka gannawa kiyana eka.
            # Meka 0.5 (50%) hari 0.8 (80%) hari kalala oyata ona widiyata spacing eka wenas karaganna puluwan.
            padding_factor = 0.5
            target_w = int(label_w * padding_factor)
            target_h = int(label_h * padding_factor)

            pixmap = QPixmap(placeholder)
            scaled_pixmap = pixmap.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.video_label.setPixmap(scaled_pixmap)
        else:
            self.video_label.setText("Placeholder SVG/PNG not found in assets")

    def _build_floating_panels(self):
        # ---- Camera Devices ------------------------------------------------
        self.panel_camera = FloatingPanel(self.central, "Camera Devices", width=280)

        active_row = QWidget()
        active_row.setStyleSheet("background: transparent;")
        ar_layout = QHBoxLayout(active_row)
        ar_layout.setContentsMargins(0, 4, 0, 4)
        ar_layout.setSpacing(10)

        indicator = QFrame()
        indicator.setFixedSize(3, 20)
        indicator.setStyleSheet(
            f"background: {CLR_ACTIVE_INDICATOR}; border-radius: 2px;"
        )

        self.lbl_active_cam = _label("WSC 1.0 Built-in Camera", 13, 600, CLR_TEXT_DARK)
        ar_layout.addWidget(indicator)
        ar_layout.addWidget(self.lbl_active_cam, 1)
        self.panel_camera.body_layout.addWidget(active_row)
        self.panel_camera.body_layout.addWidget(_divider())

        # Dynamic layout for camera buttons instead of QComboBox
        self.cam_list_layout = QVBoxLayout()
        self.cam_list_layout.setContentsMargins(0, 0, 0, 0)
        self.cam_list_layout.setSpacing(4)
        self.panel_camera.body_layout.addLayout(self.cam_list_layout)

        self._populate_cameras()

        self.panel_camera.body_layout.addWidget(_divider())
        
        note_lbl = _label("Output: Select 'OBS Virtual Camera' in your apps", 11, 400, CLR_TEXT_LIGHT)
        note_lbl.setWordWrap(True)
        self.panel_camera.body_layout.addWidget(note_lbl)

        self.panel_camera.body_layout.addWidget(_divider())
        self._toggle_fast_start = self._add_toggle_row(
            self.panel_camera,
            "Fast Camera Start",
            self.settings.fast_start,
            self._on_fast_start_changed,
        )

        # ---- Transformations -----------------------------------------------
        self.panel_transform = FloatingPanel(self.central, "Transformations", width=280)
        self._toggle_flip_h = self._add_toggle_row(
            self.panel_transform,
            "Flip Horizontal",
            self.settings.flip_horizontal,
            self._on_flip_h_changed,
        )
        self.panel_transform.body_layout.addWidget(_divider())
        self._toggle_flip_v = self._add_toggle_row(
            self.panel_transform,
            "Flip Vertical",
            self.settings.flip_vertical,
            self._on_flip_v_changed,
        )

        # ---- Color Settings ------------------------------------------------
        self.panel_color = FloatingPanel(self.central, "Color Settings", width=310)

        icons = {
            "Brightness": "brightness.svg",
            "Contrast": "contrast.svg",
            "Saturation": "saturation.svg",
        }
        defaults = {
            "Brightness": self.settings.brightness,
            "Contrast": self.settings.contrast,
            "Saturation": self.settings.saturation,
        }
        callbacks = {
            "Brightness": self._on_brightness_changed,
            "Contrast": self._on_contrast_changed,
            "Saturation": self._on_saturation_changed,
        }

        self._sliders = {}
        for i, name in enumerate(["Brightness", "Contrast", "Saturation"]):
            if i > 0:
                self.panel_color.body_layout.addWidget(_divider())
            self._sliders[name] = self._add_slider_row(
                self.panel_color,
                name,
                icons[name],
                -100,
                100,
                defaults[name],
                callbacks[name],
            )

    def _add_toggle_row(
        self, panel: FloatingPanel, label: str, checked: bool, callback
    ) -> ModernToggle:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 6, 0, 6)
        rl.setSpacing(12)

        lbl = _label(label, 13, 500, CLR_TEXT_DARK)
        toggle = ModernToggle()
        toggle.setChecked(checked)
        toggle.clicked.connect(callback)

        rl.addWidget(lbl, 1)
        rl.addWidget(toggle)
        panel.body_layout.addWidget(row)
        return toggle

    def _add_slider_row(
        self,
        panel: FloatingPanel,
        label: str,
        icon_file: str,
        min_v: int,
        max_v: int,
        curr_v: int,
        callback,
    ) -> QSlider:
        panel.body_layout.addWidget(_label(label, 13, 600, CLR_TEXT_DARK))

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 2, 0, 6)
        rl.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setFixedWidth(20)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        svg_path = get_asset(icon_file)
        if os.path.exists(svg_path):
            pixmap = QIcon(svg_path).pixmap(QSize(16, 16))
            icon_lbl.setPixmap(pixmap)
        else:
            icon_lbl.setText("?")

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(curr_v)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 4px; background: {CLR_SLIDER_GRV}; border-radius: 2px; }}
            QSlider::sub-page:horizontal {{ background: {CLR_TEXT_DARK}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {CLR_SLIDER_HDL}; width: 20px; height: 20px; margin: -8px 0; border-radius: 10px; }}
        """)
        slider.valueChanged.connect(callback)

        val_lbl = _label(str(curr_v), 13, 700, CLR_TEXT_DARK)
        val_lbl.setFixedWidth(30)
        val_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        slider.valueChanged.connect(lambda v, l=val_lbl: l.setText(str(v)))

        rl.addWidget(icon_lbl)
        rl.addWidget(slider, 1)
        rl.addWidget(val_lbl)
        panel.body_layout.addWidget(row)
        return slider

    def _build_bottom_bar(self):
        self.bottom_bar = QWidget(self.central)
        self.bottom_bar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.bottom_bar.setFixedHeight(96)

        layout = QHBoxLayout(self.bottom_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # ── Left: camera pill ──────────────────────
        self.cam_pill = QFrame()
        self.cam_pill.setObjectName("CamPill")
        self.cam_pill.setFixedHeight(52)
        self.cam_pill.setStyleSheet(f"""
            QFrame#CamPill {{
                background: {CLR_GRAY_BG};
                border-radius: 26px;
                border: 1px solid {CLR_BORDER};
            }}
        """)
        _add_shadow(self.cam_pill, blur=20, dy=6, alpha=20)

        cam_pill_l = QHBoxLayout(self.cam_pill)
        cam_pill_l.setContentsMargins(6, 6, 10, 6)
        cam_pill_l.setSpacing(0)

        self.btn_cam = QPushButton()
        self.btn_cam.setFixedSize(40, 40)
        self.btn_cam.setStyleSheet(self._circle_btn_style(40))

        video_off_icon = QIcon(get_asset("video_off.svg"))
        if not video_off_icon.isNull():
            self.btn_cam.setIcon(video_off_icon)
            self.btn_cam.setIconSize(QSize(22, 22))
        else:
            self.btn_cam.setText("📷")

        self.btn_cam.clicked.connect(self._toggle_stream)

        sep = QFrame()
        sep.setFixedSize(1, 22)
        sep.setStyleSheet(f"background: {CLR_BORDER}; border: none;")

        self.btn_cam_dropdown = QPushButton()
        self.btn_cam_dropdown.setFixedSize(28, 40)
        self.btn_cam_dropdown.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {CLR_TEXT_DARK}; font-size: 16px; }}
            QPushButton:hover {{ background: #F3F4F6; border-radius: 14px; }}
        """)

        arrow_icon = QIcon(get_asset("down_arrow.jpg"))
        if arrow_icon.isNull():
            self.btn_cam_dropdown.setText("▾")
        else:
            self.btn_cam_dropdown.setIcon(arrow_icon)
            self.btn_cam_dropdown.setIconSize(QSize(20, 20))

        self.btn_cam_dropdown.clicked.connect(
            lambda: self._toggle_panel(self.panel_camera)
        )

        cam_pill_l.addWidget(self.btn_cam)
        cam_pill_l.addSpacing(4)
        cam_pill_l.addWidget(sep)
        cam_pill_l.addWidget(self.btn_cam_dropdown)

        layout.addWidget(self.cam_pill, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()

        # ── Centre: transform + color buttons ──────────────────────────────
        centre_row = QHBoxLayout()
        centre_row.setSpacing(14)

        # Passing fallback text symbols in case SVGs are missing
        self.btn_transform = self._make_icon_btn(
            "transform.jpg", "⛶", self.panel_transform
        )
        self.btn_color = self._make_icon_btn("color.jpg", "⊛", self.panel_color)

        centre_row.addWidget(self.btn_transform)
        centre_row.addWidget(self.btn_color)

        layout.addLayout(centre_row)
        layout.addStretch()

        # ── Right: zoom pill ───────────────────────────────────────────────
        self.zoom_pill = QFrame()
        self.zoom_pill.setObjectName("ZoomPill")
        self.zoom_pill.setFixedHeight(52)
        self.zoom_pill.setStyleSheet(f"""
            QFrame#ZoomPill {{
                background: {CLR_GRAY_BG};
                border-radius: 26px;
                border: 1px solid {CLR_BORDER};
            }}
        """)
        _add_shadow(self.zoom_pill, blur=20, dy=6, alpha=20)

        zoom_l = QHBoxLayout(self.zoom_pill)
        zoom_l.setContentsMargins(10, 0, 10, 0)
        zoom_l.setSpacing(3)

        btn_minus = self._pill_btn("minus.svg", "−", lambda: self._adjust_zoom(-0.1))
        self.lbl_zoom = _label(
            f"{self.settings.zoom_level * 100:.0f}%", 14, 600, CLR_TEXT_DARK
        )
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setFixedWidth(52)
        btn_plus = self._pill_btn("plus.svg", "+", lambda: self._adjust_zoom(0.1))

        zoom_l.addWidget(btn_minus)
        zoom_l.addWidget(self.lbl_zoom)
        zoom_l.addWidget(btn_plus)

        layout.addWidget(self.zoom_pill, 0, Qt.AlignmentFlag.AlignVCenter)

    def _circle_btn_style(self, size: int, bg: str = "transparent") -> str:
        return f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-radius: {size // 2}px;
                color: {CLR_TEXT_DARK};
                font-size: 18px;
            }}
            QPushButton:hover {{ background: #F3F4F6; }}
            QPushButton:pressed {{ background: #E5E7EB; }}
        """

    def _make_icon_btn(
        self, icon_file: str, fallback_text: str, panel: FloatingPanel
    ) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(70, 52)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {CLR_GRAY_BG};
                border: 1px solid {CLR_BORDER};
                border-radius: 26px;
                color: {CLR_TEXT_DARK};
                font-size: 22px;
            }}
            QPushButton:hover {{ background: #F9FAFB; }}
            QPushButton:pressed {{ background: #F3F4F6; }}
        """)

        icon = QIcon(get_asset(icon_file))
        if icon.isNull():
            btn.setText(fallback_text)
        else:
            btn.setIcon(icon)
            btn.setIconSize(QSize(22, 22))

        _add_shadow(btn, blur=20, dy=6, alpha=20)
        btn.clicked.connect(lambda: self._toggle_panel(panel))
        return btn

    def _pill_btn(self, icon_file: str, fallback_text: str, callback) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(36, 36)
        btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {CLR_GRAY_BG}; 
                border: none; 
                border-radius: 18px; 
                color: {CLR_TEXT_MED}; 
                font-size: 20px; 
                font-weight: 600; 
                font-family: '{_FONT_FAMILY}';
            }}
            QPushButton:hover {{ background: #F3F4F6; color: {CLR_TEXT_DARK}; }}
        """)

        icon = QIcon(get_asset(icon_file))
        if icon.isNull():
            btn.setText(fallback_text)
        else:
            btn.setIcon(icon)
            btn.setIconSize(QSize(18, 18))

        btn.clicked.connect(callback)
        return btn

    def _position_panels(self):
        bar_top = self.height() - self.bottom_bar.height()
        gap = 12

        self.panel_camera.adjustSize()
        self.panel_camera.move(
            32, bar_top - self.panel_camera.sizeHint().height() - gap
        )

        self.panel_transform.adjustSize()
        cx = self.width() // 2
        self.panel_transform.move(
            cx - 80 - self.panel_transform.width() - gap // 2,
            bar_top - self.panel_transform.sizeHint().height() - gap,
        )

        self.panel_color.adjustSize()
        self.panel_color.move(
            cx - 80 + 52 + gap, bar_top - self.panel_color.sizeHint().height() - gap
        )

    def _toggle_panel(self, panel: FloatingPanel):
        self._position_panels()
        if panel.isVisible():
            panel.hide()
        else:
            panel.show()
            panel.raise_()
            self.bottom_bar.raise_()

    def _populate_cameras(self):
        # Clear old items in layout
        for i in reversed(range(self.cam_list_layout.count())):
            widget_to_remove = self.cam_list_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        raw_devices = []
        if FilterGraph:
            try:
                raw_devices = FilterGraph().get_input_devices()
            except Exception:
                pass

        if not raw_devices:
            raw_devices = ["Cannot detect cameras"]

        valid_cameras = []
        for i, name in enumerate(raw_devices):
            if "obs" in name.lower():
                continue
            valid_cameras.append((i, name))

        if not valid_cameras:
            valid_cameras = [(0, "No valid cameras found")]

        # Set active label
        current_idx = self.settings.camera_index
        active_name = next((n for idx, n in valid_cameras if idx == current_idx), "Unknown Camera")
        self.lbl_active_cam.setText(active_name)

        # Generate clean buttons for each camera
        for idx, name in valid_cameras:
            btn = QPushButton(name)
            
            is_active = (idx == current_idx)
            font_weight = "bold" if is_active else "normal"
            bg_color = "#E5E7EB" if is_active else "transparent"
            text_color = CLR_TEXT_DARK if is_active else CLR_TEXT_MED

            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg_color};
                    border: none;
                    color: {text_color};
                    font-family: '{_FONT_FAMILY}';
                    font-size: 13px;
                    font-weight: {font_weight};
                    text-align: left;
                    padding: 10px 14px;
                    border-radius: 8px;
                    margin: 2px 0px;
                }}
                QPushButton:hover {{
                    background: #F3F4F6;
                    color: {CLR_TEXT_DARK};
                }}
            """)
            btn.clicked.connect(
                lambda checked, c_idx=idx, c_name=name: self._on_camera_selected(
                    c_idx, c_name
                )
            )
            self.cam_list_layout.addWidget(btn)

    def resizeEvent(self, event):
        self.video_label.setGeometry(0, 0, self.width(), self.height())
        self.bottom_bar.setGeometry(0, self.height() - 96, self.width(), 96)
        self._position_panels()
        if self.engine and self.engine.isRunning():
            self.engine.update_preview_size(
                self.video_label.width(), self.video_label.height()
            )
        if not self._cam_active:
            self._draw_placeholder()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        panels = [self.panel_camera, self.panel_transform, self.panel_color]
        for panel in panels:
            if panel.isVisible() and not panel.geometry().contains(event.position().toPoint()):
                panel.hide()
        super().mousePressEvent(event)

    def _toggle_stream(self):
        if self.engine and self.engine.isRunning():
            self._stop_engine()
        else:
            self._start_engine()

    def _start_engine(self):
        try:
            from src.camera_engine import CameraEngine
        except ImportError as e:
            import traceback

            print("[StreamLens] ERROR: Failed to import CameraEngine.", file=sys.stderr)
            print("[StreamLens] Traceback of the import failure:", file=sys.stderr)
            traceback.print_exc()
            print(f"[StreamLens] Reason: {e}", file=sys.stderr)
            print("[StreamLens] Falling back to demo mode.", file=sys.stderr)
            return

        self._cam_active = True
        # Show loading state while camera warms up
        self.video_label.setPixmap(QPixmap())
        self.video_label.setText("Starting camera...")
        self.video_label.setStyleSheet(
            f"background: #000000; color: {CLR_TEXT_LIGHT}; "
            f"font-family: '{_FONT_FAMILY}'; font-size: 14px;"
        )

        # Set icon to ON and keep background transparent/white
        self.btn_cam.setStyleSheet(self._circle_btn_style(40))
        video_on_icon = QIcon(get_asset("video.svg"))
        if not video_on_icon.isNull():
            self.btn_cam.setIcon(video_on_icon)
        else:
            self.btn_cam.setText("🎥")

        self.cam_pill.setStyleSheet(f"""
            QFrame#CamPill {{
                background: {CLR_WHITE};
                border-radius: 26px;
                border: 1px solid {CLR_BORDER};
            }}
        """)

        self.engine = CameraEngine(self.settings)
        self.engine.update_preview_size(
            self.video_label.width(), self.video_label.height()
        )
        # QueuedConnection ensures the slot runs on the engine's thread,
        # preventing UI freeze from cross-thread lock contention
        self.settings_changed.connect(
            self.engine.update_setting, Qt.ConnectionType.QueuedConnection
        )
        self.engine.frame_ready.connect(self._on_frame_ready)
        self.engine.error_occurred.connect(self._on_engine_error)
        self.engine.finished.connect(self._on_engine_finished)
        self.engine.camera_ready.connect(self._on_camera_ready)
        self.engine.start()

    def _stop_engine(self):
        if self.engine:
            self.engine.stop()

    @pyqtSlot()
    def _on_engine_finished(self):
        self.engine = None
        self._cam_active = False
        self.video_label.setStyleSheet(f"background: {CLR_BG};")

        # Revert back to OFF icon
        self.btn_cam.setStyleSheet(self._circle_btn_style(40))
        video_off_icon = QIcon(get_asset("video_off.svg"))
        if not video_off_icon.isNull():
            self.btn_cam.setIcon(video_off_icon)
        else:
            self.btn_cam.setText("📷")

        self.cam_pill.setStyleSheet(f"""
            QFrame#CamPill {{
                background: {CLR_WHITE};
                border-radius: 26px;
                border: 1px solid {CLR_BORDER};
            }}
        """)
        self._draw_placeholder()

    @pyqtSlot(QImage)
    def _on_frame_ready(self, q_img: QImage):
        self.video_label.setPixmap(QPixmap.fromImage(q_img))
        if self.engine:
            self.engine.acknowledge_frame()

    @pyqtSlot(str)
    def _on_engine_error(self, err: str):
        print(f"[StreamLens] Camera error: {err}")
        self._stop_engine()

    @pyqtSlot()
    def _on_camera_ready(self):
        """Called when camera has finished warming up and is producing stable frames."""
        self.video_label.setText("")
        self.video_label.setStyleSheet("background: #000000;")

    def closeEvent(self, event):
        if self.engine:
            self.engine.stop()
            self.engine.wait(3000)  # Block on exit to ensure clean shutdown
        if self.state_manager:
            self.state_manager.flush()
        super().closeEvent(event)

    def _on_camera_selected(self, idx: int, name: str):
        self.lbl_active_cam.setText(name)
        if self.state_manager:
            self.state_manager.update_setting("camera_index", idx)
        else:
            self.settings.camera_index = idx

        if self.engine and self.engine.isRunning():
            self._stop_engine()
            # The UI flow allows user to manually restart it or you can call self._start_engine() here

    def _on_fast_start_changed(self):
        new_val = not self.settings.fast_start
        if self.state_manager:
            self.state_manager.update_setting("fast_start", new_val)
        else:
            self.settings.fast_start = new_val
        self.settings_changed.emit("fast_start", new_val)

    def _on_flip_h_changed(self):
        new_val = not self.settings.flip_horizontal
        if self.state_manager:
            self.state_manager.update_setting("flip_horizontal", new_val)
        else:
            self.settings.flip_horizontal = new_val
        self.settings_changed.emit("flip_horizontal", new_val)

    def _on_flip_v_changed(self):
        new_val = not self.settings.flip_vertical
        if self.state_manager:
            self.state_manager.update_setting("flip_vertical", new_val)
        else:
            self.settings.flip_vertical = new_val
        self.settings_changed.emit("flip_vertical", new_val)

    def _on_brightness_changed(self, v: int):
        if self.state_manager:
            self.state_manager.update_setting("brightness", v)
        else:
            self.settings.brightness = v
        self.settings_changed.emit("brightness", v)

    def _on_contrast_changed(self, v: int):
        if self.state_manager:
            self.state_manager.update_setting("contrast", v)
        else:
            self.settings.contrast = v
        self.settings_changed.emit("contrast", v)

    def _on_saturation_changed(self, v: int):
        if self.state_manager:
            self.state_manager.update_setting("saturation", v)
        else:
            self.settings.saturation = v
        self.settings_changed.emit("saturation", v)

    def _adjust_zoom(self, delta: float):
        new_zoom = max(1.0, min(3.0, self.settings.zoom_level + delta))
        if self.state_manager:
            self.state_manager.update_setting("zoom_level", new_zoom)
        else:
            self.settings.zoom_level = new_zoom
        self.lbl_zoom.setText(f"{new_zoom * 100:.0f}%")
        self.settings_changed.emit("zoom_level", new_zoom)


class _FallbackSettings:
    camera_index = 0
    flip_horizontal = True
    flip_vertical = False
    brightness = 0
    contrast = 0
    saturation = 0
    zoom_level = 1.0
    width = 1280
    height = 720
    fps = 60
    fast_start = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Stream Lens")

    win = StreamLensUI(state_manager=None)
    win.show()
    sys.exit(app.exec())
