import cv2
import mediapipe as mp
import math
import pyautogui

from .gesture_utils import (
    get_two_hand_distance,
    is_open_hand,
    get_index_tip,
    get_hand_center,
    detect_hand_state,
)
from .gesture_state import create_state
from .config import (
    ZOOM_ENTER_STABLE_FRAMES,
    ZOOM_CONTINUOUS_THRESHOLD,
    ZOOM_LOST_TOLERANCE_FRAMES,
    POINTER_LOST_TOLERANCE_FRAMES,
    NAV_LOST_TOLERANCE_FRAMES,
    PAN_LOST_TOLERANCE_FRAMES,
    CLICK_COOLDOWN_FRAMES,
    CLICK_FLASH_FRAMES,
    TEST_BOX_BASE_SIZE,
    TEST_BOX_MIN_SIZE,
    TEST_BOX_MAX_SIZE,
    INDEX_TIP_MARKER_RADIUS,
    POINTER_DIRECT_SMOOTHING,
    POINTER_SNAP_DISTANCE,
    MOUSE_POINTER_SMOOTHING,
    MOUSE_POINTER_SNAP_DISTANCE,
    PAN_SCALE_X,
    PAN_SCALE_Y,
    PAN_DEADZONE,
    SCROLL_STEP,
    SCROLL_COOLDOWN_FRAMES,
    DWELL_RADIUS_PIXELS,
    DWELL_FRAMES_REQUIRED,
    MODE_NONE,
    MODE_ZOOM,
    MODE_POINTER,
    MODE_NAV,
    MODE_PAN,
)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


def reset_zoom_state(state):
    state["zoom_ready_frames"] = 0
    state["zoom_active"] = False
    state["zoom_baseline_distance"] = None
    state["zoom_previous_distance"] = None
    state["zoom_current_distance"] = None
    state["zoom_lost_frames"] = 0
    state["zoom_mouse_primed"] = False


def reset_pointer_state(state):
    state["pointer_active"] = False
    state["pointer_initialized"] = False
    state["pointer_preview_x"] = None
    state["pointer_preview_y"] = None
    state["smoothed_cursor_x"] = None
    state["smoothed_cursor_y"] = None
    state["mouse_cursor_x"] = None
    state["mouse_cursor_y"] = None
    state["pointer_lost_frames"] = 0
    state["last_index_tip"] = None
    state["dwell_anchor_x"] = None
    state["dwell_anchor_y"] = None
    state["dwell_counter"] = 0


def reset_nav_state(state):
    state["nav_active"] = False
    state["nav_lost_frames"] = 0


def reset_pan_state(state):
    if state.get("mouse_dragging", False):
        pyautogui.mouseUp(button="middle")
        state["mouse_dragging"] = False

    state["pan_active"] = False
    state["pan_initialized"] = False
    state["pan_anchor_hand"] = None
    state["pan_lost_frames"] = 0


def reset_all_modes(state):
    reset_zoom_state(state)
    reset_pointer_state(state)
    reset_nav_state(state)
    reset_pan_state(state)
    state["mode"] = MODE_NONE
    state["last_command_text"] = "IDLE"


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def get_point(hand_landmarks, idx, w, h):
    lm = hand_landmarks.landmark[idx]
    return int(lm.x * w), int(lm.y * h)


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


def is_pointer_pose_stronger(hand_landmarks, w, h):
    index_extended = is_index_extended(hand_landmarks)
    middle_folded = is_middle_folded(hand_landmarks)
    ring_folded = is_ring_folded(hand_landmarks)
    pinky_folded = is_pinky_folded(hand_landmarks)

    if not (index_extended and middle_folded and ring_folded and pinky_folded):
        return False

    index_tip = get_point(hand_landmarks, 8, w, h)
    middle_tip = get_point(hand_landmarks, 12, w, h)
    ring_tip = get_point(hand_landmarks, 16, w, h)
    pinky_tip = get_point(hand_landmarks, 20, w, h)
    wrist = get_point(hand_landmarks, 0, w, h)

    others_center_x = (middle_tip[0] + ring_tip[0] + pinky_tip[0]) / 3
    others_center_y = (middle_tip[1] + ring_tip[1] + pinky_tip[1]) / 3

    index_separation = distance(index_tip, (others_center_x, others_center_y))
    hand_size = max(distance(wrist, middle_tip), 1)

    return index_separation > hand_size * 0.55


