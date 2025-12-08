# Raspberry Pi Setup Guide

Complete guide to setting up the Smart Soldering Station on a Raspberry Pi.

## Hardware Requirements

- **Raspberry Pi 3B+, 4, or 5** (4GB+ RAM recommended for better performance)
- **MicroSD card** (16GB+ recommended)
- **USB Webcam** or **Raspberry Pi Camera Module**
- **Power supply** (official Pi power supply recommended)
- **Monitor, keyboard, mouse** (for initial setup)
- **Optional**: Relays, servos, or robot arm for actual control

## Step 1: Prepare Your Raspberry Pi

### Install Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Install **Raspberry Pi OS (64-bit)** - 64-bit is recommended for MediaPipe
3. Configure WiFi and enable SSH in the imager settings (optional)
4. Boot your Pi and complete the initial setup

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

## Step 2: Install System Dependencies

MediaPipe and OpenCV need these system libraries:

```bash
# Core dependencies
sudo apt install -y python3-pip python3-venv git

# OpenCV and MediaPipe dependencies
sudo apt install -y libatlas-base-dev libopenjp2-7 libtiff5
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev
sudo apt install -y libgtk-3-dev libcanberra-gtk3-module
sudo apt install -y libqt5gui5 libqt5test5 libqt5widgets5
sudo apt install -y python3-dev python3-numpy

# For camera support
sudo apt install -y v4l-utils
```

## Step 3: Get the Project

### Option A: Clone from GitHub

```bash
cd ~
git clone https://github.com/elijahtharakan/smartsolderingstation.git
cd smartsolderingstation
```

### Option B: Transfer from Your Computer

From your Windows machine, use SCP:

```powershell
# Replace 'raspberrypi.local' with your Pi's IP address if needed
scp -r "c:\Users\elija\Desktop\College\EE 497\smartsolderingstation\smartsolderingstation" pi@raspberrypi.local:~/
```

Or use a USB drive to copy the folder.

## Step 4: Set Up Python Virtual Environment

```bash
cd ~/smartsolderingstation
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your prompt.

## Step 5: Install Python Dependencies

### Method 1: Standard Installation (Try This First)

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Method 2: If OpenCV Fails

If `opencv-python` fails to install, use the headless version:

```bash
pip install opencv-python-headless
pip install mediapipe numpy pyserial pyyaml pytest
```

### Method 3: If MediaPipe Fails

MediaPipe can be tricky on Pi. Try these in order:

```bash
# Try latest version
pip install mediapipe

# If that fails, try a specific older version
pip install mediapipe==0.10.0

# Or try the pre-built wheel approach
pip install mediapipe --no-cache-dir
```

**Note**: On older Raspberry Pi models (Pi 3), you may need to build MediaPipe from source or use an alternative hand tracking solution.

## Step 6: Camera Setup

### For USB Webcam

USB webcams usually work automatically. Verify with:

```bash
ls /dev/video*
# Should show /dev/video0 or similar
```

Test the camera:

```bash
v4l2-ctl --list-devices
```

### For Raspberry Pi Camera Module (libcamera / Picamera2)

Recent Raspberry Pi OS releases use the libcamera stack (replacing the old "legacy" camera stack). Prefer libcamera and the Picamera2 Python library for the official camera modules. Do NOT enable the legacy camera driver unless you specifically need it, as it can conflict with libcamera.

1. Install libcamera tools and Picamera2:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y libcamera-apps python3-picamera2
```

2. (Optional) Enable the camera in raspi-config if your OS exposes the option:
```bash
sudo raspi-config
# Interface Options -> Camera -> Enable
```

3. Reboot:
```bash
sudo reboot
```


4. Test the camera with Picamera2 (Python):

Create a file called `test_picamera2.py` with the following content:

```python
from picamera2 import Picamera2
import time

picam2 = Picamera2()
picam2.start()
time.sleep(2)  # Allow camera to warm up
picam2.capture_file("test.jpg")
print("Image captured as test.jpg")
picam2.close()
```

Run it:
```bash
python3 test_picamera2.py
```

If you see `Image captured as test.jpg` and a new file appears, your camera is working!

If you have a USB webcam, continue to use the v4l2 tools (see the USB Webcam section above).

**Troubleshooting:**
- If you get errors about the camera not being found, check:
   - Is the camera ribbon cable fully inserted?
   - Run `ls /dev/video*` (should show `/dev/video0` or `/dev/video1`)
   - Run `dmesg | grep -i camera` for kernel messages
   - Try rebooting after reseating the camera
- If you see `ModuleNotFoundError: No module named 'picamera2'`, install it:
   ```bash
   sudo apt install python3-picamera2
   ```

### Camera Permissions

Add your user to the video group (useful for v4l2 devices):

```bash
sudo usermod -a -G video $USER
```

Log out and back in for this to take effect.

## Step 7: Test the Demo

### Basic Test (Mock Robot - No Hardware Needed)

```bash
cd ~/smartsolderingstation
source venv/bin/activate
python run_demo.py --robot mock
```

Or:

```bash
python -m src.demo --robot mock
```

**Expected behavior**: A window should open showing your webcam feed with hand tracking overlays.

### Test Without Display (Headless)

If running over SSH without a display:

```bash
# Set to use headless OpenCV
export DISPLAY=
python run_demo.py --robot mock
```

For true headless operation, you'll need to modify the code to save frames instead of displaying them.

## Step 8: Hardware Integration

### For GPIO Control (Relays, Servos, etc.)

1. Install GPIO libraries:
```bash
pip install gpiozero RPi.GPIO
```

