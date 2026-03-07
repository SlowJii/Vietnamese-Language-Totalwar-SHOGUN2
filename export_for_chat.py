#!/usr/bin/env python3
"""
export_for_chat.py — BƯỚC 1: Xuất nội dung TSV ra file text để dán vào Gemini chat

Cách dùng:
    python export_for_chat.py units.loc.tsv
    python export_for_chat.py units.loc.tsv --chunk-size 150
    python export_for_chat.py --priority          # Xuất các file ưu tiên cao
    python export_for_chat.py                     # Xuất tất cả (cảnh báo: nhiều!)

Kết quả:
    chat_export/<tên_file>/chunk_001.txt   ← Dán vào Gemini chat
    chat_export/<tên_file>/chunk_002.txt
    chat_export/<tên_file>/manifest.json   ← Dữ liệu nội bộ để import lại
    chat_export/<tên_file>/system_prompt.txt ← Prompt hướng dẫn cho Gemini

Sau khi dịch xong, lưu response của Gemini vào:
    chat_import/<tên_file>/chunk_001.txt
    chat_import/<tên_file>/chunk_002.txt
    ...rồi chạy: python import_from_chat.py units.loc.tsv
"""

import json
import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "text" / "db"
EXPORT_DIR = BASE_DIR / "chat_export"
IMPORT_DIR = BASE_DIR / "chat_import"
GLOSSARY_FILE = BASE_DIR / "translation_glossary.json"

# ─── Danh sách file ưu tiên cao ───────────────────────────────────────────────
PRIORITY_FILES = [
    "units.loc.tsv",
    "unit_description_texts.loc.tsv",
    "ui_component_localisation.loc.tsv",
    "building_description_texts.loc.tsv",
    "technologies.loc.tsv",
    "unit_abilities.loc.tsv",
    "effects.loc.tsv",
    "effect_bundles.loc.tsv",
    "factions.loc.tsv",
    "missions.loc.tsv",
    "dilemmas.loc.tsv",
]

# ─── Phân loại file → system prompt ───────────────────────────────────────────
FILE_CATEGORIES = {
    "unit_names": [
        "units.loc.tsv", "unit_class.loc.tsv", "unit_castes.loc.tsv",
        "unit_category.loc.tsv", "unit_regiment_names_localisation_lookup.loc.tsv",
        "commodity_unit_names.loc.tsv",
    ],
    "unit_descriptions": [
        "unit_description_texts.loc.tsv", "unit_abilities.loc.tsv",
        "unit_info_card_abilities_strings.loc.tsv",
        "avatar_unit_info_card_abilites_strings.loc.tsv",
        "abilities.loc.tsv", "ui_unit_stats.loc.tsv",
    ],
    "building": [
        "building_description_texts.loc.tsv", "building_chains.loc.tsv",
        "building_culture_variants.loc.tsv", "building_faction_variants.loc.tsv",
        "building_culture_gov_type_variants.loc.tsv",
        "battlefield_building_categories.loc.tsv",
        "battlefield_buildings.loc.tsv", "battlefield_buildings_names.loc.tsv",
    ],
    "technology": ["technologies.loc.tsv", "technology_categories.loc.tsv"],
    "encyclopedia": [
        "encyclopedia_blocks.loc.tsv", "encyclopedia_pages.loc.tsv",
        "encyclopedia_template_strings.loc.tsv",
        "encyclopedia_tutorial_videos.loc.tsv",
        "encyclopedia_tutorial_video_game_areas.loc.tsv",
        "encyclopedia_tutorial_video_section_titles.loc.tsv",
        "encyclopedia_tutorial_video_subtitle_texts.loc.tsv",
    ],
    "dialogue": [
        "dilemmas.loc.tsv", "incidents.loc.tsv", "missions.loc.tsv",
        "pre_battle_speeches.loc.tsv", "movie_event_strings.loc.tsv",
        "aide_de_camp_speeches.loc.tsv", "random_localisation_strings.loc.tsv",
        "quotes.loc.tsv", "subtitles.loc.tsv",
        "message_event_strings.loc.tsv", "message_event_text.loc.tsv",
    ],
    "proper_names": [
        "names.loc.tsv", "names_forts.loc.tsv", "names_royalty.loc.tsv",
        "regions.loc.tsv", "regions_sea.loc.tsv",
        "historical_characters.loc.tsv", "ship_names.loc.tsv",
        "campaign_map_settlements.loc.tsv", "campaign_map_towns_and_ports.loc.tsv",
    ],
}