def ensure_extra_state(state):
    if "zoom_lost_frames" not in state:
        state["zoom_lost_frames"] = 0
    if "zoom_mouse_primed" not in state:
        state["zoom_mouse_primed"] = False
    if "pointer_lost_frames" not in state:
        state["pointer_lost_frames"] = 0
    if "nav_lost_frames" not in state:
        state["nav_lost_frames"] = 0
    if "pan_lost_frames" not in state:
        state["pan_lost_frames"] = 0
    if "click_flash_frames" not in state:
        state["click_flash_frames"] = 0
    if "scroll_cooldown" not in state:
        state["scroll_cooldown"] = 0
    if "test_box_size" not in state:
        state["test_box_size"] = TEST_BOX_BASE_SIZE
    if "test_box_center_x" not in state:
        state["test_box_center_x"] = None
    if "test_box_center_y" not in state:
        state["test_box_center_y"] = None
    if "nav_active" not in state:
        state["nav_active"] = False
    if "pan_active" not in state:
        state["pan_active"] = False
    if "pan_initialized" not in state:
        state["pan_initialized"] = False
    if "pan_anchor_hand" not in state:
        state["pan_anchor_hand"] = None
    if "mouse_dragging" not in state:
        state["mouse_dragging"] = False
    if "mouse_cursor_x" not in state:
        state["mouse_cursor_x"] = None
    if "mouse_cursor_y" not in state:
        state["mouse_cursor_y"] = None
    if "dwell_anchor_x" not in state:
        state["dwell_anchor_x"] = None
    if "dwell_anchor_y" not in state:
        state["dwell_anchor_y"] = None
    if "dwell_counter" not in state:
        state["dwell_counter"] = 0


