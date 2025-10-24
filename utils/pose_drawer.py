import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def draw_skeleton(frame):
    """
    Mediapipe Pose Landmarks를 frame 위에 그림.
    Args:
        frame (numpy.ndarray): BGR 이미지
    Returns:
        frame (numpy.ndarray): skeleton이 그려진 이미지
    """
    img=frame.copy()
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = pose.process(image_rgb)

    if result.pose_landmarks:
        mp_drawing.draw_landmarks(
            img,
            result.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )
    return img
