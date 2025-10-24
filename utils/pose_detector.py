import numpy as np
from collections import deque

hand_history = deque(maxlen=7)
MIN_CONSISTENT_FRAMES = 5
VIS_THRESH = 0.7

# --- 대상 추적 ---
target_center = None
miss_count = 0
MAX_DIST_THRESHOLD = 0.2
MAX_MISS_FRAMES = 10


def reset_hand_history():
    hand_history.clear()


def detect_hand_raised(result, frame_shape):
    global target_center, miss_count
    h, w, _ = frame_shape

    if not result.pose_landmarks:
        miss_count += 1
        if miss_count > MAX_MISS_FRAMES:
            target_center = None
        hand_history.append(False)
        return sum(hand_history) >= MIN_CONSISTENT_FRAMES

    miss_count = 0
    lm = result.pose_landmarks.landmark
    lw, rw = lm[15], lm[16]
    leye, reye = lm[2], lm[5]
    lhip, rhip = lm[23], lm[24]

    cx, cy = (lhip.x + rhip.x) / 2, (lhip.y + rhip.y) / 2

    if target_center is None:
        target_center = np.array([cx, cy])
    else:
        dist = np.linalg.norm(np.array([cx, cy]) - target_center)
        if dist < MAX_DIST_THRESHOLD:
            target_center = np.array([cx, cy])
        else:
            if miss_count < MAX_MISS_FRAMES:
                pass
            else:
                hand_history.append(False)
                return sum(hand_history) >= MIN_CONSISTENT_FRAMES

    if (lw.visibility > VIS_THRESH and rw.visibility > VIS_THRESH and
        leye.visibility > VIS_THRESH and reye.visibility > VIS_THRESH):

        eye_level = (leye.y + reye.y) / 2
        cond = (lw.y < eye_level or rw.y < eye_level)
        hand_history.append(cond)
    else:
        hand_history.append(False)

    return sum(hand_history) >= MIN_CONSISTENT_FRAMES


def get_pose_landmarks(result, frame_shape):
    global target_center, miss_count
    h, w, _ = frame_shape

    if not result.pose_landmarks:
        miss_count += 1
        if miss_count > MAX_MISS_FRAMES:
            target_center = None
        return None

    miss_count = 0
    lm = result.pose_landmarks.landmark
    lhip, rhip = lm[23], lm[24]
    cx, cy = (lhip.x + rhip.x) / 2, (lhip.y + rhip.y) / 2

    if target_center is None:
        target_center = np.array([cx, cy])
    else:
        dist = np.linalg.norm(np.array([cx, cy]) - target_center)
        if dist > MAX_DIST_THRESHOLD:
            if miss_count < MAX_MISS_FRAMES:
                pass
            else:
                return None
        else:
            target_center = np.array([cx, cy])

    return {
        "left_hip": (lm[23].x * w, lm[23].y * h),
        "right_hip": (lm[24].x * w, lm[24].y * h),
        "left_wrist": (lm[15].x * w, lm[15].y * h),
        "right_wrist": (lm[16].x * w, lm[16].y * h),
        "left_shoulder": (lm[11].x * w, lm[11].y * h),
        "right_shoulder": (lm[12].x * w, lm[12].y * h),
        "left_elbow": (lm[13].x * w, lm[13].y * h),
        "right_elbow": (lm[14].x * w, lm[14].y * h),
    }


def detect_swing_by_pose(lm_dict, swing_state, debug=True):
    lx, ly = lm_dict["left_hip"]
    rx, ry = lm_dict["right_hip"]
    lwx, lwy = lm_dict["left_wrist"]
    rwx, rwy = lm_dict["right_wrist"]
    x_min, x_max = min(lx, rx), max(lx, rx)
    y_avg = (ly + ry) / 2.0

    if debug:
        print(f"[STATE={swing_state}] Hips=({lx:.1f},{rx:.1f}), Wrists=({lwx:.1f},{rwx:.1f})")

    if swing_state == "none":
        cond_y = (lwy > y_avg - 10 and rwy > y_avg - 10)
        cond_x = (x_min - 10 < lwx < x_max + 10 and x_min - 10 < rwx < x_max + 10)
        if cond_y and cond_x:
            return "swing_start", "address"

    if swing_state == "address":
        cond_left = (lwx < x_min - 10 and rwx < x_min - 10)
        cond_right = (lwx > x_max + 10 and rwx > x_max + 10)
        if cond_left:
            return "backswing", "backswing_left"
        elif cond_right:
            return "backswing", "backswing_right"

    if swing_state == "backswing_left":
        if lwx > x_max + 10 and rwx > x_max + 10:
            return "swing_end", "swing_end"

    if swing_state == "backswing_right":
        if lwx < x_min - 10 and rwx < x_min - 10:
            return "swing_end", "swing_end"

    return None, swing_state
