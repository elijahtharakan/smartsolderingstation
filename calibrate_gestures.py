"""Gesture calibration tool - helps tune gesture detection thresholds.

Run this script to test and adjust gesture recognition in real-time.
Press keys 0-5 to test specific finger counts, 'q' to quit.
"""
import cv2
import sys
from src.hand_tracker import HandTracker
import src.gestures as gestures

# Try Picamera2 first
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False


def draw_finger_count_debug(frame, landmarks, count, direction=None):
    """Draw debug info showing which fingers are detected as extended."""
    h, w = frame.shape[:2]
    
    # Draw all landmarks
    for i, (x, y, z) in enumerate(landmarks):
        cx, cy = int(x * w), int(y * h)
        cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
        
        # Highlight fingertips
        if i in [4, 8, 12, 16, 20]:
            cv2.circle(frame, (cx, cy), 8, (255, 0, 255), 2)
    
    # Draw finger count
    cv2.putText(frame, f"Fingers: {count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
    
    # Draw direction if detected
    if direction:
        cv2.putText(frame, f"Direction: {direction.upper()}", (10, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 128, 0), 2)


def main():
    print("=" * 60)
    print("GESTURE CALIBRATION TOOL")
    print("=" * 60)
    print("\nInstructions:")
    print("- Show your hand to the camera")
    print("- Try different finger counts (1, 2, 3, 4, 5)")
    print("- The detected count will be displayed on screen")
    print("- Press 'q' to quit")
    print("- Press 's' to save a snapshot")
    print("\nIf detection is inaccurate, adjust angle_threshold in")
    print("src/gestures.py count_extended_fingers() function")
    print("=" * 60)
    
    tracker = HandTracker()
    
    # Initialize camera
    picam2 = None
    cap = None
    
    if PICAMERA2_AVAILABLE:
        try:
            print("\n[INFO] Using Picamera2...")
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)}
            )
            picam2.configure(config)
            picam2.start()
            print("[INFO] Camera initialized successfully")
        except Exception as e:
            print(f"[WARNING] Picamera2 failed: {e}")
            picam2 = None
    
    if picam2 is None:
        print("\n[INFO] Using OpenCV VideoCapture...")
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Cannot open camera!")
            return
        print("[INFO] Camera opened")
    
    # Create window
    window_name = "Gesture Calibration"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)
    
    snapshot_count = 0
    
    try:
        while True:
            # Capture frame
            if picam2 is not None:
                frame_raw = picam2.capture_array()
                frame = cv2.cvtColor(frame_raw, cv2.COLOR_RGB2BGR)
            else:
                ret, frame = cap.read()
                if not ret:
                    print("[ERROR] Failed to read frame")
                    break
            
            # Flip frame if camera is upside down
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            # Process hand tracking
            hands = tracker.process_frame(frame)
            
            if hands:
                hand = hands[0]
                landmarks = hand["landmarks"]
                
                # Count fingers
                finger_count = gestures.count_extended_fingers(landmarks, hand.get("handedness"))
                
                # Detect gesture with direction
                try:
                    gesture_info = gestures.detect_gesture_with_direction(landmarks, hand.get("handedness"))
                    gesture = gesture_info['gesture']
                    direction = gesture_info['direction']
                    combined = gesture_info['combined']
                except (AttributeError, KeyError):
                    gesture = gestures.detect_gesture_with_handedness(landmarks, hand.get("handedness"))
                    direction = None
                    combined = gesture
                
                # Draw debug info
                draw_finger_count_debug(frame, landmarks, finger_count, direction)
                
                # Display gesture name
                if gesture:
                    display_text = gesture
                    if direction:
                        display_text = f"{gesture} + {direction}"
                    cv2.putText(frame, f"Gesture: {display_text}", (10, 70), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                
                # Display combined gesture
                if combined and combined != gesture:
                    cv2.putText(frame, f"Combined: {combined}", (10, 110), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 255, 128), 2)
                
                # Display handedness
                cv2.putText(frame, f"{hand.get('handedness', 'Unknown')} hand", (10, 190), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            else:
                # Reset movement tracking when no hand
                gestures.reset_movement_tracking()
                cv2.putText(frame, "No hand detected", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            
            # Display instructions
            cv2.putText(frame, "Press 'q' to quit, 's' to snapshot", (10, frame.shape[0] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow(window_name, frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n[INFO] Exiting...")
                break
            elif key == ord('s'):
                snapshot_count += 1
                filename = f"calibration_snapshot_{snapshot_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"[INFO] Saved snapshot: {filename}")
    
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    
    finally:
        if picam2 is not None:
            picam2.stop()
            picam2.close()
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Calibration ended")


if __name__ == "__main__":
    main()
