"""Demo application: capture webcam, track hands, detect gestures, and send robot commands."""
import argparse
import time
import cv2
import yaml
from typing import Optional

from src.hand_tracker import HandTracker
import src.gestures as gestures
from src.robot_interface import MockRobot, SerialRobot, PiGPIORobot


def draw_hand_info(frame, hand):
    h, w = frame.shape[:2]
    for (x, y, z) in hand["landmarks"]:
        cx, cy = int(x * w), int(y * h)
        cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
    cv2.putText(frame, f"{hand['handedness']} {hand.get('score',0):.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)


def main(robot_type: str = "mock"):
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

    cap = cv2.VideoCapture(0)
    last_gesture: Optional[str] = None
    last_sent = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            hands = tracker.process_frame(frame)
            gesture = None
            if hands:
                # just process first hand for demo
                hand = hands[0]
                draw_hand_info(frame, hand)
                gesture = None
                # prefer handedness-aware API when available in the gestures module
                try:
                    gesture = gestures.detect_gesture_with_handedness(hand["landmarks"], hand.get("handedness"))
                except AttributeError:
                    try:
                        gesture = gestures.detect_gesture(hand["landmarks"])
                    except AttributeError:
                        gesture = None
                if gesture:
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 2)

            # send gesture to robot on change with debounce
            now = time.time()
            if gesture and gesture != last_gesture and (now - last_sent) > 0.5:
                # map gesture to command via config if available
                cmd = None
                if cfg and 'gestures' in cfg and gesture in cfg['gestures']:
                    cmd = cfg['gestures'][gesture]
                else:
                    cmd = gesture
                robot.send_command(cmd)
                last_gesture = gesture
                last_sent = now

            cv2.imshow("Gesture → Robot Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", choices=["mock", "serial"], default="mock")
    args = parser.parse_args()
    main(robot_type=args.robot)
