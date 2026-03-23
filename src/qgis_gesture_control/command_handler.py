import pyautogui

pyautogui.FAILSAFE = True


def handle_command(command, state, dx=0, dy=0):
    screen_w, screen_h = pyautogui.size()
    center_x = screen_w // 2
    center_y = screen_h // 2

    safe_margin = 140

    if command == "ZOOM_IN":
        pyautogui.scroll(200)
        state["last_command_text"] = "ZOOM_IN"

    elif command == "ZOOM_OUT":
        pyautogui.scroll(-200)
        state["last_command_text"] = "ZOOM_OUT"

    elif command == "PAN":
        move_x = int(dx * state.get("pan_mouse_scale_x", 2.0))
        move_y = int(dy * state.get("pan_mouse_scale_y", 2.0))

        if not state.get("dragging", False):
            pyautogui.moveTo(center_x, center_y)
            pyautogui.mouseDown(button="left")
            state["dragging"] = True

        if move_x != 0 or move_y != 0:
            pyautogui.moveRel(move_x, move_y, duration=0)

        current_x, current_y = pyautogui.position()

        near_left = current_x < safe_margin
        near_right = current_x > screen_w - safe_margin
        near_top = current_y < safe_margin
        near_bottom = current_y > screen_h - safe_margin

        if near_left or near_right or near_top or near_bottom:
            pyautogui.mouseUp(button="left")
            pyautogui.moveTo(center_x, center_y)
            pyautogui.mouseDown(button="left")

        state["last_command_text"] = f"PAN ({move_x}, {move_y})"

    elif command == "NAV_READY":
        if state.get("dragging", False):
            pyautogui.mouseUp(button="left")
            state["dragging"] = False
        state["last_command_text"] = "NAV_READY"

    elif command == "IDLE":
        if state.get("dragging", False):
            pyautogui.mouseUp(button="left")
            state["dragging"] = False
        state["last_command_text"] = "IDLE"