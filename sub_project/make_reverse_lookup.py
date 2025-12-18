import re
from collections import defaultdict

INPUT_HEADER = "locations.h"
OUTPUT_HEADER = "location_lookup.h"

# ------------------------------------------------------------
# 1. locations.h에서 { X, Y } 형태 좌표 추출
# ------------------------------------------------------------

pattern = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}")

coords = []

with open(INPUT_HEADER, "r", encoding="utf-8") as f:
    for line in f:
        m = pattern.search(line)
        if m:
            x = int(m.group(1))
            y = int(m.group(2))
            coords.append((x, y))

print(f"총 {len(coords)}개 좌표 로드 완료")

# ------------------------------------------------------------
# 2. 같은 좌표끼리 index 목록 묶기
# ------------------------------------------------------------

lookup = defaultdict(list)

for idx, (x, y) in enumerate(coords):
    lookup[(x, y)].append(idx)

print(f"유니크 좌표 개수 = {len(lookup)}")

# ------------------------------------------------------------
# 3. C 헤더 파일 생성
# ------------------------------------------------------------

with open(OUTPUT_HEADER, "w", encoding="utf-8") as out:
    out.write("#ifndef LOCATION_LOOKUP_H\n")
    out.write("#define LOCATION_LOOKUP_H\n\n")
    out.write("#include <stdint.h>\n")
    out.write("#include <pgmspace.h>\n\n")

    out.write("struct LookupItem {\n")
    out.write("  int16_t gridX;\n")
    out.write("  int16_t gridY;\n")
    out.write("  int16_t indices[32]; // 최대 32개까지만 저장하도록 가정\n")
    out.write("  int16_t count;\n")
    out.write("};\n\n")

    out.write(f"const int lookupCount = {len(lookup)};\n")
    out.write("const LookupItem lookupTable[lookupCount] PROGMEM = {\n")

    for (x, y), idx_list in lookup.items():
        idx_str = ", ".join(str(i) for i in idx_list)
        padding = ", " * (32 - len(idx_list))  # 남은 공간 0으로 채울 필요는 없음 (비워도 됨)
        out.write(f"  {{ {x}, {y}, {{ {idx_str} }}, {len(idx_list)} }},\n")

    out.write("};\n\n")
    out.write("#endif // LOCATION_LOOKUP_H\n")

print(f"'{OUTPUT_HEADER}' 생성 완료!")
