"""Simple rule-based gesture recognizers using hand landmarks.

Landmarks: list of 21 (x,y,z) tuples as returned by HandTracker.
"""
import math
from typing import List, Tuple, Optional

Landmark = Tuple[float, float, float]


def _dist(a: Landmark, b: Landmark) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle_between(a: Landmark, b: Landmark, c: Landmark) -> float:
    """Return angle (degrees) at point b for triangle a-b-c.

    Angle between vectors ba and bc.
    """
    # vectors: v1 = a - b, v2 = c - b
    v1 = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    v2 = (c[0] - b[0], c[1] - b[1], c[2] - b[2])
    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    n1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
    n2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)
    if n1 == 0 or n2 == 0:
        return 180.0
    cosang = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.degrees(math.acos(cosang))


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
    return detect_gesture_with_handedness(landmarks, None)


def detect_gesture_with_handedness(landmarks: List[Landmark], handedness: Optional[str] = None) -> Optional[str]:
    """Return a gesture string or None. Accepts optional handedness ('Left'|'Right').

    Rules (priority):
    - pinch
    - fist
    - count of extended fingers (5=open, 0=fist, 1,2)
    - point (index extended specially)
    """
    if is_pinch(landmarks):
        return "pinch"
    if is_fist(landmarks):
        return "fist"

    # count extended fingers (including thumb if detectable)
    n = count_extended_fingers(landmarks, handedness)
    if n == 5:
        return "open"
    if n == 0:
        return "fist"
    if n == 1:
        return "one"
    if n == 2:
        return "two"

    if is_pointing_index(landmarks):
        return "point"

    return None


def count_extended_fingers(landmarks: List[Landmark], handedness: Optional[str] = None) -> int:
    """Return number of extended fingers (0-5).

    Method:
    - For index/middle/ring/pinky: compare tip.y < pip.y (y smaller = higher on image => extended).
    - For thumb: use x comparison between tip and IP/MCP depending on handedness. If handedness is None, attempt heuristic.
    """
    if not landmarks or len(landmarks) < 21:
        return 0

    tips = [4, 8, 12, 16, 20]
    pips = [3, 6, 10, 14, 18]  # for thumb use 3 as reference

    extended = 0

    # robust, rotation-invariant check using joint angles
    # For each finger, compute the angle at the pip joint between mcp->pip and tip->pip.
    # If the angle is small (finger is roughly straight), count as extended.
    # landmarks indices: thumb mcp=2, ip(pip)=3, tip=4 ; index mcp=5 pip=6 tip=8 ; etc.
    finger_indices = [
        (2, 3, 4),  # thumb: mcp, ip, tip
        (5, 6, 8),  # index: mcp, pip, tip
        (9, 10, 12),
        (13, 14, 16),
        (17, 18, 20),
    ]

    for mcp_i, pip_i, tip_i in finger_indices:
        try:
            # angle at pip between mcp->pip and tip->pip
            angle = _angle_between(landmarks[mcp_i], landmarks[pip_i], landmarks[tip_i])
            # if angle near 180 degrees (vectors opposite), finger is near-straight -> extended
            if angle > 150.0:
                extended += 1
        except Exception:
            continue

    return extended
