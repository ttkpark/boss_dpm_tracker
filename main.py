import cv2
import os
import numpy as np
from openpyxl import load_workbook

VIDEO_PATH = 'video/video_light_edit.mp4'
FRAME_INTERVAL_SEC = 0.75  # 프레임 추출 간격
tick_max = 4.9  # 최대 체력 변화량 (%)
result_tick = 3.0  # 결과 출력 간격 (초)
SAVE_DEBUG_IMAGES = True  # 디버그 이미지 저장 여부

# 글로벌 변수
SIZE = (0, 0)
HP_BAR_REGION = None  # 사용자 지정 마젠타 영역으로 고정 설정

def extract_frames(video_path, interval_sec=1):
    """영상에서 프레임을 일정 간격으로 추출"""
    global SIZE
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 영상을 열 수 없습니다: {video_path}")
        return [], []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * interval_sec)
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    SIZE = (width, height)
    print(f"영상 해상도: {width} x {height}")
    print(f"프레임 레이트: {fps:.2f} fps")
    
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
    print(f"총 {len(frames)}개 프레임 추출 완료")
    return frames, timestamps

def detect_hp_bar_region(frame):
    """체력바 영역을 고정 설정 - 사용자 지정 마젠타 영역 기반"""
    global HP_BAR_REGION, SIZE
    
    # 이미 설정된 경우 재사용
    if HP_BAR_REGION is not None:
        return HP_BAR_REGION
    
    height, width = frame.shape[:2]
    
    base_x, base_y, base_w, base_h = 454, 7, 1064, 15
    # 사용자가 마젠타색으로 표시한 정확한 체력바 영역
    # 1920x1080 해상도 기준으로 상단 체력바 위치
    if width == 1920 and height == 1080:
        # 마젠타 박스 안쪽의 실제 보스 체력바 영역
        HP_BAR_REGION = (base_x, base_y, base_w, base_h)  # 마젠타 영역 내부의 실제 체력바
    else:
        # 다른 해상도의 경우 비례 계산
        scale_x = width / 1920
        scale_y = height / 1080
        
        HP_BAR_REGION = (
            int(base_x * scale_x),
            int(base_y * scale_y),
            int(base_w * scale_x),
            int(base_h * scale_y)
        )
    
    print(f"고정 체력바 영역 설정: {HP_BAR_REGION} (가로세로비: {HP_BAR_REGION[2]/HP_BAR_REGION[3]:.1f})")
    return HP_BAR_REGION

