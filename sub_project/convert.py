import csv
import os

# input CSV file name (user)
CSV_FILENAME = 'forecast_points.CSV'
# output header file name (for ESP32)
HEADER_FILENAME = 'locations.h'

# C++ 구조체 정의 (격자 X, Y 좌표만 포함)
struct_definition = """
struct Location {
  int16_t gridX; // 격자 X
  int16_t gridY; // 격자 Y
};
"""

locations_list = []
location_names = [] # 주석으로만 사용할 이름 목록

print(f"'{CSV_FILENAME}' 파일 읽는 중...")

try:
    with open(CSV_FILENAME, mode='r', encoding='cp949') as infile:
        reader = csv.reader(infile)
        
        # 헤더 줄(3줄) 건너뛰기
        next(reader) 
        next(reader)
        next(reader)
        
        # CSV의 격자 X, Y 열 인덱스 (0부터 시작)
        GRID_X_INDEX = 5 # "격자 X"
        GRID_Y_INDEX = 6 # "격자 Y"
        
        # 주소 열 인덱스 (주석용)
        NAME1_INDEX = 2
        NAME2_INDEX = 3
        NAME3_INDEX = 4

        for row in reader:
            try:
                # 격자 X, Y 값이 비어있지 않은지 확인
                if row[GRID_X_INDEX] and row[GRID_Y_INDEX]:
                    gridX = int(row[GRID_X_INDEX])
                    gridY = int(row[GRID_Y_INDEX])
                    
                    # { X 좌표, Y 좌표 } 순서로 저장
                    locations_list.append(f"  {{ {gridX}, {gridY} }}") 
                    
                    # 주석용 이름 조합
                    name1 = row[NAME1_INDEX]
                    name2 = row[NAME2_INDEX]
                    name3 = row[NAME3_INDEX]
                    full_name = " ".join(filter(None, [name1, name2, name3]))
                    location_names.append(f" // {full_name}")

            except (ValueError, IndexError):
                pass # 유효하지 않은 데이터 건너뛰기

    print(f"총 {len(locations_list)}개의 유효한 좌표를 찾았습니다.")

    # C++ 헤더 파일 작성
    with open(HEADER_FILENAME, mode='w', encoding='utf-8') as outfile:
        outfile.write("#ifndef LOCATIONS_H\n")
        outfile.write("#define LOCATIONS_H\n\n")
        
        outfile.write("#include <pgmspace.h>\n")
        outfile.write("#include <stdint.h>\n\n") # int16_t를 사용하기 위해 추가
        
        outfile.write(struct_definition) # gridX, gridY만 있는 구조체 정의
        outfile.write("\n")
        
        # PROGMEM: 이 거대한 배열을 RAM이 아닌 플래시 메모리에 저장
        outfile.write(f"const int locationCount = {len(locations_list)};\n\n")
        outfile.write("const Location locations[locationCount] PROGMEM = {\n")
        
        # 데이터와 주석을 함께 기록
        for data, name in zip(locations_list, location_names):
            outfile.write(f"{data},{name}\n")
            
        outfile.write("};\n\n")
        outfile.write("#endif // LOCATIONS_H\n")

    print(f"'{HEADER_FILENAME}' 파일 생성 완료!")
    print(f"이 파일을 ESP32 프로젝트 폴더(.ino 파일이 있는 곳)로 복사하세요.")

except FileNotFoundError:
    print(f"오류: '{CSV_FILENAME}' 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"오류 발생: {e}")