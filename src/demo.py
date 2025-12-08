"""Demo application: capture webcam, track hands, detect gestures, and send robot commands."""
import argparse
import time
import cv2
import yaml
from typing import Optional
import os

from src.hand_tracker import HandTracker
import src.gestures as gestures
from src.robot_interface import MockRobot, SerialRobot, PiGPIORobot

# Force OpenCV to use a specific backend for better VNC compatibility
# Try GTK first, then Qt, then default
try:
    cv2.namedWindow("test", cv2.WINDOW_NORMAL)
    cv2.destroyWindow("test")
except:
    pass

# Try to import Picamera2 for Raspberry Pi Camera support
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False


def draw_hand_info(frame, hand):
    h, w = frame.shape[:2]
    for (x, y, z) in hand["landmarks"]:
        cx, cy = int(x * w), int(y * h)
        cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
    cv2.putText(frame, f"{hand['handedness']} {hand.get('score',0):.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)


def main(robot_type: str = "mock"):
    print(f"[DEBUG] Starting demo with robot_type={robot_type}")
    # instantiate robot
    if robot_type == "mock":
        robot = MockRobot()
    elif robot_type == 'serial':
        robot = SerialRobot()
    elif robot_type == 'gpio':
        robot = PiGPIORobot()
    else:
        robot = MockRobot()

    # load config (optional)
    cfg = None
    try:
        with open('config/example_config.yaml', 'r') as fh:
            cfg = yaml.safe_load(fh)
    except Exception:
        cfg = None

    tracker = HandTracker()
    print("[DEBUG] HandTracker initialized")

    # Try Picamera2 first (for Pi Camera), fallback to OpenCV
    picam2 = None
    cap = None
    
    print(f"[DEBUG] Picamera2 available: {PICAMERA2_AVAILABLE}")
    
    if PICAMERA2_AVAILABLE:
        try:
            print("[DEBUG] Attempting to use Picamera2...")
            picam2 = Picamera2()
            # Configure for OpenCV-compatible format
            config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
            picam2.configure(config)
            picam2.start()
            print("[DEBUG] Picamera2 initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Picamera2 failed: {e}, falling back to OpenCV")
            picam2 = None
    else:
        print("[DEBUG] Picamera2 not available, using OpenCV VideoCapture")
    
    if picam2 is None:
        # Try different camera backends for Raspberry Pi
        print("[DEBUG] Trying to open camera with different backends...")
        
        # Try V4L2 backend explicitly
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if cap.isOpened():
            # Try to read a test frame
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                print("[DEBUG] OpenCV VideoCapture with V4L2 backend opened successfully")
            else:
                print("[DEBUG] V4L2 backend opened but cannot read frames, trying default...")
                cap.release()
                cap = cv2.VideoCapture(0)
        else:
            print("[DEBUG] V4L2 backend failed, trying default backend...")
            cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("[ERROR] Failed to open camera at index 0")
            return
        print("[DEBUG] Camera opened, testing frame read...")
        
        # Do a test read
        ret, test_frame = cap.read()
        if not ret or test_frame is None:
            print("[ERROR] Camera opened but cannot read frames")
            print("[DEBUG] Trying alternative camera indices...")
            cap.release()
            
            # Try other indices - Pi camera is often on video10-13
            for idx in [10, 11, 12, 13, 2, 1]:
                print(f"[DEBUG] Trying /dev/video{idx}...")
                cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                if cap.isOpened():
                    print(f"[DEBUG] /dev/video{idx} opened, testing frame read...")
                    # Give camera time to initialize
                    time.sleep(0.5)
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        print(f"[DEBUG] Success with /dev/video{idx}, frame shape: {test_frame.shape}")
                        break
                    else:
                        print(f"[DEBUG] /dev/video{idx} opened but cannot read frames")
                    cap.release()
            else:
                print("[ERROR] No working camera found")
                print("[HINT] Try installing picamera2: sudo apt install libcap-dev && pip install picamera2")
                return
        else:
            print("[DEBUG] Test frame read successful")
    
    last_gesture: Optional[str] = None
    last_sent = 0.0

    try:
        print("[DEBUG] Entering main loop...")
        frame_count = 0
        
        # Create window with specific flags for VNC compatibility
        window_name = "Gesture → Robot Demo"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 640, 480)
        print(f"[DEBUG] Created window: {window_name}")
        
        while True:
            # Capture frame from either Picamera2 or OpenCV
            if picam2 is not None:
                frame_raw = picam2.capture_array()
                # Picamera2 returns RGB, convert to BGR for OpenCV/MediaPipe compatibility
                frame = cv2.cvtColor(frame_raw, cv2.COLOR_RGB2BGR)
                ret = True
            else:
                ret, frame = cap.read()
            
            if not ret or frame is None:
                print(f"[ERROR] Failed to read frame after {frame_count} frames")
                break
            
            # Flip the frame 180 degrees (camera is upside down)
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            # Debug: Check if frame has data
            if frame_count == 0:
                print(f"[DEBUG] Frame stats - min: {frame.min()}, max: {frame.max()}, mean: {frame.mean():.1f}")
                # Save first frame to disk to verify camera works
                cv2.imwrite("debug_frame.jpg", frame)
                print("[DEBUG] Saved first frame to debug_frame.jpg - check if this image looks correct")
            
            frame_count += 1
            if frame_count == 1:
                print(f"[DEBUG] First frame captured: {frame.shape}")

            hands = tracker.process_frame(frame)
            gesture = None
            direction = None
            if hands:
                if frame_count < 5:  # Debug first few detections
                    print(f"[DEBUG] Detected {len(hands)} hand(s)")
                # just process first hand for demo
                hand = hands[0]
                draw_hand_info(frame, hand)
                
                # Detect gesture with direction
                try:
                    gesture_info = gestures.detect_gesture_with_direction(hand["landmarks"], hand.get("handedness"))
                    gesture = gesture_info['gesture']
                    direction = gesture_info['direction']
                    combined_gesture = gesture_info['combined']
                    
                    if frame_count < 5 and gesture:
                        print(f"[DEBUG] Detected gesture: {gesture}, direction: {direction}")
                except (AttributeError, KeyError):
                    # Fallback to simple gesture detection
                    try:
                        gesture = gestures.detect_gesture_with_handedness(hand["landmarks"], hand.get("handedness"))
                        combined_gesture = gesture
                        if frame_count < 5 and gesture:
                            print(f"[DEBUG] Detected gesture: {gesture}")
                    except AttributeError:
                        try:
                            gesture = gestures.detect_gesture(hand["landmarks"])
                            combined_gesture = gesture
                            if frame_count < 5 and gesture:
                                print(f"[DEBUG] Detected gesture: {gesture}")
                        except AttributeError:
                            gesture = None
                            combined_gesture = None
                
                # Display gesture and direction
                if gesture:
                    display_text = f"Gesture: {gesture}"
                    if direction:
                        display_text += f" -> {direction.upper()}"
                    cv2.putText(frame, display_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 2)

            # send gesture to robot on change with debounce
            now = time.time()
            if gesture and (now - last_sent) > 0.5:
                # Use combined gesture (with direction) if available, otherwise just gesture
                current_gesture = combined_gesture if combined_gesture else gesture
                
                # Only send if gesture changed
                if current_gesture != last_gesture:
                    # map gesture to command via config if available
                    cmd = None
                    if cfg and 'gestures' in cfg and current_gesture in cfg['gestures']:
                        cmd = cfg['gestures'][current_gesture]
                    else:
                        # Default command is the gesture name
                        cmd = current_gesture
                    robot.send_command(cmd)
                    last_gesture = current_gesture
                    last_sent = now
            elif not gesture:
                # Reset movement tracking when no hand detected
                gestures.reset_movement_tracking()

            # Display the frame - force refresh
            cv2.imshow(window_name, frame)
            
            if frame_count == 1:
                print("[DEBUG] First frame displayed in window")
            
            # Check for 'q' key to quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("[DEBUG] 'q' pressed, exiting...")
                break
    except Exception as e:
        print(f"[ERROR] Exception in main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[DEBUG] Cleaning up...")
        if picam2 is not None:
            picam2.stop()
            picam2.close()
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("[DEBUG] Demo ended")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", choices=["mock", "serial"], default="mock")
    args = parser.parse_args()
    main(robot_type=args.robot)
