<div align="center">

<pre>
 ____ _                                       _                   
/ ___| |_ _ __ ___  __ _ _ __ ___    | |    ___ _ __  ___  
\___ \ __| '__/ _ \/ _` | '_ ` _ \   | |   / _ \ '_ \/ __| 
 ___) | |_| | |  __/ (_| | | | | | |  | |__|  __/ | | \__ \ 
|____/ \__|_|  \___|\__,_|_| |_| |_|  |_____\___|_| |_|___/ 
</pre>

<h5>StreamLens Virtual Camera</h5>

A minimalist, high-performance 60FPS virtual camera interface built for seamless real-time stream manipulation and global application integration. **Quality Over Everything.**

<br />

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-00C000?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![PyVirtualCam](https://img.shields.io/badge/PyVirtualCam-0.11+-FF6F61?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/letmaik/pyvirtualcam)
[![Backend](https://img.shields.io/badge/Backend-OBS_Virtual_Camera-orange?style=for-the-badge&logo=obsstudio&logoColor=white)](https://obsproject.com/)

</div>

---

## Features

- **Universal App Support:** Built on top of the industry-standard OBS Virtual Camera backend, ensuring 100% compatibility with restrictive WebRTC browsers (Chrome/Google Meet) and Electron apps (WhatsApp Desktop, Zoom).
- **Premium UI & Native Typography:** A fully custom GUI designed with PyQt6, dynamically utilizing the `Inter` font family for crisp, system-agnostic rendering. Features smooth drop shadows, clean padding, and a professional layout.
- **Real-Time Synchronization:** Instant frame adjustments utilizing a robust thread-safe Signal/Slot architecture. No engine restarts required when altering settings.
- **Pro-Level Color Grading:** Real-time Brightness, Contrast, and Saturation adjustments using high-performance HSV color-space scaling.
- **Automated 1-Click Build:** Includes a `build.bat` script for effortless Windows executable compilation (`.exe`) without touching the terminal.
- **Smart Device Handling:** Built-in conflict resolution and UI filtering to prevent hardware locking and infinite loops during device selection.

---

## Architecture

StreamLens follows a rigorous, production-grade **multithreaded architectural paradigm** built on strict separation of concerns:

<pre>
               +-------------------------------------------+
               |                 Main GUI Thread           |
               |  - PyQt6 Event Loop                       |
               |  - Custom Frameless Control Windows       |
               +---------------------+---------------------+
                                     ^
                         Signal/Slot | (Frame Buffers)
                                     v
               +---------------------+---------------------+
               |             Background Worker QThread     |
               |  - OpenCV Camera Processing (DirectShow)  |
               |  - Image Filter/Grading Transformations   |
               |  - PyVirtualCam output stream loop (OBS)  |
               +-------------------------------------------+
</pre>

1. **GUI Main Thread:** Drives the layout, listens to user control inputs, and uses high-performance signal boundaries to receive frame matrices for paint events.
2. **Background Camera Engine:** Run continuously on a dedicated background worker (`QThread`). Operates the camera capturing and transformation pipeline, formats frames, and channels frames natively to `pyvirtualcam`'s OBS registers.

---

## Prerequisites

Before running StreamLens, you must register the virtual camera drivers on your system. This acts as the certified bridge for applications like WhatsApp and Chrome.

1. Download and install [OBS Studio](https://obsproject.com/).
2. Open OBS Studio at least once and click **"Start Virtual Camera"** to initialize the drivers. (You can close OBS afterward).

---

## Quick Start

### Option 1: The 1-Click Automated Build (Windows)
For the fastest setup, simply double-click the **`build.bat`** file in the root directory. 
This script will automatically create a virtual environment, install all requirements, compile the project, and generate the `stream_lens_v1.0.4.exe` file inside the `dist/` folder.

### Option 2: Manual Setup for Developers

**1. Clone & Initialize**

```bash
git clone [https://github.com/dilshanxo/streamlens-virtual-cam.git](https://github.com/dilshanxo/streamlens-virtual-cam.git)
cd streamlens-virtual-cam
```

**2. Set up Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install Requirements**
```bash
pip install -r requirements.txt
```

**4. Execute the Application**
```bash
python src/ui_main.py
```

---

## Usage Guide (Integrating with Chat Apps)

When StreamLens is running, it locks your physical webcam to process the frames. To use your newly graded virtual stream in third-party applications:

1. Open your target application (e.g., WhatsApp, Zoom, Google Meet).
2. Go to the Video/Camera settings.
3. Select **`OBS Virtual Camera`** as your input device.
4. *Note: Do not select your physical webcam from the chat app's list, as StreamLens is already utilizing it.*

---

## Testing

StreamLens features high coverage unit tests. To run tests locally in your virtual environment:

```bash
python -m unittest discover -s tests
```

---

## Contributing

Contributions make the open-source community an amazing place! Check out our [CONTRIBUTING.md](CONTRIBUTING.md) to get started on following PEP 8 coding style standards and executing headless test suites before sending pull requests.
