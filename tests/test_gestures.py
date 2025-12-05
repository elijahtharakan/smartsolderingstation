from src.gestures import is_pinch, is_open_hand, is_fist, is_pointing_index


def _make_landmarks(offset=0.0):
    # simple synthetic landmarks: wrist at (0,0), thumb/index tips at varying x
    lm = [(0.0, 0.0, 0.0)] * 21
    # thumb tip index 4
    lm[4] = (0.02, 0.0, 0.0)
    # index tip index 8 (separated by offset)
    lm[8] = (0.02 + offset, 0.0, 0.0)
    # other tips spread out
    lm[12] = (0.12, 0.0, 0.0)
    lm[16] = (0.12, 0.0, 0.0)
    lm[20] = (0.12, 0.0, 0.0)
    return lm


def test_pinch_detected():
    lm = _make_landmarks(offset=0.0)
    assert is_pinch(lm)


def test_open_hand_not_pinch():
    lm = _make_landmarks(offset=0.2)
    assert not is_pinch(lm)


def test_count_one_finger():
    # index up only
    lm = [(0.5, 0.5, 0.0)] * 21
    # index tip (8) above pip (6)
    # set mcp, pip, tip for index so the angle method recognizes extension
    lm[5] = (0.5, 0.6, 0.0)  # mcp below pip
    lm[6] = (0.5, 0.5, 0.0)  # pip
    lm[8] = (0.5, 0.2, 0.0)  # tip (up)
    # middle/ring/pinky down
    lm[10] = (0.5, 0.4, 0.0)
    lm[12] = (0.5, 0.6, 0.0)
    lm[14] = (0.5, 0.4, 0.0)
    lm[16] = (0.5, 0.6, 0.0)
    lm[18] = (0.5, 0.4, 0.0)
    lm[20] = (0.5, 0.6, 0.0)
    from src.gestures import count_extended_fingers
    assert count_extended_fingers(lm, handedness=None) >= 1


def test_count_two_fingers():
    # index + middle up
    lm = [(0.5, 0.5, 0.0)] * 21
    # index: set mcp,pip,tip
    lm[5] = (0.5, 0.6, 0.0)
    lm[6] = (0.5, 0.5, 0.0)
    lm[8] = (0.5, 0.2, 0.0)
    # middle: set mcp,pip,tip
    lm[9] = (0.5, 0.6, 0.0)
    lm[10] = (0.5, 0.5, 0.0)
    lm[12] = (0.5, 0.2, 0.0)
    # others down
    lm[14] = (0.5, 0.5, 0.0)
    lm[16] = (0.5, 0.7, 0.0)
    lm[18] = (0.5, 0.5, 0.0)
    lm[20] = (0.5, 0.7, 0.0)
    from src.gestures import count_extended_fingers
    assert count_extended_fingers(lm, handedness=None) >= 2
