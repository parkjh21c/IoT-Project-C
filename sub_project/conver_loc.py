import csv
import re
import os

# ==========================================
# 1. 설정 (파일 이름 확인 필수)
# ==========================================
CSV_FILENAME = "forecast_points.CSV"
HEADER_FILENAME = "location.h"

# ==========================================
# 2. 로마자 변환 클래스 (제공해주신 코드 활용)
# ==========================================
class SimpleRomanizer:
    def __init__(self):
        self.CHO = ['g', 'kk', 'n', 'd', 'tt', 'r', 'm', 'b', 'pp', 's', 'ss', '', 'j', 'jj', 'ch', 'k', 't', 'p', 'h']
        self.JUNG = ['a', 'ae', 'ya', 'yae', 'eo', 'e', 'yeo', 'ye', 'o', 'wa', 'wae', 'oe', 'yo', 'u', 'wo', 'we', 'wi', 'yu', 'eu', 'ui', 'i']
        self.JONG = ['', 'k', 'kk', 'ks', 'n', 'nj', 'nh', 't', 'l', 'lg', 'lm', 'lb', 'ls', 'lt', 'lp', 'lh', 'm', 'b', 'bs', 's', 'ss', 'ng', 'j', 'ch', 'k', 't', 'p', 'h']

    def romanize(self, text):
        result = []
        for char in text:
            if '가' <= char <= '힣':
                code = ord(char) - 44032
                cho_idx = code // 588
                jung_idx = (code % 588) // 28
                jong_idx = code % 28
                
                cho_char = self.CHO[cho_idx]
                if cho_idx == 11: cho_char = '' # 'ㅇ' 처리
                
                result.append(cho_char + self.JUNG[jung_idx] + self.JONG[jong_idx])
            else:
                result.append(char)
        return "".join(result)

# 주요 행정구역 매핑
CITY_MAP = {
    "서울특별시": "Seoul", "부산광역시": "Busan", "대구광역시": "Daegu",
    "인천광역시": "Incheon", "광주광역시": "Gwangju", "대전광역시": "Daejeon",
    "울산광역시": "Ulsan", "세종특별자치시": "Sejong", "경기도": "Gyeonggi-do",
    "강원특별자치도": "Gangwon-do", "충청북도": "Chungcheongbuk-do",
    "충청남도": "Chungcheongnam-do", "전북특별자치도": "Jeonbuk-do",
    "전라남도": "Jeollanam-do", "경상북도": "Gyeongsangbuk-do",
    "경상남도": "Gyeongsangnam-do", "제주특별자치도": "Jeju-do"
}

def translate_address(korean_addr):
    romanizer = SimpleRomanizer()
    for kr, en in CITY_MAP.items():
        if kr in korean_addr:
            korean_addr = korean_addr.replace(kr, en)
            break
    
    def convert_part(word):
        if re.match(r'^[A-Za-z\-]+$', word): return word
        converted = romanizer.romanize(word)
        suffixes = {'gu': '-gu', 'dong': '-dong', 'eup': '-eup', 'myeon': '-myeon', 'si': '-si', 'gun': '-gun', 'ri': '-ri', 'ga': '-ga', 'ro': '-ro'}
        for k, v in suffixes.items():
            if converted.endswith(k) and len(converted) > len(k):
                if not converted.endswith(v): converted = converted[:-len(k)] + v
                break
        return converted.title()

    parts = korean_addr.split()
    return " ".join([convert_part(part) for part in parts])

def build_full_name(name1, name2, name3):
    parts = []
    if name1: parts.append(name1)
    if name2: parts.append(name2)
    if name3: parts.append(name3)
    return " ".join(parts)

# ==========================================
# 3. CSV 읽기 및 헤더 생성 메인 로직
# ==========================================
def main():
    locations_data = [] 
    locations_name_map = [] 

    print(f"'{CSV_FILENAME}' 파일을 읽고 변환 중...")

    try:
        with open(CSV_FILENAME, mode="r", encoding="cp949") as infile:
            reader = csv.reader(infile)
            try:
                next(reader) # 헤더 스킵
            except StopIteration:
                pass

            # CSV 인덱스 (파일 형식에 맞게 조정됨)
            IDX_NAME1 = 2; IDX_NAME2 = 3; IDX_NAME3 = 4
            IDX_GRID_X = 5; IDX_GRID_Y = 6
            IDX_LON = 13; IDX_LAT = 14

            count = 0
            for row in reader:
                try:
                    if not row[IDX_GRID_X] or not row[IDX_GRID_Y]: continue
                    
                    x = int(row[IDX_GRID_X])
                    y = int(row[IDX_GRID_Y])
                    lon = float(row[IDX_LON]) 
                    lat = float(row[IDX_LAT])

                    # 1. 한글 이름 조합
                    korean_full_name = build_full_name(row[IDX_NAME1], row[IDX_NAME2], row[IDX_NAME3])
                    
                    # 2. 영문 변환 적용!
                    english_name = translate_address(korean_full_name)

                    # 구조체: x, y, lat, lon, EnglishName
                    locations_data.append((x, y, lat, lon, english_name))
                    locations_name_map.append((english_name, x, y))
                    count += 1

                except (ValueError, IndexError):
                    continue

    except FileNotFoundError:
        print(f"오류: '{CSV_FILENAME}' 파일을 찾을 수 없습니다.")
        return

    print(f"변환 완료! 총 {count}개 데이터 처리됨.")

    # 파일 쓰기
    with open(HEADER_FILENAME, "w", encoding="utf-8") as hf:
        hf.write("#ifndef LOCATION_H\n")
        hf.write("#define LOCATION_H\n\n")
        hf.write("#include <pgmspace.h>\n")
        hf.write("#include <stdint.h>\n\n")

        # LocationData (Lat/Lon 포함 + 이름은 영문)
        hf.write("struct LocationData {\n")
        hf.write("    int16_t gridX;\n")
        hf.write("    int16_t gridY;\n")
        hf.write("    double lat;\n")
        hf.write("    double lon;\n")
        hf.write("    const char* name;\n")
        hf.write("};\n\n")

        # LocationName (검색용)
        hf.write("struct LocationName {\n")
        hf.write("    const char* name;\n")
        hf.write("    int16_t gridX;\n")
        hf.write("    int16_t gridY;\n")
        hf.write("};\n\n")

        hf.write(f"const int locationCount = {count};\n\n")

        hf.write("// Grid Coordinates & Lat/Lon Data (English Names)\n")
        hf.write("const LocationData locationList[] PROGMEM = {\n")
        for x, y, lat, lon, name in locations_data:
            hf.write(f'    {{ {x}, {y}, {lat:.6f}, {lon:.6f}, "{name}" }},\n')
        hf.write("};\n\n")

        hf.write("// Name Search Data (English Names)\n")
        hf.write("const LocationName locationNameList[] PROGMEM = {\n")
        for name, x, y in locations_name_map:
            hf.write(f'    {{ "{name}", {x}, {y} }},\n')
        hf.write("};\n\n")

        hf.write("#endif // LOCATION_H\n")

    print(f"'{HEADER_FILENAME}' 생성 완료! (영문 변환 + 위경도 포함)")

if __name__ == "__main__":
    main()