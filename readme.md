# boss_dpm_tracker
- 영상을 입력하면, 아래와 같은 영상의 DPM을 계산 분석해주는 툴이다.
- ![img](src/스크린샷%202025-06-07%20165346.png)

## 0. 사용 방법
- 준비물 : 보스 딜을 측정하고 싶은 영상을 준비한다.
- **첫 장면부터 마지막 장면까지** 보스 hp체력바 및 체력치가 보이도록 하는 영상으로 편집해서 `./video/` 폴더에 옮긴다.
- `main.py` 속의 첫 부분에서  `VIDEO_PATH = 'video/video3.mp4'`의 코드의 `video/~~`경로를 적절한 경로로 바꾼다.
- 2. 실행 부분을 따라 실행한다.
- 4. 결과 파일 분석에 따라 진행한다.
- 딜구간 변경 부분을 잘 보고, 극딜 및 평딜 부분의 `시:분:초`를 기록한다.
- 극딜 및 평딜 부분에서 **'전체' 항목은 반드시** 넣어준다.
- 결과 그래프를 엑셀에서 레이아웃을 가시성 있게 수정한다.

### 안 될 때 튜닝 방법
- 오류 : 영상 프레임을 0 x 0 으로 인식할 때
- main.py의 VIDEO_PATH에 제대로 된 이미지가 있는지 확인한다.

- 오류 : None는 많이 안 뜨는데 오류가 날 경우
- main.py의 tick_max 값은 보스 난이도에 따라 맞춘다.
- 천천히 까지면(6분에 30% 이하의 경우) 1.9로 맞추어야 오류가 안 난다.
- 금방 까지면 4.9

- 오류 : 오인식이 너무 많아 오류가 나는 경우
- debug 폴더를 보면 숫자가 제대로 걸러지는지 확인,
- 왼쪽의 콜론처럼 생긴 것 때문에 문제가 생기면 좌측 한 줄을 자른다. HP_REGION_ORIGINAL의 w 항목(3번째)를 1 줄인다.
- 글씨 두께가 너무 클 경우, 174라인부터 181줄까지 해상도에 맞는 thres 항목을 수정한다.
- 되도록 1920 x 1080 동영상을 가져오는 것이 현명하다.

## 1. 폴더 구조
```
boss_dps_tracker/
├── main.py
├── video/              # 분석할 영상 파일 위치
│   └── boss.mp4
├── venv/               # 가상환경 (아래 스크립트로 생성)
```

## 2. 초기화 및 실행

- 터미널에서 다음을 입력하세요:

```bash
python -m venv venv
source venv/bin/activate  # 윈도우는 venv\Scripts\activate
pip install -r requirements.txt
```
- 또는 `initalize.bat` 실행(윈도우 유저)
- activate가 되질 않을 경우엔, python 버전을 확인하고, 윈도우 venv를 지원하는 python으로 호출하면 된다.
- 윈도우 python3.13이 설치된 경우 문구 python을 python313으로 바꾸어서 호출하면 잘 된다.


## 3. 실행 방법

```bash
# 가상환경 진입하지 않았을 때
call venv\Scripts\activate

# 프로그램 실행
python main.py
```

## 4. 결과 파일 설명
- ![스크린샷](./src/스크린샷%202025-06-07%20165346.png)
- ![스크린샷](./src/스크린샷%202025-06-07%20083740.png)
- 좌측은 데이터 필드이다.
- 우측엔 딜의 각 부분을 시간을 지정해서 대표구간을 설정할 수 있으며, 그 구간별 DPM도 그래프에 표시 된다.

## 5. 기능 설명
- 구조도 입니다.
```
main()
│
├── extract_frames(video_path, interval_sec)
│   └── (cv2.VideoCapture 활용)
│
├── crop_hp_area(frame, region)
│
├── extract_hp_percent(image, t, thres)
│   └── preprocess_hp_image(image, scale, t, thres)
│       └── (cv2.resize, cv2.cvtColor, cv2.threshold 등)
│   └── read_hp_easyocr(image)
│       └── easyocr.Reader.readtext()
│
├── calculate_dps(hp_data)
│
└── save_to_excel(data, filename)
    └── openpyxl.load_workbook()
    └── openpyxl.chart.ScatterChart, Reference, Series
```

### def extract_frames(video_path, interval_sec=1)
- `video_path`에 있는 영상을 `interval_sec`초로 프레임을 쪼개어 프레임의 timestamp와 같이 묶어 `(frames,timestamps)의 배열`을 반환한다.
- global로 정의된 프레임 기준 크기에 비한 비율 변수(X_multi, Y_multi)를 수정한다. (1366x776 이미지가 x,y가 비율 1이다.)
- global로 정의된 HP_REGION(hp 글씨 관심 영역)을 해상도에 맞게 조절한다. 

### def crop_hp_area(frame, region)
- `frame` 비디오 프레임을 받아 `region`의 (x,y,w,h)대로 잘라낸 `부분 영역`을 반환한다.


### def extract_hp_percent(image, t,thres)
- `image` 원본 이미지를 받아 이미지의 hp를 출력한다.
- ,->.  S,s=>5 l => 1 O,o => 0
- 내부적으로 `preprocess_hp_image`, `read_hp_easyocr` 사용.

