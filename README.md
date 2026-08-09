  ____  _                               _                     
 / ___|| |_ _ __ ___  __ _ _ __ ___    | |    ___ _ __  ___ 
 \___ \| __| '__/ _ \/ _` | '_ ` _ \   | |   / _ \ '_ \/ __|
  ___) | |_| | |  __/ (_| | | | | | |  | |__|  __/ | | \__ \
 |____/ \__|_|  \___|\__,_|_| |_| |_|  |_____\___|_| |_|___/

# StreamLens

Built on the philosophy of **Quality Over Everything**. StreamLens is a premium, high-fidelity virtual camera application that provides real-time stream manipulation, professional color grading, and dynamic transformations with an ultra-responsive interface. 

## Key Features

- **Real-time synchronization:** Ultra-low latency camera capture and virtual camera frame output.
- **Pro-Level Color Grading:** Adjust brightness, contrast, saturation and apply dynamic transformations like flipping and zooming on-the-fly.
- **Universal App Support:** Robust OBS backend integration ensures your modified stream is cleanly picked up by sandboxed applications like Google Meet (Chrome), WhatsApp Desktop, and Zoom.

## Prerequisites

To ensure StreamLens connects seamlessly with other applications, it leverages the robust OBS Virtual Camera driver.

**CRITICAL REQUIREMENT:** 
You **MUST** install [OBS Studio](https://obsproject.com/) and start the OBS Virtual Camera at least once to register the virtual camera drivers on your system. StreamLens will use this existing driver to route its high-quality video feed universally.

## 1-Click Build

We've provided a fully automated build pipeline. To compile the application yourself:

1. Ensure Python is installed on your system.
2. Double-click the `build.bat` file located in the root directory.
3. The script will automatically setup a virtual environment, install dependencies, and build the `stream_lens_v1.0.4.exe` executable.
4. When finished, find your compiled application in the newly generated `dist/` folder!

## Usage Guide

1. Launch `StreamLens` (or the compiled `stream_lens_v1.0.4.exe`).
2. Select your physical web camera from the **Camera Devices** list. StreamLens will instantly start processing the feed.
3. Open your desired third-party app (Zoom, Google Meet, WhatsApp, etc.).
4. In the video settings of the third-party app, select **"OBS Virtual Camera"** (DO NOT select your physical camera). 
5. Your customized StreamLens feed will now appear perfectly inside the app without any locking errors!
