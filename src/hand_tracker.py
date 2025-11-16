import cv2
import numpy as np

try:
    import mediapipe as mp
except Exception:  # mediapipe may not be installed yet on the dev machine
    mp = None


class HandTracker:
    """Wrapper around MediaPipe Hands to return normalized landmarks and handedness.

    Usage:
        tracker = HandTracker(max_num_hands=2)
        hands = tracker.process_frame(frame)
        # hands -> list of {landmarks: [(x,y,z),...], handedness: 'Left'|'Right', score: float}
    """

    def __init__(self, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        if mp is None:
            raise RuntimeError("mediapipe not available; install mediapipe to use HandTracker")

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )

    def process_frame(self, frame_bgr):
        """Process a BGR OpenCV frame and return detected hands as normalized landmarks.

        Returns list of dicts: {landmarks: [(x,y,z),...], handedness: str, score: float}
        """
        img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        out = []
        if not results.multi_hand_landmarks:
            return out

        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            lm = []
            for p in hand_landmarks.landmark:
                lm.append((p.x, p.y, p.z))
            out.append({
                "landmarks": lm,
                "handedness": handedness.classification[0].label,
                "score": float(handedness.classification[0].score),
            })
        return out
