"""Simple rule-based gesture recognizers using hand landmarks.

Landmarks: list of 21 (x,y,z) tuples as returned by HandTracker.
"""
import math
from typing import List, Tuple, Optional

Landmark = Tuple[float, float, float]


def _dist(a: Landmark, b: Landmark) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_pinch(landmarks: List[Landmark], thresh: float = 0.05) -> bool:
    """Detect a simple pinch: thumb tip (4) close to index tip (8)."""
    if not landmarks or len(landmarks) < 9:
        return False
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    return _dist(thumb_tip, index_tip) < thresh


def is_fist(landmarks: List[Landmark], thresh: float = 0.08) -> bool:
    """Rough fist detection: average distance of finger tips to wrist is small."""
    if not landmarks or len(landmarks) < 21:
        return False
    wrist = landmarks[0]
    tips = [landmarks[i] for i in (4, 8, 12, 16, 20)]
    avg = sum(_dist(wrist, t) for t in tips) / len(tips)
    return avg < thresh


def is_open_hand(landmarks: List[Landmark], thresh: float = 0.12) -> bool:
    """Detect open hand: finger tips are far from wrist on average."""
    if not landmarks or len(landmarks) < 21:
        return False
    wrist = landmarks[0]
    tips = [landmarks[i] for i in (4, 8, 12, 16, 20)]
    avg = sum(_dist(wrist, t) for t in tips) / len(tips)
    return avg > thresh


def is_pointing_index(landmarks: List[Landmark], thresh: float = 0.06) -> bool:
    """Index pointing: index tip far from wrist while other fingertips relatively close."""
    if not landmarks or len(landmarks) < 21:
        return False
    wrist = landmarks[0]
    index_tip = landmarks[8]
    other_tips = [landmarks[i] for i in (4, 12, 16, 20)]
    index_dist = _dist(wrist, index_tip)
    others_avg = sum(_dist(wrist, t) for t in other_tips) / len(other_tips)
    return index_dist > others_avg + thresh


def detect_gesture(landmarks: List[Landmark]) -> Optional[str]:
    """Return a gesture string or None."""
    if is_pinch(landmarks):
        return "pinch"
    if is_fist(landmarks):
        return "fist"
    if is_open_hand(landmarks):
        return "open"
    if is_pointing_index(landmarks):
        return "point"
    return None
