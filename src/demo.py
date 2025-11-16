"""Demo application: capture webcam, track hands, detect gestures, and send robot commands."""
import argparse
import time
import cv2
from typing import Optional

from src.hand_tracker import HandTracker
from src.gestures import detect_gesture
from src.robot_interface import MockRobot, SerialRobot


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
    else:
        robot = SerialRobot()

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
                gesture = detect_gesture(hand["landmarks"])
                if gesture:
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 2)

            # send gesture to robot on change with debounce
            now = time.time()
            if gesture and gesture != last_gesture and (now - last_sent) > 0.5:
                robot.send_command(gesture)
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