SYSTEM_PROMPTS = {
    "unit_names": """\
Bạn là chuyên gia dịch game chiến thuật lịch sử Nhật Bản sang tiếng Việt.

QUY TẮC DỊCH TÊN ĐƠN VỊ:
1. Các tên đơn vị sẽ gần như được giữ nguyên, ví dụ Yari Samurai hay Yari Ashigaru sẽ được giữ nguyên, chỉ thay đổi các giá trị được liệt kê ở dưới.
2. GIỮ NGUYÊN tên tiếng Nhật: Ashigaru, Samurai, Katana, Naginata, Yari, Nodachi, Kisho, Kachi, Ronin, Dojo...
3. GIỮ NGUYÊN clan & tướng: Takeda, Uesugi, Oda, Hattori, Date, Tokugawa, Shimazu, Mori, Chosokabe, Hojo, Otomo, Imagawa...
4. DỊCH những từ tiếng Anh: Heavy → Hạng nặng, Light → Hạng nhẹ, Elite → Tinh binh...
5. Matchlock Ashigaru → Điểu thương thủ (Ashigaru); Matchlock Samurai → giữ nguyên.
6. Không thêm giải thích dư thừa.
7. Dòng trống → để trống.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích thêm.\
""",
    "unit_descriptions": """\
Bạn là nhà văn lịch sử Việt Nam chuyên về thời Chiến Quốc Nhật Bản (Sengoku Jidai).

QUY TẮC:
1. Dịch HOÀN TOÀN ĐẦY ĐỦ — NGHIÊM CẤM tóm lược, cắt bỏ.
2. Văn phong trang trọng, lịch sử, uyên bác nhưng dễ đọc.
3. GIỮ NGUYÊN tên tiếng Nhật (Ashigaru, Samurai, Naginata, Katana, Yari, Bushido, Daimyo, Shogun...).
4. GIỮ NGUYÊN ký tự đặc biệt: \\n (xuống dòng), || (phân cách tooltip), %S, %d, %i.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích.\
""",
    "building": """\
Bạn là nhà sử học Việt Nam chuyên về lịch sử phong kiến Nhật Bản.

QUY TẮC:
1. Dịch HOÀN TOÀN ĐẦY ĐỦ — không tóm lược.
2. Văn phong trang trọng, gợi không khí phong kiến Nhật Bản.
3. GIỮ NGUYÊN tên riêng (địa danh, nhân vật, Kami, Sengoku Jidai, Bushido, Jodo Shinshu...).
4. GIỮ NGUYÊN: \\n, ||, %S, %d.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích.\
""",
    "technology": """\
Bạn là nhà văn lịch sử quân sự Việt Nam chuyên về Sengoku Jidai và Minh Trị Duy Tân.

QUY TẮC:
1. Dịch HOÀN TOÀN ĐẦY ĐỦ.
2. Văn phong trang trọng, kết hợp lịch sử và kỹ thuật quân sự.
3. GIỮ NGUYÊN tên riêng tiếng Nhật và phương Tây.
4. GIỮ NGUYÊN: \\n, ||, %S, %d.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích.\
""",
    "encyclopedia": """\
Bạn là nhà văn bách khoa sử học Việt Nam chuyên về Nhật Bản thời Chiến Quốc và Minh Trị.

QUY TẮC:
1. Dịch HOÀN TOÀN ĐẦY ĐỦ — không bỏ sót.
2. Văn phong học thuật, súc tích, lôi cuốn.
3. GIỮ NGUYÊN tên riêng tiếng Nhật.
4. GIỮ NGUYÊN ký tự đặc biệt.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích.\
""",
    "dialogue": """\
Bạn là nhà soạn kịch lịch sử Việt Nam chuyên về chiến tranh phong kiến Nhật Bản.

QUY TẮC:
1. Dịch HOÀN TOÀN ĐẦY ĐỦ — không cắt bỏ.
2. Văn phong hào hùng, bi tráng, mang tinh thần Bushido.
3. Bài diễn thuyết trước trận: ngôn ngữ hùng hồn, khích lệ.
4. GIỮ NGUYÊN tên riêng tiếng Nhật.
5. GIỮ NGUYÊN: \\n, ||, %S, %d.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích.\
""",
    "proper_names": """\
Bạn là chuyên gia về tên riêng và địa danh Nhật Bản.

QUY TẮC:
1. Tên người Nhật: GIỮ NGUYÊN (Tokugawa Ieyasu, Oda Nobunaga...).
2. Địa danh Nhật: GIỮ NGUYÊN (Kyoto, Osaka, Edo, Nagato...).
3. Tên biển tiếng Anh mô tả thực: dịch (Inland Sea → Nội hải).
4. Dòng trống → trống.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích.\
""",
    "ui": """\
Bạn là chuyên gia dịch giao diện game (UI/UX) sang tiếng Việt.

QUY TẮC:
1. Dịch ĐẦY ĐỦ VÀ CHÍNH XÁC.
2. Ngôn ngữ rõ ràng, ngắn gọn, dễ hiểu.
3. GIỮ NGUYÊN tên riêng tiếng Nhật.
4. GIỮ NGUYÊN: || (phân cách tooltip), \\n, %S, %d, %i.
5. Dòng chỉ là "xxx" hoặc PLACEHOLDER: giữ nguyên.

OUTPUT: Mỗi dòng = [số] bản dịch. KHÔNG giải thích.\
""",
}