def draw_test_box(frame, state):
    h, w, _ = frame.shape

    box_size = int(
        clamp(
            state.get("test_box_size", TEST_BOX_BASE_SIZE),
            TEST_BOX_MIN_SIZE,
            TEST_BOX_MAX_SIZE,
        )
    )

    if state["test_box_center_x"] is None:
        state["test_box_center_x"] = w // 2
    if state["test_box_center_y"] is None:
        state["test_box_center_y"] = h // 2

    cx = int(clamp(state["test_box_center_x"], box_size // 2, w - box_size // 2))
    cy = int(clamp(state["test_box_center_y"], box_size // 2, h - box_size // 2))

    state["test_box_center_x"] = cx
    state["test_box_center_y"] = cy

    x1 = cx - box_size // 2
    y1 = cy - box_size // 2
    x2 = cx + box_size // 2
    y2 = cy + box_size // 2

    if state.get("click_flash_frames", 0) > 0:
        color = (0, 255, 255)
        thickness = 4
    elif state["mode"] == MODE_ZOOM:
        color = (255, 0, 255)
        thickness = 3
    elif state["mode"] == MODE_POINTER:
        color = (0, 200, 255)
        thickness = 3
    elif state["mode"] == MODE_PAN:
        color = (0, 255, 120)
        thickness = 3
    elif state["mode"] == MODE_NAV:
        color = (255, 180, 0)
        thickness = 3
    else:
        color = (180, 180, 180)
        thickness = 2

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    if (
        state["mode"] == MODE_POINTER
        and state["pointer_preview_x"] is not None
        and state["pointer_preview_y"] is not None
    ):
        px = int(clamp(state["pointer_preview_x"], x1, x2))
        py = int(clamp(state["pointer_preview_y"], y1, y2))
        cv2.circle(frame, (px, py), 8, (0, 0, 255), -1)

    return x1, y1, x2, y2


def draw_overlay(frame, state):
    font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(frame, f"MODE: {state['mode']}", (20, 30), font, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, f"CMD: {state['last_command_text']}", (20, 60), font, 0.8, (255, 255, 0), 2)
    cv2.putText(frame, f"ZOOM READY: {state['zoom_ready_frames']}", (20, 90), font, 0.7, (255, 255, 255), 2)

    if state["zoom_current_distance"] is not None:
        cv2.putText(
            frame,
            f"HAND DIST: {int(state['zoom_current_distance'])}",
            (20, 120),
            font,
            0.7,
            (255, 255, 255),
            2,
        )

    cv2.putText(frame, f"ZOOM LOST: {state.get('zoom_lost_frames', 0)}", (20, 150), font, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"POINTER LOST: {state.get('pointer_lost_frames', 0)}", (20, 180), font, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"NAV LOST: {state.get('nav_lost_frames', 0)}", (20, 210), font, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"PAN LOST: {state.get('pan_lost_frames', 0)}", (20, 240), font, 0.7, (255, 255, 255), 2)

    if state["click_cooldown"] > 0:
        cv2.putText(frame, f"CLICK COOLDOWN: {state['click_cooldown']}", (20, 270), font, 0.7, (0, 200, 255), 2)

    cv2.putText(
        frame,
        f"DWELL: {state.get('dwell_counter', 0)} / {DWELL_FRAMES_REQUIRED}",
        (20, 300),
        font,
        0.7,
        (0, 255, 255),
        2,
    )


def prime_zoom_target(screen_center_x, screen_center_y):
    pyautogui.moveTo(screen_center_x, screen_center_y, duration=0)


def main():
    cap = cv2.VideoCapture(0)
    state = create_state()
    ensure_extra_state(state)

    screen_w, screen_h = pyautogui.size()
    screen_center_x = screen_w // 2
    screen_center_y = screen_h // 2

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as hands:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Ne mogu da procitam frame sa kamere.")
                break

            state["frame_index"] += 1

            if state["click_cooldown"] > 0:
                state["click_cooldown"] -= 1

            if state["click_flash_frames"] > 0:
                state["click_flash_frames"] -= 1

            if state["scroll_cooldown"] > 0:
                state["scroll_cooldown"] -= 1

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            detected_hands = []

            if results.multi_hand_landmarks:
                for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    handedness_label = "Unknown"

                    if results.multi_handedness and idx < len(results.multi_handedness):
                        handedness_label = results.multi_handedness[idx].classification[0].label

                    detected_hands.append(
                        {
                            "landmarks": hand_landmarks,
                            "label": handedness_label,
                        }
                    )

                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style(),
                    )

                    wrist = hand_landmarks.landmark[0]
                    wrist_x = int(wrist.x * w)
                    wrist_y = int(wrist.y * h)

                    cv2.putText(
                        frame,
                        handedness_label,
                        (wrist_x, wrist_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )

            hand_count = len(detected_hands)

            box_x1, box_y1, box_x2, box_y2 = draw_test_box(frame, state)

            if hand_count == 2:
                reset_pointer_state(state)
                reset_nav_state(state)
                reset_pan_state(state)

                hand1 = detected_hands[0]["landmarks"]
                hand2 = detected_hands[1]["landmarks"]

                hand1_open = is_open_hand(hand1)
                hand2_open = is_open_hand(hand2)

                hand_distance, c1, c2 = get_two_hand_distance(hand1, hand2, w, h)
                state["zoom_current_distance"] = hand_distance

                cv2.line(frame, c1, c2, (255, 0, 255), 2)
                cv2.circle(frame, c1, 8, (255, 0, 255), -1)
                cv2.circle(frame, c2, 8, (255, 0, 255), -1)

                if hand1_open and hand2_open:
                    state["zoom_lost_frames"] = 0
                    state["zoom_ready_frames"] += 1

                    if state["zoom_ready_frames"] >= ZOOM_ENTER_STABLE_FRAMES:
                        if not state["zoom_active"]:
                            state["zoom_active"] = True
                            state["mode"] = MODE_ZOOM
                            state["zoom_baseline_distance"] = hand_distance
                            state["zoom_previous_distance"] = hand_distance
                            state["last_command_text"] = "ZOOM_READY"
                            if not state["zoom_mouse_primed"]:
                                prime_zoom_target(screen_center_x, screen_center_y)
                                state["zoom_mouse_primed"] = True
                        else:
                            if not state["zoom_mouse_primed"]:
                                prime_zoom_target(screen_center_x, screen_center_y)
                                state["zoom_mouse_primed"] = True

                            delta = hand_distance - state["zoom_previous_distance"]

                            if delta > ZOOM_CONTINUOUS_THRESHOLD:
                                state["last_command_text"] = "ZOOM_IN"
                                state["test_box_size"] = clamp(
                                    state["test_box_size"] + abs(delta) * 0.35,
                                    TEST_BOX_MIN_SIZE,
                                    TEST_BOX_MAX_SIZE,
                                )
                                if state["scroll_cooldown"] == 0:
                                    pyautogui.scroll(SCROLL_STEP)
                                    state["scroll_cooldown"] = SCROLL_COOLDOWN_FRAMES

                            elif delta < -ZOOM_CONTINUOUS_THRESHOLD:
                                state["last_command_text"] = "ZOOM_OUT"
                                state["test_box_size"] = clamp(
                                    state["test_box_size"] - abs(delta) * 0.35,
                                    TEST_BOX_MIN_SIZE,
                                    TEST_BOX_MAX_SIZE,
                                )
                                if state["scroll_cooldown"] == 0:
                                    pyautogui.scroll(-SCROLL_STEP)
                                    state["scroll_cooldown"] = SCROLL_COOLDOWN_FRAMES

                            else:
                                state["last_command_text"] = "ZOOM_HOLD"

                            state["zoom_previous_distance"] = hand_distance
                            state["mode"] = MODE_ZOOM
                    else:
                        state["mode"] = MODE_NONE
                        state["last_command_text"] = "ZOOM_ARMING"
                else:
                    if state["zoom_active"]:
                        state["zoom_lost_frames"] += 1
                        state["mode"] = MODE_ZOOM
                        state["last_command_text"] = "ZOOM_GRACE"

                        if state["zoom_lost_frames"] > ZOOM_LOST_TOLERANCE_FRAMES:
                            reset_zoom_state(state)
                            state["mode"] = MODE_NONE
                            state["last_command_text"] = "ZOOM_STOP"
                    else:
                        reset_zoom_state(state)
                        state["mode"] = MODE_NONE
                        state["last_command_text"] = "TWO_HANDS_NOT_OPEN"

            elif hand_count == 1:
                reset_zoom_state(state)
                state["zoom_current_distance"] = None

                current_hand = detected_hands[0]
                hand_landmarks = current_hand["landmarks"]
                hand_label = current_hand["label"]

                index_tip = get_index_tip(hand_landmarks, w, h)
                hand_center = get_hand_center(hand_landmarks, w, h)
                hand_state = detect_hand_state(hand_landmarks)
                open_hand_valid = is_open_hand(hand_landmarks)

                cv2.circle(frame, index_tip, INDEX_TIP_MARKER_RADIUS, (0, 255, 0), -1)
                cv2.circle(frame, hand_center, 6, (255, 255, 0), -1)

                pointer_pose_valid = hand_label == "Right" and is_pointer_pose_stronger(hand_landmarks, w, h)
                nav_pose_valid = open_hand_valid and not pointer_pose_valid
                fist_pose_valid = hand_state == "FIST"

                if pointer_pose_valid:
                    reset_nav_state(state)
                    reset_pan_state(state)

                    state["pointer_lost_frames"] = 0
                    state["mode"] = MODE_POINTER
                    state["pointer_active"] = True

                    target_x = clamp(index_tip[0], box_x1, box_x2)
                    target_y = clamp(index_tip[1], box_y1, box_y2)

                    mouse_target_x = clamp(index_tip[0] / w * screen_w, 0, screen_w - 1)
                    mouse_target_y = clamp(index_tip[1] / h * screen_h, 0, screen_h - 1)

                    if not state["pointer_initialized"]:
                        state["pointer_initialized"] = True
                        state["pointer_preview_x"] = target_x
                        state["pointer_preview_y"] = target_y
                        state["smoothed_cursor_x"] = target_x
                        state["smoothed_cursor_y"] = target_y
                        state["mouse_cursor_x"] = mouse_target_x
                        state["mouse_cursor_y"] = mouse_target_y
                        state["dwell_anchor_x"] = mouse_target_x
                        state["dwell_anchor_y"] = mouse_target_y
                        state["dwell_counter"] = 0
                        pyautogui.moveTo(int(mouse_target_x), int(mouse_target_y), duration=0)
                        state["last_command_text"] = "POINTER_READY"
                    else:
                        lag_distance = distance(
                            (state["pointer_preview_x"], state["pointer_preview_y"]),
                            (target_x, target_y),
                        )

                        if lag_distance > POINTER_SNAP_DISTANCE:
                            state["smoothed_cursor_x"] = target_x
                            state["smoothed_cursor_y"] = target_y
                        else:
                            state["smoothed_cursor_x"] = (
                                state["smoothed_cursor_x"] * (1 - POINTER_DIRECT_SMOOTHING)
                                + target_x * POINTER_DIRECT_SMOOTHING
                            )
                            state["smoothed_cursor_y"] = (
                                state["smoothed_cursor_y"] * (1 - POINTER_DIRECT_SMOOTHING)
                                + target_y * POINTER_DIRECT_SMOOTHING
                            )

                        state["pointer_preview_x"] = clamp(state["smoothed_cursor_x"], box_x1, box_x2)
                        state["pointer_preview_y"] = clamp(state["smoothed_cursor_y"], box_y1, box_y2)

                        mouse_lag = distance(
                            (state["mouse_cursor_x"], state["mouse_cursor_y"]),
                            (mouse_target_x, mouse_target_y),
                        )

                        if mouse_lag > MOUSE_POINTER_SNAP_DISTANCE:
                            state["mouse_cursor_x"] = mouse_target_x
                            state["mouse_cursor_y"] = mouse_target_y
                        else:
                            state["mouse_cursor_x"] = (
                                state["mouse_cursor_x"] * (1 - MOUSE_POINTER_SMOOTHING)
                                + mouse_target_x * MOUSE_POINTER_SMOOTHING
                            )
                            state["mouse_cursor_y"] = (
                                state["mouse_cursor_y"] * (1 - MOUSE_POINTER_SMOOTHING)
                                + mouse_target_y * MOUSE_POINTER_SMOOTHING
                            )

                        pyautogui.moveTo(
                            int(state["mouse_cursor_x"]),
                            int(state["mouse_cursor_y"]),
                            duration=0,
                        )
                        state["last_command_text"] = "POINTER_MOVE"

                        current_cursor = (state["mouse_cursor_x"], state["mouse_cursor_y"])
                        dwell_anchor = (state["dwell_anchor_x"], state["dwell_anchor_y"])

                        if distance(current_cursor, dwell_anchor) <= DWELL_RADIUS_PIXELS:
                            if state["click_cooldown"] == 0:
                                state["dwell_counter"] += 1
                            else:
                                state["dwell_counter"] = 0
                        else:
                            state["dwell_anchor_x"] = state["mouse_cursor_x"]
                            state["dwell_anchor_y"] = state["mouse_cursor_y"]
                            state["dwell_counter"] = 0

                        if (
                            state["dwell_counter"] >= DWELL_FRAMES_REQUIRED
                            and state["click_cooldown"] == 0
                        ):
                            state["last_command_text"] = "DWELL_CLICK"
                            state["click_cooldown"] = CLICK_COOLDOWN_FRAMES
                            state["click_flash_frames"] = CLICK_FLASH_FRAMES
                            pyautogui.click(button="left")
                            state["dwell_counter"] = 0
                            state["dwell_anchor_x"] = state["mouse_cursor_x"]
                            state["dwell_anchor_y"] = state["mouse_cursor_y"]

                elif state["pan_active"]:
                    reset_pointer_state(state)

                    if open_hand_valid:
                        reset_pan_state(state)
                        state["mode"] = MODE_NAV
                        state["last_command_text"] = "PAN_EXIT_OPEN_HAND"
                    else:
                        state["mode"] = MODE_PAN

                        if fist_pose_valid:
                            state["pan_lost_frames"] = 0
                        else:
                            state["pan_lost_frames"] += 1

                        if state["pan_lost_frames"] > PAN_LOST_TOLERANCE_FRAMES:
                            reset_pan_state(state)
                            state["mode"] = MODE_NAV if state["nav_active"] else MODE_NONE
                            state["last_command_text"] = "PAN_STOP"
                        else:
                            if not state["pan_initialized"]:
                                state["pan_initialized"] = True
                                state["pan_anchor_hand"] = hand_center

                                pyautogui.moveTo(screen_center_x, screen_center_y, duration=0)
                                pyautogui.mouseDown(button="middle")

                                state["mouse_dragging"] = True
                                state["last_command_text"] = "PAN_READY_CENTER"
                            else:
                                dx = hand_center[0] - state["pan_anchor_hand"][0]
                                dy = hand_center[1] - state["pan_anchor_hand"][1]

                                if abs(dx) < PAN_DEADZONE:
                                    dx = 0
                                if abs(dy) < PAN_DEADZONE:
                                    dy = 0

                                if dx != 0 or dy != 0:
                                    state["test_box_center_x"] += dx * PAN_SCALE_X
                                    state["test_box_center_y"] += dy * PAN_SCALE_Y

                                    move_x = int(dx * PAN_SCALE_X)
                                    move_y = int(dy * PAN_SCALE_Y)
                                    pyautogui.moveRel(move_x, move_y, duration=0)

                                state["pan_anchor_hand"] = hand_center

                                if fist_pose_valid:
                                    state["last_command_text"] = f"PAN ({int(dx)}, {int(dy)})"
                                else:
                                    state["last_command_text"] = f"PAN_GRACE ({int(dx)}, {int(dy)})"

                elif nav_pose_valid:
                    reset_pointer_state(state)
                    reset_pan_state(state)

                    state["nav_active"] = True
                    state["nav_lost_frames"] = 0
                    state["mode"] = MODE_NAV
                    state["last_command_text"] = "NAV_READY"

                elif state["nav_active"] and fist_pose_valid:
                    reset_pointer_state(state)

                    state["pan_lost_frames"] = 0
                    state["mode"] = MODE_PAN
                    state["pan_active"] = True

                    if not state["pan_initialized"]:
                        state["pan_initialized"] = True
                        state["pan_anchor_hand"] = hand_center

                        pyautogui.moveTo(screen_center_x, screen_center_y, duration=0)
                        pyautogui.mouseDown(button="middle")

                        state["mouse_dragging"] = True
                        state["last_command_text"] = "PAN_READY_CENTER"
                    else:
                        dx = hand_center[0] - state["pan_anchor_hand"][0]
                        dy = hand_center[1] - state["pan_anchor_hand"][1]

                        if abs(dx) < PAN_DEADZONE:
                            dx = 0
                        if abs(dy) < PAN_DEADZONE:
                            dy = 0

                        if dx != 0 or dy != 0:
                            state["test_box_center_x"] += dx * PAN_SCALE_X
                            state["test_box_center_y"] += dy * PAN_SCALE_Y

                            move_x = int(dx * PAN_SCALE_X)
                            move_y = int(dy * PAN_SCALE_Y)
                            pyautogui.moveRel(move_x, move_y, duration=0)

                        state["pan_anchor_hand"] = hand_center
                        state["last_command_text"] = f"PAN ({int(dx)}, {int(dy)})"

                else:
                    if state["pointer_active"]:
                        state["pointer_lost_frames"] += 1
                        state["mode"] = MODE_POINTER
                        state["last_command_text"] = "POINTER_GRACE"

                        if state["pointer_lost_frames"] > POINTER_LOST_TOLERANCE_FRAMES:
                            reset_pointer_state(state)
                            state["mode"] = MODE_NONE
                            if hand_label != "Right":
                                state["last_command_text"] = "LEFT_HAND_ONLY"
                            else:
                                state["last_command_text"] = "NO_POINTER_POSE"

                    elif state["pan_active"]:
                        state["pan_lost_frames"] += 1
                        state["mode"] = MODE_PAN
                        state["last_command_text"] = "PAN_GRACE"

                        if state["pan_lost_frames"] > PAN_LOST_TOLERANCE_FRAMES:
                            reset_pan_state(state)
                            state["mode"] = MODE_NAV if state["nav_active"] else MODE_NONE
                            state["last_command_text"] = "PAN_STOP"

                    elif state["nav_active"]:
                        state["nav_lost_frames"] += 1
                        state["mode"] = MODE_NAV
                        state["last_command_text"] = "NAV_GRACE"

                        if state["nav_lost_frames"] > NAV_LOST_TOLERANCE_FRAMES:
                            reset_nav_state(state)
                            reset_pan_state(state)
                            state["mode"] = MODE_NONE
                            state["last_command_text"] = "NAV_STOP"

                    else:
                        reset_pointer_state(state)
                        reset_nav_state(state)
                        reset_pan_state(state)
                        state["mode"] = MODE_NONE
                        state["last_command_text"] = "NO_ACTIVE_POSE"

                state["last_index_tip"] = index_tip

            else:
                reset_all_modes(state)

            cv2.imshow("Gesture Test Sandbox", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break

    reset_pan_state(state)
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
