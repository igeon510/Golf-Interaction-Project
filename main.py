import sys
import time
import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

import mediapipe as mp
from state_machine import StateMachine, Event, State
from utils.pose_detector import detect_hand_raised, get_pose_landmarks, detect_swing_by_pose
from utils.sound import play_voice
from utils.pose_drawer import draw_skeleton
from vlc_controller import VLCController
import os


class GolfWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Golf Interaction (PySide6 UI)")
        # 일시적으로 사이즈, 추후 수정 
        self.setFixedSize(540, 880)

        # ===== 비디오 레이블 =====
        self.label = QLabel(self)
        self.label.resize(self.size())
        self.label.setScaledContents(True)

        # ===== ui_top =====
        self.ui_top = QLabel(self)
        self.ui_top.setAttribute(Qt.WA_TranslucentBackground)
        self.ui_top.setStyleSheet("background: transparent;")

        top_pix = QPixmap("assets/ui_top_IDLE.png")
        if not top_pix.isNull():
            scaled_top = top_pix.scaledToWidth(int(self.width()), Qt.SmoothTransformation)
            self.ui_top.setPixmap(scaled_top)
            self.ui_top.move((self.width() - scaled_top.width()) // 2, 0)
            self.ui_top.raise_()

        # ===== ui_bottom =====
        self.ui_bottom = QLabel(self)
        self.ui_bottom.setAttribute(Qt.WA_TranslucentBackground)
        bottom_pix = QPixmap("assets/ui_bottom_DETECTING.png")
        scaled_bottom = bottom_pix.scaledToWidth(int(self.width() * 0.2), Qt.SmoothTransformation)
        self.ui_bottom.setPixmap(scaled_bottom)
        margin = 0.9
        self.ui_bottom.move((self.width() - scaled_bottom.width())*margin,
                            (self.height() - scaled_bottom.height())*margin)
        self.ui_bottom.raise_()

    def update_window(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888).copy()
        pix = QtGui.QPixmap.fromImage(qimg)
        scaled = pix.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        self.label.repaint()
        self.ui_top.raise_()
        self.ui_bottom.raise_()

    def update_ui_bottom(self, cond: str):
        path = f"assets/ui_bottom_{cond}.png"
        if not os.path.exists(path):
            print(f"[WARN] {path} 없음")
            return
        pix = QPixmap(path).scaledToWidth(int(self.width() * 0.2), Qt.SmoothTransformation)
        margin = 0.9
        self.ui_bottom.setPixmap(pix)
        self.ui_bottom.move((self.width() - pix.width())*margin,
                            (self.height() - pix.height())*margin)
        self.ui_bottom.raise_()

    def update_ui_top(self, cond: str):
        path = f"assets/ui_top_{cond}.png"
        if not os.path.exists(path):
            print(f"[WARN] {path} 없음")
            return
        pix = QPixmap(path).scaledToWidth(int(self.width()), Qt.SmoothTransformation)
        self.ui_top.setPixmap(pix)
        self.ui_top.move((self.width() - pix.width()) // 2, 0)
        self.ui_top.raise_()


def main():
    app = QApplication(sys.argv)
    ui = GolfWindow()

    sm = StateMachine()
    cap = cv2.VideoCapture(0)
    swing_state = "none"
    swing_active = False
    start = True

    # 🔹 Mediapipe Pose 초기화
    mp_pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    # 🔹 VLC Controller 초기화
    vlc = VLCController()
    video_poster = os.path.join("videos", "video_poster.mp4")
    video_algorithm = os.path.join("videos", "video_algorithm.mp4")

    if not cap.isOpened():
        print("웹캠 열 수 없음")

    ui.show()

    def process():
        nonlocal swing_state, swing_active, start

        ret, frame = cap.read()
        if not ret:
            return

        rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        # 🔹 Mediapipe Pose 1회만 처리
        frame_rgb = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
        result = mp_pose.process(frame_rgb)

        # ===== IDLE 상태 =====
        if sm.state == State.IDLE:
            if start:
                vlc.play(video_poster)
                start = False

            skel_frame = draw_skeleton(rotated_frame)
            ui.update_window(skel_frame)

            if detect_hand_raised(result, rotated_frame.shape):
                sm.handle_event(Event.HAND_RAISED)
                play_voice("detecting")
                ui.update_ui_bottom("ADDRESS")
                ui.update_ui_top("ADDRESS")

        # ===== DETECTING 상태 =====
        elif sm.state == State.DETECTING:
            # 30초 지나면 timeout, 30초 안에 어드레스부터 스윙 끝내기.
            if sm.check_timeout(duration=30):
                sm.handle_event(Event.TIMEOUT)
                ui.update_ui_bottom("DETECTING")
                ui.update_ui_top("IDLE")
            skel_frame = draw_skeleton(rotated_frame)
            ui.update_window(skel_frame)

            lm_dict = get_pose_landmarks(result, rotated_frame.shape)
            if lm_dict:
                event, swing_state = detect_swing_by_pose(lm_dict, swing_state)
                if event == "swing_start":
                    play_voice("address")
                    ui.update_ui_bottom("SWING")
                    ui.update_ui_top("SWING")
                    swing_active = True

                elif event == "backswing":
                    play_voice("backswing")

                elif event == "swing_end":
                    play_voice("end")
                    swing_active = False
                    sm.handle_event(Event.SWING_DONE)
                    rn = np.random.randint(1, 7)
                    ui.update_ui_top(f"RESULT_{rn}")
                    ui.update_ui_bottom("RESULT")
                    swing_state = "none"
                    vlc.play(video_algorithm)
                    start = True

        # ===== RESULT 상태 =====
        elif sm.state == State.RESULT:
            ui.update_window(rotated_frame)
            if sm.check_timeout(duration=5):
                print("[INFO] RESULT → IDLE (timeout)")
                sm.handle_event(Event.TIMEOUT)
                ui.update_ui_top("IDLE")
                ui.update_ui_bottom("DETECTING")

    timer = QtCore.QTimer()
    timer.timeout.connect(process)
    timer.start(30)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
