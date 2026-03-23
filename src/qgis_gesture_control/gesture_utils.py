import math


def count_open_fingers(hand_landmarks):
    landmarks = hand_landmarks.landmark
    open_fingers = 0

    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]

    for tip_id, pip_id in zip(finger_tips, finger_pips):
        if landmarks[tip_id].y < landmarks[pip_id].y:
            open_fingers += 1

    return open_fingers


def detect_hand_state(hand_landmarks):
    open_fingers = count_open_fingers(hand_landmarks)

    if open_fingers >= 3:
        return "OPEN"
    elif open_fingers <= 1:
        return "FIST"
    else:
        return "UNKNOWN"


def get_hand_center(hand_landmarks, w, h):
    xs = [lm.x for lm in hand_landmarks.landmark]
    ys = [lm.y for lm in hand_landmarks.landmark]
    return int(sum(xs) / len(xs) * w), int(sum(ys) / len(ys) * h)


def get_pan_anchor(hand_landmarks, w, h):
    wrist = hand_landmarks.landmark[0]
    middle_mcp = hand_landmarks.landmark[9]

    x = int(((wrist.x + middle_mcp.x) / 2) * w)
    y = int(((wrist.y + middle_mcp.y) / 2) * h)

    return x, y


def get_point(hand_landmarks, idx, w, h):
    lm = hand_landmarks.landmark[idx]
    return int(lm.x * w), int(lm.y * h)


def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def is_strict_zoom_pinch_shape(hand_landmarks, w, h):
    thumb = get_point(hand_landmarks, 4, w, h)
    index = get_point(hand_landmarks, 8, w, h)
    middle = get_point(hand_landmarks, 12, w, h)
    ring = get_point(hand_landmarks, 16, w, h)
    pinky = get_point(hand_landmarks, 20, w, h)

    thumb_index = distance(thumb, index)

    strict_pinch_close_threshold = 28
    other_fingers_far_threshold = 55

    thumb_index_close = thumb_index <= strict_pinch_close_threshold

    def far(p, others):
        return all(distance(p, o) >= other_fingers_far_threshold for o in others)

    thumb_far = far(thumb, [middle, ring, pinky])
    index_far = far(index, [middle, ring, pinky])

    valid = thumb_index_close and thumb_far and index_far

    return valid, thumb_index, thumb, index


def is_open_hand(hand_landmarks):
    return count_open_fingers(hand_landmarks) >= 3


def get_two_hand_distance(hand1, hand2, w, h):
    c1 = get_hand_center(hand1, w, h)
    c2 = get_hand_center(hand2, w, h)
    return distance(c1, c2), c1, c2


def is_index_extended(hand_landmarks):
    landmarks = hand_landmarks.landmark
    return landmarks[8].y < landmarks[6].y


def is_middle_folded(hand_landmarks):
    landmarks = hand_landmarks.landmark
    return landmarks[12].y > landmarks[10].y


def is_ring_folded(hand_landmarks):
    landmarks = hand_landmarks.landmark
    return landmarks[16].y > landmarks[14].y


def is_pinky_folded(hand_landmarks):
    landmarks = hand_landmarks.landmark
    return landmarks[20].y > landmarks[18].y


def is_index_pointer_pose(hand_landmarks):
    index_extended = is_index_extended(hand_landmarks)
    middle_folded = is_middle_folded(hand_landmarks)
    ring_folded = is_ring_folded(hand_landmarks)
    pinky_folded = is_pinky_folded(hand_landmarks)

    return index_extended and middle_folded and ring_folded and pinky_folded


def is_index_bent(hand_landmarks):
    landmarks = hand_landmarks.landmark
    return landmarks[8].y > landmarks[6].y


def get_index_tip(hand_landmarks, w, h):
    return get_point(hand_landmarks, 8, w, h)