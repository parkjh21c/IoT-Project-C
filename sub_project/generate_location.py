import csv

# 입력 CSV 파일명 (사용자가 업로드한 파일명에 맞게 수정 필요)
# 주의: 파일명이 다르다면 이 부분을 실제 파일명으로 수정해주세요.
CSV_FILENAME = "forecast_points.CSV"

# 출력 헤더 파일명
HEADER_FILENAME = "location.h"

def build_full_name(name1, name2, name3):
    """CSV에서 읽어온 시/도, 구, 동 이름을 하나의 문자열로 조합"""
    parts = []
    if name1: parts.append(name1)
    if name2: parts.append(name2)
    if name3: parts.append(name3)
    return " ".join(parts)

def main():
    locations_data = [] # (x, y, lat, lon, name) 정보를 담을 리스트
    locations_name_map = [] # 이름 검색용 (name, x, y) - 기존 호환성 유지

    print(f"'{CSV_FILENAME}' 파일을 읽는 중...")

    try:
        with open(CSV_FILENAME, mode="r", encoding="cp949") as infile:
            reader = csv.reader(infile)

            # --- 헤더 스킵 로직 ---
            # 원본 파일 형태에 따라 스킵 줄 수가 다를 수 있습니다.
            # '단기예보지점좌표...' 파일은 보통 첫 줄이 헤더입니다.
            # 만약 데이터가 읽히지 않는다면 next(reader) 횟수를 조절하세요.
            try:
                header = next(reader) # 첫 번째 줄(컬럼명) 스킵
                # next(reader) # 필요시 추가 스킵
            except StopIteration:
                print("CSV 파일이 비어있거나 형식이 잘못되었습니다.")
                return

            # CSV 컬럼 인덱스 (0부터 시작)
            # 파일: 구분, 행정구역코드, 1단계, 2단계, 3단계, 격자X, 격자Y, ... , 경도(초/100), 위도(초/100)
            # 주의: 제공해주신 스니펫에 따라 경도/위도(소수점)가 13, 14번 인덱스라고 가정합니다.
            IDX_NAME1 = 2   # 시/도
            IDX_NAME2 = 3   # 시/군/구
            IDX_NAME3 = 4   # 읍/면/동
            IDX_GRID_X = 5
            IDX_GRID_Y = 6
            IDX_LON = 13    # 경도 (Longitude) - 보통 126.xxx
            IDX_LAT = 14    # 위도 (Latitude)  - 보통 37.xxx

            count = 0
            for row in reader:
                try:
                    # 필수 데이터가 비어있으면 건너뜀
                    if not row[IDX_GRID_X] or not row[IDX_GRID_Y]:
                        continue
                    
                    # 데이터 파싱
                    x = int(row[IDX_GRID_X])
                    y = int(row[IDX_GRID_Y])
                    
                    # 위도, 경도 읽기 (소수점 포함)
                    # 데이터에 빈 값이 있을 경우를 대비해 예외처리
                    lon = float(row[IDX_LON]) 
                    lat = float(row[IDX_LAT])

                    # 전체 주소 문자열 조합
                    full_name = build_full_name(row[IDX_NAME1], row[IDX_NAME2], row[IDX_NAME3])

                    # 리스트에 추가 (구조체 순서: x, y, lat, lon, name)
                    locations_data.append((x, y, lat, lon, full_name))
                    
                    # 이름 검색용 리스트 (기존 유지)
                    locations_name_map.append((full_name, x, y))
                    
                    count += 1

                except (ValueError, IndexError) as e:
                    # 변환 실패하거나 인덱스 오류가 난 행은 건너뜀
                    continue

    except FileNotFoundError:
        print(f"오류: '{CSV_FILENAME}' 파일을 찾을 수 없습니다.")
        return

    print(f"총 {count}개의 유효한 위치 데이터를 읽었습니다.")

    # ---------- Header 파일 생성 ----------
    with open(HEADER_FILENAME, "w", encoding="utf-8") as hf:
        hf.write("#ifndef LOCATION_H\n")
        hf.write("#define LOCATION_H\n\n")
        hf.write("#include <pgmspace.h>\n")
        hf.write("#include <stdint.h>\n\n")

        # 1. LocationData 구조체 정의 (Lat, Lon 추가됨)
        # MCU 메모리 절약을 위해 gridX, gridY는 int16_t, 위경도는 double 사용
        hf.write("// X, Y 좌표와 실제 위경도, 지명 정보를 담는 구조체\n")
        hf.write("struct LocationData {\n")
        hf.write("    int16_t gridX;\n")
        hf.write("    int16_t gridY;\n")
        hf.write("    double lat;\n")
        hf.write("    double lon;\n")
        hf.write("    const char* name;\n")
        hf.write("};\n\n")

        # 2. LocationName 구조체 정의 (이름 -> X, Y 검색용)
        hf.write("// 지명으로 X, Y를 찾기 위한 구조체\n")
        hf.write("struct LocationName {\n")
        hf.write("    const char* name;\n")
        hf.write("    int16_t gridX;\n")
        hf.write("    int16_t gridY;\n")
        hf.write("};\n\n")

        hf.write(f"const int locationCount = {count};\n\n")

        # 배열 1: LocationData (모든 데이터 포함)
        hf.write("// 격자 좌표 및 위경도 데이터 (GPS -> 주소 변환용)\n")
        hf.write("const LocationData locationList[] PROGMEM = {\n")
        for x, y, lat, lon, name in locations_data:
            # C 언어 구문에 맞게 포맷팅
            hf.write(f'    {{ {x}, {y}, {lat:.6f}, {lon:.6f}, "{name}" }},\n')
        hf.write("};\n\n")

        # 배열 2: LocationName (이름 -> 좌표 변환용, 필요 없다면 제거 가능)
        hf.write("// 지명 검색 데이터 (주소 -> 격자 변환용)\n")
        hf.write("const LocationName locationNameList[] PROGMEM = {\n")
        for name, x, y in locations_name_map:
            hf.write(f'    {{ "{name}", {x}, {y} }},\n')
        hf.write("};\n\n")

        hf.write("#endif // LOCATION_H\n")

    print(f"'{HEADER_FILENAME}' 파일 생성 완료!")

if __name__ == "__main__":
    main()