import socket
import subprocess
import time

class VLCController:
    def __init__(self, host="localhost", port=4212,
                 vlc_path="/Applications/VLC.app/Contents/MacOS/VLC"):
        self.host = host
        self.port = port
        self.proc = subprocess.Popen([
            vlc_path,
            "--intf", "macosx",      # ✅ 화면 출력 필요
            "--extraintf", "rc",     # ✅ RC 제어
            f"--rc-host={host}:{port}",
            # "--fullscreen",
            "--loop",
            "--no-video-title-show"
        ])
        time.sleep(2)  # VLC가 뜨고 안정화될 때까지 대기

    def _send(self, cmd: str):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.send((cmd + "\n").encode())
            s.close()
        except Exception as e:
            print(f"[ERROR] VLC 제어 실패: {e}")

    def play(self, video_path):
        self._send("clear")
        self._send(f"add {video_path}")

    def stop(self):
        self._send("stop")
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
