import subprocess

def play_voice(event: str):
    if event=="detecting":
        msg="어드레스를 취해주세요"
    if event == "address":
        msg = "스윙을 시작해주세요"
    elif event == "backswing":
        msg = "백스윙"
    elif event == "end":
        msg = "스윙 끝, 결과를 출력합니다."
    try:
        # 한국어 보이스 'Yuna' 사용 (설치돼 있어야 함)
        subprocess.Popen(["/usr/bin/say", "-v", "Yuna", msg])
    except Exception as e:
        print(f"[WARN] voice output failed: {e}")
