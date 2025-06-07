# boss_dps_tracker
좋습니다! 아래는 **게임 보스 리플레이 영상에서 체력 정보(%)를 추출하고 시간당 딜량을 계산**하는 전체 Python 스크립트입니다.

---

## ✅ 1. 폴더 구조 추천

```
boss_dps_tracker/
├── main.py
├── video/              # 분석할 영상 파일 위치
│   └── boss.mp4
├── venv/               # 가상환경 (아래 스크립트로 생성)
```

---

## ✅ 2. 가상환경(vEnv) 설정 및 패키지 설치

터미널에서 다음을 입력하세요:

```bash
python -m venv venv
source venv/bin/activate  # 윈도우는 venv\Scripts\activate
pip install opencv-python pytesseract
```

※ **Tesseract-OCR 설치 필수**

* macOS: `brew install tesseract`
* Ubuntu: `sudo apt install tesseract-ocr`
* Windows: [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) 설치 후 경로 지정 필요

---

## ✅ 3. 실행 가능한 Python 코드 (`main.py`)

```python
import cv2
import pytesseract
import os

# Windows 사용자는 tesseract 경로 직접 설정 필요
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

VIDEO_PATH = 'video/boss.mp4'
HP_REGION = (1000, 100, 100, 40)  # (x, y, w, h) → 수정 필요
FRAME_INTERVAL_SEC = 1  # 1초 간격

def extract_frames(video_path, interval_sec=1):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * interval_sec)

    frames, timestamps = [], []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            frames.append(frame)
            timestamps.append(frame_idx / fps)
        frame_idx += 1
    cap.release()
    return frames, timestamps

def crop_hp_area(frame, region):
    x, y, w, h = region
    return frame[y:y+h, x:x+w]

def extract_hp_percent(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    text = pytesseract.image_to_string(thresh, config='--psm 7 -c tessedit_char_whitelist=0123456789.%')
    try:
        hp = float(text.strip().replace('%', ''))
        return hp
    except:
        return None

def calculate_dps(hp_data):
    dps_records = []
    for i in range(1, len(hp_data)):
        t0, hp0 = hp_data[i-1]
        t1, hp1 = hp_data[i]
        if hp1 is not None and hp0 is not None and hp1 < hp0:
            dps = (hp0 - hp1) / (t1 - t0)
            dps_records.append((t1, dps))
    return dps_records

def main():
    print("▶ 영상 분석 시작")
    frames, timestamps = extract_frames(VIDEO_PATH, FRAME_INTERVAL_SEC)
    hp_records = []

    for frame, t in zip(frames, timestamps):
        cropped = crop_hp_area(frame, HP_REGION)
        hp = extract_hp_percent(cropped)
        print(f"{t:.1f}s: {hp}%")
        hp_records.append((t, hp))

    dps_records = calculate_dps(hp_records)
    if dps_records:
        avg_dps = sum(d for _, d in dps_records) / len(dps_records)
        print(f"\n✅ 평균 딜량: {avg_dps:.2f}%/sec")
    else:
        print("⚠️ 딜량 데이터를 추출할 수 없습니다.")

if __name__ == "__main__":
    main()
```

---

## ✅ 실행 방법

```bash
python main.py
```

---

## 📌 사용 전 확인사항

* `HP_REGION = (x, y, w, h)`는 영상의 체력 텍스트 위치에 맞게 조정해야 합니다.
  원본 영상 한 프레임을 OpenCV로 띄워보고 `cv2.imshow()`로 좌표 확인 가능.
* 영상은 `video/boss.mp4`에 넣어야 합니다 (또는 경로 수정).

---

필요하다면:

* 결과를 `matplotlib`로 시각화
* CSV/Excel로 저장
* HP 그래프 곡선 그리기

도 추가로 도와드릴 수 있습니다!


- https://tesseract-ocr.github.io/tessdoc/Installation.html
- tesseract-ocr 설치 완료.



```
thres = 118, last% = 602.0, fail_count = 30 ✅ 평균 딜량: 0.20%/sec
thres = 119, last% = 602.0, fail_count = 29 ✅ 평균 딜량: 0.20%/sec
thres = 120, last% = 602.0, fail_count = 33 ✅ 평균 딜량: 0.20%/sec
thres = 121, last% = 602.0, fail_count = 32 ✅ 평균 딜량: 0.20%/sec
thres = 122, last% = 602.0, fail_count = 28 ✅ 평균 딜량: 0.20%/sec
thres = 123, last% = 602.0, fail_count = 29 ✅ 평균 딜량: 0.19%/sec
thres = 124, last% = 602.0, fail_count = 25 ✅ 평균 딜량: 0.21%/sec
thres = 125, last% = 602.0, fail_count = 18 ✅ 평균 딜량: 0.19%/sec
thres = 126, last% = 602.0, fail_count = 22 ✅ 평균 딜량: 0.18%/sec
thres = 127, last% = 602.0, fail_count = 19 ✅ 평균 딜량: 0.19%/sec
thres = 128, last% = 602.0, fail_count = 21 ✅ 평균 딜량: 0.18%/sec
thres = 129, last% = 602.0, fail_count = 22 ✅ 평균 딜량: 0.19%/sec
thres = 130, last% = 602.0, fail_count = 18 ✅ 평균 딜량: 0.19%/sec
thres = 131, last% = 602.0, fail_count = 23 ✅ 평균 딜량: 0.18%/sec
thres = 132, last% = 602.0, fail_count = 18 ✅ 평균 딜량: 0.19%/sec
thres = 133, last% = 602.0, fail_count = 18 ✅ 평균 딜량: 0.19%/sec
thres = 134, last% = 602.0, fail_count = 24 ✅ 평균 딜량: 0.20%/sec
thres = 135, last% = 602.0, fail_count = 29 ✅ 평균 딜량: 0.22%/sec
thres = 136, last% = 602.0, fail_count = 26 ✅ 평균 딜량: 0.20%/sec
thres = 137, last% = 602.0, fail_count = 31 ✅ 평균 딜량: 0.22%/sec
thres = 138, last% = 602.0, fail_count = 37 ✅ 평균 딜량: 0.20%/sec
thres = 139, last% = 602.0, fail_count = 37 ✅ 평균 딜량: 0.20%/sec

=> 권장 이진화 필터 threshold는 실패 카운트가 18인 125, 130, 132, 133이다.
thres = 125, last% = 602.0, fail_count = 69 ✅ 평균 딜량: 0.28%/sec
thres = 130, last% = 602.0, fail_count = 69 ✅ 평균 딜량: 0.30%/sec
thres = 132, last% = 602.0, fail_count = 84 ✅ 평균 딜량: 0.30%/sec
thres = 133, last% = 602.0, fail_count = 66 ✅ 평균 딜량: 0.28%/sec

4개를 잡아서 1초 필터를 해보았다.
- 130, 125가 좋겠다.
```