import csv

# 입력 CSV 파일명
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
    locations_xy = []
    locations_name = []

    print(f"'{CSV_FILENAME}' 파일을 읽는 중...")

    with open(CSV_FILENAME, mode="r", encoding="cp949") as infile:
        reader = csv.reader(infile)

        # 헤더 3줄 스킵
        next(reader)
        next(reader)
        next(reader)

        # CSV 컬럼 인덱스
        NAME1 = 2   # 시/도
        NAME2 = 3   # 시/군/구
        NAME3 = 4   # 읍/면/동
        GRID_X = 5
        GRID_Y = 6

        for row in reader:
            try:
                if not row[GRID_X] or not row[GRID_Y]:
                    continue

                x = int(row[GRID_X])
                y = int(row[GRID_Y])

                # 전체 주소 문자열 조합
                full_name = build_full_name(row[NAME1], row[NAME2], row[NAME3])

                # 배열1: XY 기반
                locations_xy.append((x, y, full_name))

                # 배열2: 이름 기반
                locations_name.append((full_name, x, y))

            except:
                continue

    print(f"총 {len(locations_xy)}개의 유효한 위치 데이터를 읽었습니다.")

    # ---------- Header 파일 생성 ----------
    with open(HEADER_FILENAME, "w", encoding="utf-8") as hf:
        hf.write("#ifndef LOCATION_H\n")
        hf.write("#define LOCATION_H\n\n")
        hf.write("#include <pgmspace.h>\n")
        hf.write("#include <stdint.h>\n\n")

        # 구조체 정의
        hf.write("struct LocationXY {\n")
        hf.write("    int16_t gridX;\n")
        hf.write("    int16_t gridY;\n")
        hf.write("    const char* name;\n")
        hf.write("};\n\n")

        hf.write("struct LocationName {\n")
        hf.write("    const char* name;\n")
        hf.write("    int16_t gridX;\n")
        hf.write("    int16_t gridY;\n")
        hf.write("};\n\n")

        hf.write(f"const int locationCount = {len(locations_xy)};\n\n")

        # 배열 1: X,Y → 이름
        hf.write("const LocationXY locationXY[] PROGMEM = {\n")
        for x, y, name in locations_xy:
            hf.write(f'    {{ {x}, {y}, "{name}" }},\n')
        hf.write("};\n\n")

        # 배열 2: 이름 → X,Y
        hf.write("const LocationName locationName[] PROGMEM = {\n")
        for name, x, y in locations_name:
            hf.write(f'    {{ "{name}", {x}, {y} }},\n')
        hf.write("};\n\n")

        hf.write("#endif // LOCATION_H\n")

    print(f"'{HEADER_FILENAME}' 파일 생성 완료!")


if __name__ == "__main__":
    main()
