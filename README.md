MediaPipe Gesture → Robot (Raspberry Pi)

Minimal scaffold to build a MediaPipe-based hand gesture recognition platform that sends commands to a robot arm (Raspberry Pi target).

Quick start

1. Create a Python 3.8+ virtualenv on the Raspberry Pi.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the demo (uses mock robot by default):

```powershell
python -m src.demo --robot mock
```

Files created
- `src/hand_tracker.py` — MediaPipe hand tracking wrapper
- `src/gestures.py` — simple rule-based gesture detectors
- `src/robot_interface.py` — serial / mock robot interfaces
- `src/demo.py` — webcam demo and overlay
- `requirements.txt` — python deps
- `tests/test_gestures.py` — unit tests for gesture logic

Notes
- On Raspberry Pi, installing MediaPipe may require platform-specific wheels or the `mediapipe` package compiled for your OS. See MediaPipe docs for Pi-specific steps.

Run the demo correctly (why `ModuleNotFoundError: No module named 'src'` appears)

Preferred (clean) method — run as a module from the project root

When you run a script directly (for example: `python src\demo.py`), Python sets the import search path so that the `src` folder is the current package directory. That can make `from src.x import y` fail with "ModuleNotFoundError" because Python expects to find `src` at the project root.

From the project root (the folder that contains `src`) run the demo as a module — this ensures the project root is on Python's import path:

```powershell
& C:/Users/elija/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m src.demo --robot mock
```

PowerShell tip: if your Python is on PATH you can shorten that to:

```powershell
python -m src.demo --robot mock
```

Alternative: set PYTHONPATH for the session (less recommended than `-m`):

```powershell
#$env:PYTHONPATH = 'C:\path\to\project\root'
# prefer running the module or the top-level launcher instead of executing inside `src/`:
& C:/Users/elija/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m src.demo --robot mock
# or, run the provided launcher from the project root:
python run_demo.py --robot mock
```

Quick launcher (optional)

If you prefer a single-file entry point, create a top-level `run_demo.py` next to `src/` with:

```python
from src import demo

if __name__ == '__main__':
	demo.main()
```

Then run `python run_demo.py` from the project root. But the `-m` approach is the recommended, canonical way to run packages.
