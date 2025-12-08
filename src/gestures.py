"""Simple rule-based gesture recognizers using hand landmarks.

Landmarks: list of 21 (x,y,z) tuples as returned by HandTracker.
"""
import math
from typing import List, Tuple, Optional, Dict

Landmark = Tuple[float, float, float]

# Store previous hand position for direction tracking
_prev_hand_center: Optional[Tuple[float, float]] = None
_movement_threshold = 0.05  # Minimum movement to trigger direction detection


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


def get_hand_center(landmarks: List[Landmark]) -> Tuple[float, float]:
    """Calculate the center point of the hand (average of all landmarks)."""
    if not landmarks:
        return (0.0, 0.0)
    x_sum = sum(lm[0] for lm in landmarks)
    y_sum = sum(lm[1] for lm in landmarks)
    return (x_sum / len(landmarks), y_sum / len(landmarks))


def detect_movement_direction(landmarks: List[Landmark]) -> Optional[str]:
    """Detect if hand is moving in a direction (left, right, up, down).
    
    Returns direction string or None if not enough movement detected.
    """
    global _prev_hand_center
    
    current_center = get_hand_center(landmarks)
    
    if _prev_hand_center is None:
        _prev_hand_center = current_center
        return None
    
    # Calculate movement delta
    dx = current_center[0] - _prev_hand_center[0]
    dy = current_center[1] - _prev_hand_center[1]
    
    # Update previous position
    _prev_hand_center = current_center
    
    # Check if movement exceeds threshold
    movement = math.sqrt(dx * dx + dy * dy)
    if movement < _movement_threshold:
        return None
    
    # Determine primary direction (larger movement wins)
    if abs(dx) > abs(dy):
        # Horizontal movement
        if dx > 0:
            return "right"
        else:
            return "left"
    else:
        # Vertical movement
        if dy > 0:
            return "down"
        else:
            return "up"


def reset_movement_tracking():
    """Reset the movement tracking (call when starting fresh or gesture changes)."""
    global _prev_hand_center
    _prev_hand_center = None


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
    1. pinch (thumb and index close)
    2. fist (all fingers closed)
    3. finger counting (1, 2, 3, 4, or 5 fingers)
    """
    # Check pinch first (highest priority)
    if is_pinch(landmarks):
        return "pinch"
    
    # Count extended fingers
    n = count_extended_fingers(landmarks, handedness)
    
    # Map finger count to gestures
    if n == 0:
        return "fist"
    elif n == 1:
        return "one"
    elif n == 2:
        return "two"
    elif n == 3:
        return "three"
    elif n == 4:
        return "four"
    elif n == 5:
        return "five"

    return None


def detect_gesture_with_direction(landmarks: List[Landmark], handedness: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Return both gesture and movement direction.
    
    Returns:
        dict with keys:
        - 'gesture': the base gesture (one, two, three, etc.)
        - 'direction': movement direction (left, right, up, down) or None
        - 'combined': combined gesture+direction string (e.g., "two_left") or just gesture
    """
    gesture = detect_gesture_with_handedness(landmarks, handedness)
    direction = detect_movement_direction(landmarks)
    
    result = {
        'gesture': gesture,
        'direction': direction,
        'combined': gesture
    }
    
    # Create combined gesture if both exist
    if gesture and direction:
        result['combined'] = f"{gesture}_{direction}"
    
    return result


def count_extended_fingers(landmarks: List[Landmark], handedness: Optional[str] = None) -> int:
    """Return number of extended fingers (0-5).

    Improved method using angle-based detection:
    - For each finger, check if it's extended by measuring the angle at joints
    - A straighter angle (closer to 180°) indicates an extended finger
    - Adjustable threshold for better accuracy
    """
    if not landmarks or len(landmarks) < 21:
        return 0

    # MediaPipe hand landmark indices:
    # Thumb: 1(CMC), 2(MCP), 3(IP), 4(TIP)
    # Index: 5(MCP), 6(PIP), 7(DIP), 8(TIP)
    # Middle: 9(MCP), 10(PIP), 11(DIP), 12(TIP)
    # Ring: 13(MCP), 14(PIP), 15(DIP), 16(TIP)
    # Pinky: 17(MCP), 18(PIP), 19(DIP), 20(TIP)
    
    extended = 0
    
    # Angle threshold: if angle > this value, finger is extended
    angle_threshold = 140.0  # Adjustable - lower = stricter, higher = more lenient
    
    # Check thumb (special case - uses different joints)
    try:
        # Thumb: check angle at IP joint (index 3)
        thumb_angle = _angle_between(landmarks[2], landmarks[3], landmarks[4])
        # Also check if thumb tip is far from palm
        thumb_tip_dist = _dist(landmarks[0], landmarks[4])  # wrist to thumb tip
        palm_center = landmarks[0]  # wrist as reference
        
        # Thumb is extended if angle is large OR tip is far from palm
        if thumb_angle > angle_threshold or thumb_tip_dist > 0.15:
            extended += 1
    except Exception:
        pass
    
    # Check other four fingers (index, middle, ring, pinky)
    finger_joints = [
        (5, 6, 8),   # Index: MCP, PIP, TIP
        (9, 10, 12),  # Middle: MCP, PIP, TIP
        (13, 14, 16), # Ring: MCP, PIP, TIP
        (17, 18, 20), # Pinky: MCP, PIP, TIP
    ]
    
    for mcp_i, pip_i, tip_i in finger_joints:
        try:
            # Calculate angle at PIP joint
            angle = _angle_between(landmarks[mcp_i], landmarks[pip_i], landmarks[tip_i])
            
            # Also check if tip is above (y coordinate smaller) the MCP joint
            # This helps when hand is tilted
            tip_y = landmarks[tip_i][1]
            mcp_y = landmarks[mcp_i][1]
            
            # Finger is extended if angle is large AND tip is higher than base
            if angle > angle_threshold and tip_y < mcp_y + 0.05:
                extended += 1
        except Exception:
            continue

    return extended
