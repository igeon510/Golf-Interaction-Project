from enum import Enum, auto
import time

class State(Enum):
    IDLE = auto()
    DETECTING = auto()
    RESULT = auto()

class Event(Enum):
    HAND_RAISED = auto()
    SWING_DONE = auto()      # 스윙 종료 시 DETECTING → PROCESSING
    TIMEOUT = auto()

class StateMachine:
    def __init__(self):
        self.state = State.IDLE
        self.start_time = time.time()

    def handle_event(self, event: Event):
        if self.state == State.IDLE:
            if event == Event.HAND_RAISED:
                print("[STATE] Idle → Detecting")
                self.state = State.DETECTING
                self.start_time = time.time()

        elif self.state == State.DETECTING:
            if event == Event.SWING_DONE:
                print("[STATE] Detecting → Processing (스윙 완료)")
                self.state = State.RESULT
                self.start_time = time.time()
            elif event == Event.TIMEOUT:
                self.state = State.IDLE
                self.start_time = None
                from utils.pose_detector import hand_history
                hand_history.clear()  # 히스토리 여기서 초기화, 편함 
        

        elif self.state == State.RESULT:
            if event == Event.TIMEOUT:
                print("[STATE] Result Timeout → Idle")
                self.state = State.IDLE
                self.start_time = None
                from utils.pose_detector import hand_history
                hand_history.clear()  # 히스토리 여기서 초기화, 편함 

    def check_timeout(self, duration):
        """지정된 duration이 지나면 True 반환 (상태는 여기서 바꾸지 않음)"""
        if self.start_time and (time.time() - self.start_time) > duration:
            return True
        return False