def get_category(filename: str) -> str:
    for cat, files in FILE_CATEGORIES.items():
        if filename in files:
            return cat
    return "ui"


def load_glossary_text() -> str:
    if not GLOSSARY_FILE.exists():
        return ""
    with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
        g = json.load(f)
    lines = ["=== TỪ ĐIỂN THUẬT NGỮ BẮT BUỘC ==="]
    for section, label in [("unit_terms", "Tên đơn vị"), ("title_terms", "Danh hiệu"), ("game_terms", "Thuật ngữ game")]:
        lines.append(f"{label}:")
        for k, v in g.get(section, {}).items():
            if not k.startswith("_"):
                lines.append(f"  {k} → {v}")
    return "\n".join(lines)


def should_translate(text: str) -> bool:
    if not text or not text.strip():
        return False
    s = text.strip()
    if s in ("[PLACEHOLDER]", "PLACEHOLDER", "xxx", "dialogue text", "description", "description "):
        return False
    if s.startswith("PLACEHOLDER") or s.startswith("CINEMATIC UNIT"):
        return False
    if s.isdigit():
        return False
    return True


def parse_tsv(filepath: Path):
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()
    lines = content.splitlines()
    header_lines = []
    rows = []
    for i, line in enumerate(lines):
        if i < 2:
            header_lines.append(line)
            continue
        if not line.strip():
            rows.append({"key": "", "text": "", "tooltip": "", "empty": True})
            continue
        parts = line.split("\t")
        key = parts[0]
        text = parts[1] if len(parts) > 1 else ""
        tooltip = parts[2] if len(parts) > 2 else ""
        rows.append({"key": key, "text": text, "tooltip": tooltip, "empty": False})
    return header_lines, rows


