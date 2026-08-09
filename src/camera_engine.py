import cv2
import numpy as np
import pyvirtualcam
import threading
import time
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
from src.state_manager import AppSettings


class CameraEngine(QThread):
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)
    camera_ready = pyqtSignal()  # Emitted after camera is warmed up and stable

    # Number of warm-up frames to discard on camera open.
    # These initial frames are often black/corrupted while AE/AF settles.
    WARMUP_FRAMES = 10

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._run_flag = True
        self.cap = None
        self.lock = threading.Lock()  # Protect settings reads and writes across threads

        # State for frame rate control and backpressure
        self.ui_ready = True
        self.preview_size = (640, 480)

        # Pre-allocate processing buffers
        self.output_size = (self.settings.width, self.settings.height)
        self.sat_lut = None
        self.last_sat_val = None
        self._update_sat_lut()

    def _update_sat_lut(self):
        # Assumes lock is held by caller if running, or called in init
        sat = self.settings.saturation
        self.sat_lut = np.clip(
            np.arange(256) * (1.0 + sat / 100.0), 0, 255
        ).astype(np.uint8)
        self.last_sat_val = sat

    @pyqtSlot(str, object)
    def update_setting(self, key: str, value: object):
        """Thread-safe slot to dynamically update setting attributes from the UI thread."""
        with self.lock:
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                if key == "saturation":
                    self._update_sat_lut()

    def update_preview_size(self, width: int, height: int):
        """Update the preview size dynamically based on UI size."""
        with self.lock:
            self.preview_size = (max(16, width), max(16, height))

    def acknowledge_frame(self):
        """UI thread calls this to signal it has finished processing the last frame."""
        with self.lock:
            self.ui_ready = True

    def _init_camera(self, camera_index: int, width: int, height: int):
        """
        Initialize camera with settings optimized to prevent auto-exposure
        hunting (flash blink) and minimize startup latency.

        Returns an opened VideoCapture or None on failure.
        """
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return None

        # 1. Force MJPG codec for maximum quality & faster decode from hardware
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        # 2. Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 3. Minimize internal frame buffer to prevent stale frames on start
        #    (default is often 4+ frames, causing perceived startup lag)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # 4. Suppress auto-exposure hunting that causes flash/LED blinking.
        #    DirectShow convention: 0.25 = manual exposure, 0.75 = auto.
        #    This is best-effort — not all cameras/drivers support it.
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        cap.set(cv2.CAP_PROP_EXPOSURE, -5)

        # 5. Disable autofocus to prevent mechanical hunting delays
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        # NOTE: We deliberately do NOT set CAP_PROP_FPS via DirectShow.
        # Setting FPS triggers a full camera pipeline re-negotiation which
        # causes additional auto-exposure/flash blinks and adds 1-2s startup
        # delay. Frame pacing is instead handled by pyvirtualcam's
        # sleep_until_next_frame().

        return cap

    def _warmup_camera(self, cap, num_frames: int = None):
        """
        Discard initial frames that are typically black or have unstable
        exposure/white-balance. Uses grab() instead of read() for speed
        since we don't need to decode these frames.
        """
        if num_frames is None:
            num_frames = self.WARMUP_FRAMES
        for _ in range(num_frames):
            if not self._run_flag:
                break
            cap.grab()

    def _restore_auto_exposure(self, cap):
        """
        Re-enable auto-exposure after warm-up so the camera adapts to
        changing lighting conditions during normal operation.
        """
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)

    def run(self):
        try:
            # Snapshot settings under lock before slow hardware init
            with self.lock:
                if not self._run_flag:
                    return
                camera_index = self.settings.camera_index
                width = self.settings.width
                height = self.settings.height
                fps = self.settings.fps

            # --- Hardware Initialization (outside lock — this is slow I/O) ---
            cap = self._init_camera(camera_index, width, height)
            if cap is None:
                self.error_occurred.emit(
                    f"Could not open camera {camera_index}"
                )
                return

            with self.lock:
                if not self._run_flag:
                    cap.release()
                    return
                self.cap = cap

            # Discard warm-up frames (black/unstable exposure)
            self._warmup_camera(cap)

            if not self._run_flag:
                return

            # Re-enable auto-exposure now that initial frames are stable
            self._restore_auto_exposure(cap)

            # Notify UI that camera is ready and streaming
            self.camera_ready.emit()

            # --- Virtual Camera Initialization ---
            try:
                # Target our specific virtual camera device name so that it registers
                # as a distinct option in Windows DirectShow. This prevents users from
                # accidentally selecting the physical camera and causing locking conflicts.
                cam = pyvirtualcam.Camera(
                    width=width,
                    height=height,
                    fps=fps,
                    fmt=pyvirtualcam.PixelFormat.BGR,
                    device="StreamLens Virtual Camera"
                )
            except Exception as e:
                print(f"[CameraEngine] Failed to init 'StreamLens Virtual Camera' device: {e}. Falling back to default OBS Virtual Camera...")
                try:
                    cam = pyvirtualcam.Camera(
                        width=width,
                        height=height,
                        fps=fps,
                        fmt=pyvirtualcam.PixelFormat.BGR,
                        backend="obs"
                    )
                except Exception as e2:
                    print(f"[CameraEngine] Failed to init OBS Virtual Camera backend: {e2}. Falling back to any available virtual camera...")
                    cam = pyvirtualcam.Camera(
                        width=width,
                        height=height,
                        fps=fps,
                        fmt=pyvirtualcam.PixelFormat.BGR
                    )

            with cam:
                print(f"Virtual Camera Active: {cam.device} (Backend: {cam.backend})")

                while self._run_flag:
                    # Check cap is valid under lock
                    with self.lock:
                        cap_device = self.cap

                    if cap_device is None:
                        break

                    ret, frame = cap_device.read()
                    if not ret:
                        print("[CameraEngine] Capture failed. Attempting camera recovery...")
                        # Release current cap
                        with self.lock:
                            if self.cap:
                                self.cap.release()
                                self.cap = None

                        reconnected = False
                        while self._run_flag and not reconnected:
                            # Send a black placeholder frame to virtual camera to keep connection active
                            placeholder = np.zeros((height, width, 3), dtype=np.uint8)
                            cv2.putText(
                                placeholder,
                                "Camera Disconnected - Retrying...",
                                (50, height // 2),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (255, 255, 255),
                                2
                            )
                            cam.send(placeholder)
                            cam.sleep_until_next_frame()

                            # Sleep 2.0s checking run flag
                            for _ in range(20):
                                if not self._run_flag:
                                    break
                                time.sleep(0.1)

                            if not self._run_flag:
                                break

                            print("[CameraEngine] Attempting reconnection...")
                            new_cap = self._init_camera(camera_index, width, height)

                            if new_cap is not None:
                                self._warmup_camera(new_cap, num_frames=5)
                                self._restore_auto_exposure(new_cap)
                                with self.lock:
                                    self.cap = new_cap
                                reconnected = True
                                print("[CameraEngine] Reconnection successful!")

                        if not reconnected:
                            break
                        continue  # Re-run loop with new self.cap

                    # 1. Processing Pipeline (In-place optimizations applied inside)
                    processed_frame = self._process_frame(frame)

                    # 2. Resolution Safety Check — high quality interpolation
                    h, w = processed_frame.shape[:2]
                    target_w, target_h = width, height
                    if w != target_w or h != target_h:
                        # INTER_AREA for downscaling (anti-aliased), INTER_LANCZOS4 for upscaling
                        interp = cv2.INTER_AREA if (w > target_w or h > target_h) else cv2.INTER_LANCZOS4
                        processed_frame = cv2.resize(
                            processed_frame, (target_w, target_h), interpolation=interp
                        )

                    # 3. Virtual Camera Output
                    # We initialized pyvirtualcam with BGR format, so we can send the BGR frame directly
                    # without needing to convert it to RGB, saving CPU cycles.
                    # Use np.ascontiguousarray to ensure the memory is contiguous before sending,
                    # which is required by pyvirtualcam to prevent silent crashes or tearing.
                    out_frame = np.ascontiguousarray(processed_frame)
                    cam.send(out_frame)
                    cam.sleep_until_next_frame()

                    # 4. UI Notification with backpressure & offloaded scaling
                    with self.lock:
                        ui_ready = self.ui_ready
                        preview_size = self.preview_size

                    if ui_ready:
                        with self.lock:
                            self.ui_ready = False

                        # Scale on background thread to offload UI thread
                        # INTER_AREA produces smooth downscaled previews
                        preview_frame = cv2.resize(
                            processed_frame, preview_size, interpolation=cv2.INTER_AREA
                        )
                        ph, pw, pch = preview_frame.shape
                        q_img = QImage(
                            preview_frame.data, pw, ph, pch * pw, QImage.Format.Format_BGR888
                        ).copy()  # Make a deep copy to ensure thread safety of the memory
                        self.frame_ready.emit(q_img)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            with self.lock:
                if self.cap:
                    self.cap.release()
                    self.cap = None

    def _process_frame(self, frame):
        # Read settings variables thread-safely
        with self.lock:
            zoom_level = self.settings.zoom_level
            flip_horizontal = self.settings.flip_horizontal
            flip_vertical = self.settings.flip_vertical
            brightness = self.settings.brightness
            contrast = self.settings.contrast
            saturation = self.settings.saturation
            
            # Lazily/dynamically update LUT if changed externally (e.g. from tests)
            if self.sat_lut is None or self.last_sat_val != saturation:
                self.sat_lut = np.clip(
                    np.arange(256) * (1.0 + saturation / 100.0), 0, 255
                ).astype(np.uint8)
                self.last_sat_val = saturation
            sat_lut = self.sat_lut

        # 1. Zoom (Only resize if necessary)
        if abs(zoom_level - 1.0) > 0.01:
            h, w = frame.shape[:2]
            new_h, new_w = int(h / zoom_level), int(w / zoom_level)
            start_h = (h - new_h) // 2
            start_w = (w - new_w) // 2
            frame = frame[start_h : start_h + new_h, start_w : start_w + new_w]
            # INTER_LANCZOS4 for high quality zoom output
            frame = cv2.resize(frame, self.output_size, interpolation=cv2.INTER_LANCZOS4)

        # 2. Flips (In-place)
        if flip_horizontal and flip_vertical:
            cv2.flip(frame, -1, dst=frame)
        elif flip_horizontal:
            cv2.flip(frame, 1, dst=frame)
        elif flip_vertical:
            cv2.flip(frame, 0, dst=frame)

        # 3. Brightness/Contrast Optimization (In-place)
        if brightness != 0 or contrast != 0:
            alpha = 1.0 + (contrast / 100.0)
            beta = brightness
            cv2.convertScaleAbs(frame, dst=frame, alpha=alpha, beta=beta)

        # 4. Saturation (HSV space using lookup table to avoid float allocations)
        if saturation != 0 and sat_lut is not None:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = cv2.LUT(hsv[:, :, 1], sat_lut)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return frame

    def stop(self):
        """Signal the engine to stop. Releases camera to unblock any pending read().
        
        This method is non-blocking — it signals the thread to stop and releases
        the camera device, but does NOT wait for the thread to finish. Use wait()
        after calling stop() if you need to block until the thread exits (e.g. on
        application close).
        """
        self._run_flag = False
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None
