#!/usr/bin/env python3
"""
import_from_chat.py — BƯỚC 2: Nhập kết quả dịch từ Gemini chat vào file TSV

Cách dùng:
    python import_from_chat.py units.loc.tsv
    python import_from_chat.py units.loc.tsv --check   # Kiểm tra không ghi file

Yêu cầu:
    - Đã chạy export_for_chat.py trước
    - Đã dán response từ Gemini vào chat_import/<tên_file>/chunk_XXX.txt

Kết quả:
    text/db_vi/<tên_file>.tsv   ← File TSV tiếng Việt hoàn chỉnh
"""

import json
import re
import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "text" / "db_vi"
EXPORT_DIR = BASE_DIR / "chat_export"
IMPORT_DIR = BASE_DIR / "chat_import"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_numbered_response(response_text: str) -> dict:
    """Parse Gemini response dạng [số] text → dict {row_index: translation}"""
    results = {}
    # Tìm tất cả các dòng bắt đầu bằng [số]
    pattern = re.compile(r'^\[(\d+)\]\s?(.*)', re.MULTILINE)
    matches = list(pattern.finditer(response_text))

    for i, match in enumerate(matches):
        idx = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(response_text)
        # Gom cả nội dung multi-line (nếu có)
        full_text = (match.group(2) + response_text[start:end]).strip()
        results[idx] = full_text

    return results


def write_tsv(filepath: Path, header_lines: list, rows: list):
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        for h in header_lines:
            f.write(h + "\n")
        for row in rows:
            if row.get("empty"):
                f.write("\n")
            else:
                key = row["key"]
                text = row.get("translated_text", row["text"])
                tooltip = row["tooltip"]
                f.write(f"{key}\t{text}\t{tooltip}\n")


def import_file(filename: str, check_only: bool):
    stem = Path(filename).stem  # e.g. "units.loc"
    manifest_path = EXPORT_DIR / stem / "manifest.json"
    import_dir = IMPORT_DIR / stem

    if not manifest_path.exists():
        print(f"❌ Không tìm thấy manifest: {manifest_path}")
        print(f"   Hãy chạy trước: python export_for_chat.py {filename}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    total_chunks = manifest["total_chunks"]
    rows = manifest["rows"]
    header_lines = manifest["header_lines"]
    translatable = manifest["translatable"]

    # Map row_index → item để tra nhanh
    row_map = {item["row_index"]: item for item in translatable}

    print(f"\n📥 Import: {filename}")
    print(f"   Chunks   : {total_chunks}")
    print(f"   Dòng dịch: {len(translatable)}")

    all_translations = {}  # row_index → translated_text
    missing_chunks = []
    incomplete_chunks = []

    for chunk_num in range(1, total_chunks + 1):
        chunk_file = import_dir / f"chunk_{chunk_num:03d}.txt"

        if not chunk_file.exists():
            missing_chunks.append(chunk_num)
            print(f"   ⚠ Chunk {chunk_num:03d}: CHƯA CÓ FILE")
            continue

        content = chunk_file.read_text(encoding="utf-8")

        # Bỏ qua file placeholder (chưa điền)
        if content.strip().startswith("#") or len(content.strip()) < 20:
            missing_chunks.append(chunk_num)
            print(f"   ⚠ Chunk {chunk_num:03d}: CHƯA ĐIỀN RESPONSE (vẫn là placeholder)")
            continue

        parsed = parse_numbered_response(content)

        # Tính xem chunk này cần bao nhiêu dòng
        chunk_size = manifest["chunk_size"]
        start_idx = (chunk_num - 1) * chunk_size
        end_idx = min(start_idx + chunk_size, len(translatable))
        expected_count = end_idx - start_idx
        expected_indices = [translatable[i]["row_index"] for i in range(start_idx, end_idx)]

        found = sum(1 for idx in expected_indices if idx in parsed)
        if found < expected_count:
            incomplete_chunks.append(chunk_num)
            print(f"   ⚠ Chunk {chunk_num:03d}: {found}/{expected_count} dòng (thiếu {expected_count - found})")
        else:
            print(f"   ✓ Chunk {chunk_num:03d}: {found}/{expected_count} dòng OK")

        all_translations.update(parsed)

    # Báo cáo
    total_translated = sum(1 for item in translatable if item["row_index"] in all_translations)
    total_needed = len(translatable)
    print(f"\n   Tổng dịch được: {total_translated}/{total_needed} dòng")

    if missing_chunks:
        print(f"   ❌ Chunk chưa có/chưa điền: {missing_chunks}")

    # Dừng nếu còn thiếu chunk và không phải check mode
    if missing_chunks and not check_only:
        print(f"\n   ⚠ Vẫn sẽ ghi file TSV với {total_translated}/{total_needed} dòng đã dịch.")
        print(f"     Các dòng chưa có sẽ giữ nguyên bản gốc tiếng Anh.")

    if check_only:
        print("\n   [CHECK MODE] Không ghi file.")
        return

    # Ghép lại vào rows
    for item in translatable:
        row_idx = item["row_index"]
        if row_idx in all_translations:
            rows[row_idx]["translated_text"] = all_translations[row_idx]
        # Nếu không có bản dịch → giữ nguyên gốc (đã là mặc định trong write_tsv)

    # Ghi TSV
    output_path = OUTPUT_DIR / filename
    write_tsv(output_path, header_lines, rows)
    print(f"\n   ✅ Đã ghi: {output_path}")
    print(f"      ({total_translated}/{total_needed} dòng đã dịch,"
          f" {total_needed - total_translated} dòng giữ nguyên gốc)")


def main():
    parser = argparse.ArgumentParser(description="Import kết quả dịch từ Gemini chat vào TSV")
    parser.add_argument("files", nargs="+", help="Tên file TSV cần import")
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra, không ghi file")
    args = parser.parse_args()

    for filename in args.files:
        # Cho phép truyền vào cả path lẫn tên file
        filename = Path(filename).name
        import_file(filename, args.check)

    print(f"\n✅ Import hoàn tất! Kết quả tại: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