2. Copy and edit the config file:
```bash
cp config/example_config.yaml config/my_config.yaml
nano config/my_config.yaml
```

3. Set up your hardware connections:
   - **Relays**: Connect to GPIO pins (e.g., GPIO 17)
   - **Servos**: Connect signal wire to PWM-capable pins (e.g., GPIO 18)
   - **Remember**: Common ground between Pi and devices

4. Run with GPIO:
```bash
python run_demo.py --robot gpio
```

### For Serial Robot Control

1. Find your serial device:
```bash
ls /dev/tty*
# Common: /dev/ttyUSB0, /dev/ttyACM0, /dev/serial0
```

2. Add user to dialout group for serial access:
```bash
sudo usermod -a -G dialout $USER
```
Log out and back in.

3. Run with serial:
```bash
python run_demo.py --robot serial
```

## Step 9: Performance Optimization

### Reduce Camera Resolution

Edit `src/demo.py` and lower the resolution:

```python
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # Lower from 640
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Lower from 480
```

### Enable GPU Memory

```bash
sudo raspi-config
```
Navigate to: **Performance Options** → **GPU Memory** → Set to **128** or **256**

### Overclock (Optional, Advanced)

For Pi 4, you can safely overclock. Edit:
```bash
sudo nano /boot/config.txt
```

Add (Pi 4 example):
```
over_voltage=6
arm_freq=2000
gpu_freq=600
```

**Warning**: Ensure adequate cooling!

## Step 10: Run on Startup (Optional)

### Create Systemd Service

1. Create service file:
```bash
sudo nano /etc/systemd/system/soldering-station.service
```

2. Add this content (adjust paths as needed):
```ini
[Unit]
Description=Smart Soldering Station
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smartsolderingstation
Environment="DISPLAY=:0"
ExecStart=/home/pi/smartsolderingstation/venv/bin/python run_demo.py --robot mock
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable soldering-station.service
sudo systemctl start soldering-station.service
```

4. Check status:
```bash
sudo systemctl status soldering-station.service
```

5. View logs:
```bash
journalctl -u soldering-station.service -f
```

## Troubleshooting

### Camera Not Working

```bash
# List video devices
v4l2-ctl --list-devices

# Check camera status (for Pi Camera)
vcgencmd get_camera

# Test camera with simple command
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg
```

### MediaPipe Installation Fails

- **Try older version**: `pip install mediapipe==0.10.0`
- **Check architecture**: `uname -m` (should be aarch64 for 64-bit)
- **Ensure 64-bit OS**: MediaPipe has better support on 64-bit
- **Alternative**: Consider using other hand tracking libraries if MediaPipe won't work

### Poor Performance / Lag

- Lower camera resolution (see Step 9)
- Use Pi 4 or Pi 5 (much faster than Pi 3)
- Close other applications
- Ensure adequate cooling
- Use `opencv-python-headless` instead of `opencv-python`

### Permission Denied Errors

```bash
# For GPIO
sudo usermod -a -G gpio $USER

# For serial
sudo usermod -a -G dialout $USER

# For camera
sudo usermod -a -G video $USER

# Log out and back in after making these changes
```

### Display Issues Over SSH

If you're connecting via SSH and get display errors:

```bash
# For X11 forwarding
ssh -X pi@raspberrypi.local

# Or set DISPLAY
export DISPLAY=:0
```

For true headless operation, modify the code to not display windows.

### ImportError: libGL.so

If you get OpenGL errors:

```bash
sudo apt install -y libgl1-mesa-glx
```

## Remote Access

### VNC (Graphical Desktop)

Enable VNC in raspi-config:
```bash
sudo raspi-config
# Interface Options → VNC → Enable
```

Connect using [VNC Viewer](https://www.realvnc.com/en/connect/download/viewer/)

### SSH (Command Line)

```bash
# From Windows PowerShell
ssh pi@raspberrypi.local
```

## Testing Checklist

- [ ] Python virtual environment created and activated
- [ ] All dependencies installed without errors
- [ ] Camera detected (`ls /dev/video*`)
- [ ] Demo runs with mock robot
- [ ] Hand tracking visible in video feed
- [ ] Gestures detected and printed to console
- [ ] (If using hardware) GPIO/Serial device responds to gestures

## Next Steps

1. **Customize gestures** in `src/gestures.py`
2. **Configure hardware** in `config/my_config.yaml`
3. **Map gestures to actions** for your specific soldering station setup
4. **Build your enclosure** with the Pi and camera positioned appropriately
5. **Test thoroughly** before using with actual soldering equipment

## Safety Notes

⚠️ **Important**: When controlling real hardware (especially relays controlling high voltage):
- Test extensively with mock robot first
- Add safety interlocks and emergency stops
- Never leave unattended while powered
- Follow electrical safety best practices
- Consider a physical kill switch

## Getting Help

If you encounter issues:

1. Check the error messages carefully
2. Verify all dependencies are installed: `pip list`
3. Test camera independently: `v4l2-ctl --list-devices`
4. Check permissions: `groups` (should include video, dialout, gpio)
5. Review logs: `journalctl -u soldering-station.service -f`

## Useful Commands Reference

```bash
# Activate virtual environment
source venv/bin/activate

# Run demo
python run_demo.py --robot mock

# Check Python packages
pip list

# Test camera
v4l2-ctl --list-devices

# Check Pi temperature
vcgencmd measure_temp

# Check running services
systemctl list-units --type=service --state=running

# View real-time logs
journalctl -f
```

Good luck with your smart soldering station project! 🔥🤖
