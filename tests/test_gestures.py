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
