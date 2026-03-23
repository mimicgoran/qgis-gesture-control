def create_state():
    return {
        "mode": "NONE",
        "last_command_text": "IDLE",

        "zoom_ready_frames": 0,
        "zoom_active": False,
        "zoom_baseline_distance": None,
        "zoom_previous_distance": None,
        "zoom_current_distance": None,

        "pointer_active": False,
        "pointer_initialized": False,
        "pointer_anchor_hand": None,
        "pointer_preview_x": None,
        "pointer_preview_y": None,
        "smoothed_cursor_x": None,
        "smoothed_cursor_y": None,

        "click_armed": False,
        "click_cooldown": 0,

        "frame_index": 0,
    }