def export_file(filepath: Path, chunk_size: int):
    filename = filepath.name
    stem = filepath.stem  # e.g. "units.loc"
    category = get_category(filename)
    system_prompt = SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS["ui"])
    glossary_text = load_glossary_text()

    out_dir = EXPORT_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)
    import_dir = IMPORT_DIR / stem
    import_dir.mkdir(parents=True, exist_ok=True)

    header_lines, rows = parse_tsv(filepath)

    # Thu thập các dòng cần dịch
    translatable = []
    for i, row in enumerate(rows):
        if not row.get("empty") and should_translate(row["text"]):
            translatable.append({"row_index": i, "text": row["text"]})

    total = len(translatable)
    total_chunks = (total + chunk_size - 1) // chunk_size
    print(f"\n📄 {filename}")
    print(f"   Danh mục  : {category}")
    print(f"   Dòng dịch : {total}")
    print(f"   Chunk size: {chunk_size} → {total_chunks} chunk(s)")
    print(f"   Xuất ra   : {out_dir}")

    # Lưu manifest
    manifest = {
        "filename": filename,
        "category": category,
        "header_lines": header_lines,
        "rows": rows,
        "translatable": translatable,
        "total_chunks": total_chunks,
        "chunk_size": chunk_size,
    }
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Lưu system prompt (để dán vào Gemini trước)
    with open(out_dir / "system_prompt.txt", "w", encoding="utf-8") as f:
        f.write("=== DÁN PHẦN NÀY VÀO ĐẦU CHAT VỚI GEMINI ===\n\n")
        f.write(system_prompt)
        f.write("\n\n")
        f.write(glossary_text)
        f.write("\n\n")
        f.write("QUY TẮC ĐỊNH DẠNG OUTPUT:\n")
        f.write("- Mỗi dòng bắt đầu bằng [số] tương ứng với input\n")
        f.write("- Ví dụ: [1] bản dịch ở đây\n")
        f.write("- KHÔNG bỏ sót dòng nào\n")
        f.write("- KHÔNG thêm chú thích hay giải thích\n")

    # Xuất từng chunk
    for chunk_idx in range(total_chunks):
        chunk_num = chunk_idx + 1
        chunk_items = translatable[chunk_idx * chunk_size:(chunk_idx + 1) * chunk_size]
        chunk_file = out_dir / f"chunk_{chunk_num:03d}.txt"

        lines_out = [
            f"=== CHUNK {chunk_num}/{total_chunks} — {filename} ===",
            f"(Dịch {len(chunk_items)} dòng sau sang tiếng Việt theo quy tắc đã hướng dẫn)\n",
        ]
        for item in chunk_items:
            lines_out.append(f"[{item['row_index']}] {item['text']}")

        with open(chunk_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines_out))

        # Tạo file import placeholder (trống, để người dùng điền vào)
        import_file = import_dir / f"chunk_{chunk_num:03d}.txt"
        if not import_file.exists():
            import_file.write_text(
                f"# Dán response từ Gemini chat vào đây (xóa dòng này)\n"
                f"# File: {filename} — Chunk {chunk_num}/{total_chunks}\n",
                encoding="utf-8"
            )

    print(f"   ✓ Đã tạo {total_chunks} chunk + manifest + system_prompt.txt")
    print(f"   → Bước tiếp theo:")
    print(f"     1. Mở {out_dir / 'system_prompt.txt'} → dán vào Gemini chat")
    print(f"     2. Lần lượt dán từng chunk_XXX.txt → lưu response vào {import_dir}")
    print(f"     3. python import_from_chat.py {filename}")


def main():
    parser = argparse.ArgumentParser(description="Xuất TSV ra file text để dịch qua Gemini chat")
    parser.add_argument("files", nargs="*", help="Tên file cụ thể (để trống = tất cả)")
    parser.add_argument("--priority", action="store_true", help="Chỉ xuất file ưu tiên cao")
    parser.add_argument("--chunk-size", type=int, default=80, help="Số dòng mỗi chunk (mặc định 80)")
    args = parser.parse_args()

    if args.files:
        file_list = [INPUT_DIR / f for f in args.files if (INPUT_DIR / f).exists()]
        for f in args.files:
            if not (INPUT_DIR / f).exists():
                print(f"⚠ Không tìm thấy: {INPUT_DIR / f}")
    elif args.priority:
        file_list = [INPUT_DIR / f for f in PRIORITY_FILES if (INPUT_DIR / f).exists()]
    else:
        file_list = sorted(INPUT_DIR.glob("*.tsv"))

    if not file_list:
        print("❌ Không có file nào để xuất!")
        sys.exit(1)

    print(f"🚀 Xuất {len(file_list)} file TSV cho Gemini chat...")
    print(f"   Chunk size: {args.chunk_size} dòng/chunk")
    print(f"   Export dir: {EXPORT_DIR}")

    for filepath in file_list:
        export_file(filepath, args.chunk_size)

    print(f"\n✅ HOÀN THÀNH!")
    print(f"   Thư mục export: {EXPORT_DIR}")
    print(f"   Thư mục import: {IMPORT_DIR}")
    print(f"\nQuy trình:")
    print(f"  1. Vào thư mục chat_export/<tên_file>/")
    print(f"  2. Dán system_prompt.txt lên đầu Gemini chat")
    print(f"  3. Dán lần lượt chunk_001.txt, chunk_002.txt... và lưu response vào chat_import/")
    print(f"  4. Chạy: python import_from_chat.py <tên_file.tsv>")


if __name__ == "__main__":
    main()