### def preprocess_hp_image(image, scale=9.0, t=0,thres=0)
- 체력 이미지의 전처리를 맡는 함수.
- `image` 프레임 이미지를 받아 `변환된 이미지`를 출력한다.
- `scale` 만큼 원본 이미지를 키우고(cv2.resize)
- 그레이스케일 데이터로 변환하고(cv2.cvtColor)
- `thres`(0~255)값보다 큰 부분을 흰색, 나머지를 검은색으로 만들며 이진화하며
- ocr 인식을 위해 반전한다.
- `t`(현재 시간)의 10배를 정수화한 시간으로 ocr인식에 사용되는 변환된 이미지를 시간을 붙여 이름으로 저장하고,
 

### def save_to_excel(data, filename="boss_hp_log.xlsx")
- `data` (시간(소수점 첫자리), hp수치(소수점 첫자리)+%)
- 위 배열을 받아서 엑셀 데이터의 A,B열의 2열부터 데이터의 수만큼 데이터를 입력하고,
- XY 그래프(ScatterChart)를 사용하여 기본적인 


### def read_hp_easyocr(image)
- `image` 입력하여 글자를 인식하며
- 결과를 text(as str)로 생성하고, text를 구성하는 문자열이 숫자면 = any(char.isdigit() for char in text) `text`를 반환하고 아니면 `None`을 반환한다.


### def main()
- 영상분석 시작
- `VIDEO_PATH`경로에서, `FRAME_INTERVAL_SEC` 주기로 동영상 프레임을 분화한다.
- `SIZE[0]` 화면폭이 1376, 1364, 1920에 따라 다른 이진 임계값을 적용함. (133, 138, 135, 130)
- 프레임마다 돌며 `crop_hp_area`를 `HP_REGION` 범위로 hp바를 자르고
- `extract_hp_percent`를 자른 이미지를 입력하여 hp를 나타내는 str 타입의 문자열을 추출한다.
- 체력 차이가 일정 수치를 넘거나, 출력 오류가 나면 해당 타임라인은 무시하고, 정상적인 내용은 results에 (시간, 보스 체력%) 쌍으로 배열이 저장된다.
- 만들어진 results 배열을 다시 돌면서, N초(`result_tick`초)가 되기 전의 마지막 boss 체력으로 N초마다의 대표값을 구해서 새로운 배열로 저장한다. (x축의 일정 주기화)
- `boss_hp_log_<파일 이름>.xlsx` 파일에 엑셀을 저장한다.
- 기본 템플릿에 데이터를 추가하고 차트를 기본 설정으로 만든다. 그 외의 계산식은 템플릿에 되어 있다.

## 6. 로그 분석
```
Neither CUDA nor MPS are available - defaulting to CPU. Note: This module is much faster with a GPU.
▶ 영상 분석 시작
영상 해상도: 1920 x 1080
C:\Users\parkg\AppData\Local\Programs\Python\Python313\Lib\site-packages\torch\utils\data\dataloader.py:665: UserWarning: 'pin_memory' argument is set as true but no accelerator is found, then device pinned memory won't be used.
  warnings.warn(warn_msg)
0.0s: 100.0%  <= 지정한 시간(FRAME_INTERVAL_SEC=0.75s) 단위로 이미지를 읽어 boss hp%를 읽는다.
0.7s: 99.9%   <= 이전과 동일한 데이터일 경우는 건너뛰고 출력한다. 즉 체력바 값이 변할때만 인식하며 여기서는 0.3초 데이터를 건너뛰었다.
1.5s: 99.5%
2.2s: 99.1%
2.9s: 98.7%
3.7s: None% Invalid delta = 0%   <= 글씨 인식 오류로 None가 나오고, 이 데이터는 결과에 반영되지 않으며, 통계 데이터 중 fail_count가 1 증가한다.
4.4s: 98.4%
...
58.9s: 53.0%
59.6s: 53.2% Invalid delta = -0.20000000000000284%   <= 글씨를 읽었지만 hp 변화량이 음수이거나 너무 크면(tick_max=4.9%) 실패로 간주한다.
61.1s: 52.0%
...
113.3s: 25.6%
114.1s: 25.0%
114.8s: 24.8%
thres = 135, last% = 24.8, fail_count = 5  <= thres는 화면의 grayscale 임계치로, 값이 높을수록 내부 이미지가 날카로워지거나 소실된다. last%는 마지막 결과값이며, fail_count는 총 실패값 숫자다.
✅ 평균 딜량: 0.68%/sec <= 초당 딜량을 간단 계산한다.
0s: 100.0%  <= 여기부터는 상단의 시간당 원본 데이터를 3초마다의 boss hp%로 변환한다. 각 초를 지나기 전 마지막 시점의 %로 환산한다. (3s 98.7%는 3초 전 마지막 데이터인 2.9초 데이터를 참고함)
3s: 98.7%  <= 3초 주기는 (result_tick = 3.0s)에서 변경할 수 있다.
6s: 98.0%
...
108s: 28.0%
111s: 26.9%
114s: 25.6%
✅ 저장 완료: boss_hp_log_video3.mp4.xlsx <= 3초 주기별 딜량을 엑셀 파일로 저장한다.
```

- 코드 사진
- ![스크린샷](./src/스크린샷%202025-06-07%20165358.png)
- 내부 OCR에 활용되는 이미지
- ![스크린샷](./src/스크린샷%202025-06-07%20165530.png)