def calculate_hp_by_color_ratio(frame, t):
    """색상 비율을 이용한 체력 계산 - 회색 테두리 안의 빨간 체력바 정밀 분석"""
    hp_bar_region = detect_hp_bar_region(frame)
    if hp_bar_region is None:
        return None
    
    x, y, w, h = hp_bar_region
    hp_bar = frame[y:y+h, x:x+w]
    
    # 크기가 너무 작으면 처리 불가
    if hp_bar.shape[0] < 3 or hp_bar.shape[1] < 20:
        return None
    
    # HSV 변환
    hsv_bar = cv2.cvtColor(hp_bar, cv2.COLOR_BGR2HSV)
    
    # 체력바 빨간색 범위 (실제 측정된 색상 기반)
    lower_red1 = np.array([0, 200, 150])
    upper_red1 = np.array([5, 255, 200])
    lower_red2 = np.array([175, 200, 150])
    upper_red2 = np.array([180, 255, 200])
    
    # 빨간색 마스크 생성
    mask1 = cv2.inRange(hsv_bar, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv_bar, lower_red2, upper_red2)
    red_mask = mask1 + mask2
    
    # 회색 테두리/배경 마스크 (체력이 없는 부분)
    lower_gray = np.array([0, 0, 30])
    upper_gray = np.array([180, 50, 150])
    gray_mask = cv2.inRange(hsv_bar, lower_gray, upper_gray)
    
    # 검은색 배경 마스크
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 50])
    black_mask = cv2.inRange(hsv_bar, lower_black, upper_black)
    
    # 체력이 없는 영역 = 회색 + 검은색
    empty_mask = cv2.bitwise_or(gray_mask, black_mask)
    
    # 노이즈 제거
    kernel = np.ones((1, 2), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
    
    # 체력바는 가로 방향으로 채워지므로 가로 분석
    hp_percentage = analyze_precise_hp_ratio(red_mask, empty_mask, hp_bar.shape[1])
    
    # 디버그 이미지 저장
    if SAVE_DEBUG_IMAGES and t < 20:  # 처음 20초만 저장
        save_debug_image(frame, hp_bar_region, hp_bar, red_mask, hp_percentage, t)
    
    return hp_percentage

def analyze_precise_hp_ratio(red_mask, empty_mask, width):
    """회색 테두리 안의 빨간색 비율을 정밀 분석하여 체력 계산"""
    h, w = red_mask.shape
    
    if w == 0 or h == 0:
        return 0.0
    
    # 각 열별로 색상 분석
    red_columns = []
    empty_columns = []
    
    for col in range(w):
        red_pixels = cv2.countNonZero(red_mask[:, col])
        empty_pixels = cv2.countNonZero(empty_mask[:, col])
        
        red_ratio = red_pixels / h if h > 0 else 0
        empty_ratio = empty_pixels / h if h > 0 else 0
        
        red_columns.append(red_ratio)
        empty_columns.append(empty_ratio)
    
    # 체력바의 끝 지점 찾기 (빨간색이 끝나고 회색/검은색이 시작되는 지점)
    hp_end_position = 0
    red_threshold = 0.4  # 40% 이상이 빨간색이면 체력이 있는 것으로 판단
    
    for i in range(w):
        if red_columns[i] >= red_threshold:
            hp_end_position = i + 1
        elif empty_columns[i] > 0.3 and red_columns[i] < 0.1:
            # 빨간색이 거의 없고 회색/검은색이 많으면 체력바 끝
            break
    
    # 전체 빨간색 비율로 검증
    total_red_pixels = cv2.countNonZero(red_mask)
    total_pixels = w * h
    total_red_ratio = total_red_pixels / total_pixels if total_pixels > 0 else 0
    
    # 위치 기반 계산
    position_hp = (hp_end_position / w) * 100 if w > 0 else 0
    
    # 면적 기반 계산  
    area_hp = total_red_ratio * 100
    
    # 두 방법의 평균 (위치 기반에 더 높은 가중치)
    if abs(position_hp - area_hp) < 15:
        hp_percentage = position_hp * 0.7 + area_hp * 0.3
    else:
        # 차이가 크면 더 보수적인 값 선택
        hp_percentage = min(position_hp, area_hp)
    
    # 0~100 범위로 제한
    hp_percentage = max(0, min(100, hp_percentage))
    return round(hp_percentage, 1)

def save_debug_image(frame, hp_bar_region, hp_bar, red_mask, hp_percentage, t):
    """디버그용 이미지 저장"""
    os.makedirs("debug", exist_ok=True)
    
    t_int = int(t * 10)
    
    # 원본 프레임에 체력바 영역 표시
    debug_frame = frame.copy()
    x, y, w, h = hp_bar_region
    cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(debug_frame, f"HP: {hp_percentage}%", (x, y - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # 이미지 저장
    cv2.imwrite(f"debug/{t_int}_0_frame_with_region.png", debug_frame)
    cv2.imwrite(f"debug/{t_int}_1_hp_bar.png", hp_bar)
    cv2.imwrite(f"debug/{t_int}_2_red_mask.png", red_mask)

def save_to_excel(data, filename="boss_hp_log.xlsx"):
    """결과를 엑셀로 저장"""
    try:
        wb = load_workbook("boss_hp_log - template.xlsx")
        ws = wb.active
        
        # 데이터 입력
        for i, (time_val, hp_val) in enumerate(data):
            ws.cell(row=i+2, column=1).value = time_val  # A열: 시간
            ws.cell(row=i+2, column=2).value = hp_val    # B열: 체력
        
        # 차트 생성
        from openpyxl.chart import ScatterChart, Reference, Series
        chart = ScatterChart()
        chart.title = "구간 DPM 분석 (색상 비율 기반)"
        chart.y_axis.title = "딜량(조)"
        chart.x_axis.title = "Time"
        
        # 데이터 범위 설정
        row_count = len(data)
        cats = Reference(ws, min_col=3, min_row=2, max_row=row_count+1)  # C열: Time
        
        data_ref = Reference(ws, min_col=6, min_row=1, max_row=row_count+1)  # F열: DPM
        series = Series(data_ref, cats, title_from_data=True)
        chart.series.append(series)
        
        data_ref = Reference(ws, min_col=7, min_row=1, max_row=row_count+1)  # G열: DPM
        series = Series(data_ref, cats, title_from_data=True)
        chart.series.append(series)
        
        # 차트 추가
        ws.add_chart(chart, "L36")
        wb.save(filename)
        
        print(f"✅ 저장 완료: {filename}")
    except Exception as e:
        print(f"❌ 엑셀 저장 오류: {e}")
        # 간단한 텍스트 파일로 저장
        with open(filename.replace('.xlsx', '.txt'), 'w', encoding='utf-8') as f:
            f.write("시간(초)\t체력(%)\n")
            for time_val, hp_val in data:
                f.write(f"{time_val}\t{hp_val}\n")
        print(f"✅ 텍스트 파일로 저장: {filename.replace('.xlsx', '.txt')}")

def main():
    print("🚀 메이플스토리 보스 DPM 분석기 (색상 비율 기반)")
    print("=" * 50)
    
    # 영상에서 프레임 추출
    frames, timestamps = extract_frames(VIDEO_PATH, FRAME_INTERVAL_SEC)
    
    if not frames:
        print("❌ 프레임을 추출할 수 없습니다.")
        return
    
    results = []  # (시간, 체력%)
    error_total = 0
    last_hp = None
    
    print("\n📊 체력 분석 시작...")
    print("-" * 50)
    
    for frame, t in zip(frames, timestamps):
        hp = calculate_hp_by_color_ratio(frame, t)
        
        if hp is None:
            print(f"{t:6.1f}s: 체력바 탐지 실패")
            error_total += 1
            continue
        
        # 첫 번째 유효한 값 설정
        if last_hp is None:
            last_hp = hp
            print(f"{t:6.1f}s: {hp:5.1f}% (시작)")
            results.append((round(t, 1), f"{hp}%"))
            continue
        
        # 체력 변화량 계산
        delta = last_hp - hp
        
        # 매우 비정상적인 경우만 제외 (기존보다 관대하게)
        if hp > 50 and last_hp < 5:  # 갑자기 체력이 대폭 증가하는 비정상적 경우
            print(f"{t:6.1f}s: {hp:5.1f}% ❌ 비정상적 체력 증가 (delta: {delta:+.1f}%)")
            error_total += 1
            continue
        
        if delta > 20:  # 한 번에 20% 이상 감소는 비정상적
            print(f"{t:6.1f}s: {hp:5.1f}% ❌ 과도한 변화량 (delta: {delta:+.1f}%)")
            error_total += 1
            continue
        
        # 모든 유효한 데이터 포함 (변화량이 작아도 포함)
        if delta > 0:
            print(f"{t:6.1f}s: {hp:5.1f}% ✅ 체력 감소 (delta: -{delta:.1f}%)")
        elif delta < 0:
            print(f"{t:6.1f}s: {hp:5.1f}% 🔄 체력 회복 (delta: +{abs(delta):.1f}%)")
        else:
            print(f"{t:6.1f}s: {hp:5.1f}% ➡️ 동일 체력")
        
        results.append((round(t, 1), f"{hp}%"))
        last_hp = hp
    
    print("-" * 50)
    print(f"📈 분석 완료: 총 {len(results)}개 데이터 포인트")
    print(f"❌ 오류 횟수: {error_total}")
    if last_hp is not None:
        print(f"🎯 최종 체력: {last_hp:.1f}%")
        if results:
            initial_hp = float(results[0][1].replace('%', ''))
            total_damage = initial_hp - last_hp
            total_time = timestamps[-1] if timestamps else 1
            avg_dps = total_damage / total_time
            print(f"⚡ 평균 DPS: {avg_dps:.2f}%/초")
    
    if not results:
        print("❌ 유효한 데이터가 없습니다.")
        return
    
    # 일정 간격으로 데이터 정리
    print(f"\n📋 {result_tick}초 간격으로 데이터 정리 중...")
    interval_results = []
    focus_sec = 0
    
    # 시간순으로 정렬
    results.sort(key=lambda x: x[0])
    
    for entry in results:
        time_sec = entry[0]
        while focus_sec <= time_sec:
            # 해당 시간 구간에서 가장 가까운 데이터 찾기
            closest_entry = min(results, key=lambda x: abs(x[0] - focus_sec))
            interval_results.append((focus_sec, closest_entry[1]))
            print(f"{focus_sec:6.1f}s: {closest_entry[1]}")
            focus_sec += result_tick
            
            if focus_sec > timestamps[-1]:  # 영상 끝을 넘어가면 중단
                break
    
    # 엑셀 저장
    filename = f"boss_hp_log_{VIDEO_PATH.split('/')[-1]}.xlsx"
    save_to_excel(interval_results, filename)
    
    print(f"\n🎉 분석 완료! 결과 파일: {filename}")
    print(f"📊 전체 영상 시간: {timestamps[-1]:.1f}초")
    print(f"📊 데이터 포인트: {len(results)}개")
    print(f"📊 3초 간격 데이터: {len(interval_results)}개")

if __name__ == "__main__":
    main()