# Hướng Dẫn Dịch Thuật Dự Án (Quy Trình Pipeline với Gemini)

Tài liệu này hướng dẫn cách sử dụng hai kịch bản `export_for_chat.py` và `import_from_chat.py` để dịch nội dung của game Total War: Shogun 2 sang tiếng Việt sử dụng AI (Google Gemini).

Quy trình dịch thuật bao gồm **2 bước chính**:
1. Xuất file `.tsv` ra các tệp văn bản nhỏ (chunk) để copy paste lên Gemini.
2. Nhận kết quả từ Gemini, dán lại vào file và chạy lệnh ghép (import) để tạo file `.tsv` tiếng Việt mới.

---

## ⚙️ BƯỚC 1: XUẤT DỮ LIỆU ĐỂ DÁN VÀO CHAT (Export)

Kịch bản `export_for_chat.py` sẽ đọc các tệp dữ liệu gốc (nằm trong thư mục `text/db/`) và chia nhỏ chúng ra để dán dễ dàng vào khung chat của AI mà không giới hạn ký tự.

### Cách chạy lệnh Export

Mở Terminal / Command Prompt tại thư mục dự án và gõ các lệnh sau theo nhu cầu:

- **Xuất một file cụ thể (VD: `units.loc.tsv`)**:
  ```bash
  python export_for_chat.py units.loc.tsv
  ```
- **Xuất một file cụ thể và thay đổi số dòng mỗi chunk (VD: 150 dòng/chunk)**:
  ```bash
  python export_for_chat.py units.loc.tsv --chunk-size 150
  ```
- **Xuất danh sách các file được ưu tiên cao (Tên unit, công trình, UI, công nghệ...)**:
  ```bash
  python export_for_chat.py --priority
  ```
- **Xuất toàn bộ file (Không khuyến khích do dữ liệu cực kỳ lớn)**:
  ```bash
  python export_for_chat.py
  ```

### Cấu trúc kết quả sau khi Export

Tất cả các file xuất ra sẽ nằm trong thư mục `chat_export/<tên_file>/`. Bộ file bao gồm:

- `system_prompt.txt`: Chứa prompt chuẩn và từ điển thuật ngữ. **Bắt buộc dán phần này lên đầu cửa sổ chat của bạn trước khi đưa data vào**.
- `chunk_001.txt`, `chunk_002.txt`...: Các chunk dữ liệu để bạn dán lần lượt vào khung chat.
- `manifest.json`: Chứa số liệu cần thiết để kịch bản xử lý ở Bước 2 (bạn không cần quan tâm file này).

Đồng thời, hệ thống cũng tự tạo các file placeholder (file rỗng chứa gợi ý mồi) tại thư mục `chat_import/<tên_file>/` để chuẩn bị cho Bước 2.

---

## 🤖 GIAO TIẾP VỚI GEMINI (Chat)

1. Mở cửa sổ chat mới với Gemini.
2. Mở file `chat_export/<tên_file>/system_prompt.txt`. Copy toàn bộ nội dung và **dán vào để dạy Gemini luật dịch thuật**.
3. Mở file `chat_export/<tên_file>/chunk_001.txt`, copy nội dung và gửi cho Gemini.
4. Gemini sẽ trả lại nội dung đã dịch với cấu trúc `[số] bản dịch`.
5. Mở file tương ứng trong `chat_import/<tên_file>/chunk_001.txt`. Paste (dán đè) đoạn nội dung Gemini cung cấp vào file này và Save lại.
6. Lặp lại thao tác 3-5 đối với các `chunk` còn lại.

---

## 📥 BƯỚC 2: NHẬP DỮ LIỆU ĐÃ DỊCH VÀO GÓI TSV (Import)

Sau khi dán toàn bộ kết quả trả về của Gemini vào thư mục `chat_import/<tên_file>`, bạn tiến hành ráp chúng lại thành file tiếng Việt hoàn chỉnh.

### Cách chạy lệnh Import

Mở Terminal / Command Prompt tại thư mục dự án và gõ lệnh sau:

- **Lắp ráp một file (Ví dụ: `units.loc.tsv`)**:
  ```bash
  python import_from_chat.py units.loc.tsv
  ```
- **Lắp ráp nhiều file cùng lúc**:
  ```bash
  python import_from_chat.py units.loc.tsv effects.loc.tsv
  ```
- **Chế độ kiểm tra (Test xem thiếu bao nhiêu dòng, KHÔNG ghi đè)**:
  ```bash
  python import_from_chat.py units.loc.tsv --check
  ```

### Kết quả sau khi Import

Kịch bản sẽ đọc các file `chunk` bạn đã dán, đối chiếu tự động với file gốc và ghi đè nội dung tiếng Việt. Kết quả cuối cùng là một file `.tsv` được lưu trong thư mục:

👉 `text/db_vi/<tên_file>.tsv`

*Lưu ý: Bất kỳ dòng nào không được dịch bởi AI (hoặc bạn quên copy) thì kịch bản sẽ cấu hình để giữ nguyên tiếng Anh gốc của dòng đó không làm hỏng game.*

---

## ⚡ LUỒNG THAO TÁC RÚT GỌN:

1. Chạy xuất file: `python export_for_chat.py {file.tsv}`
2. Copy `system_prompt.txt` ném cho Gemini.
3. Copy từng `chunk_xxx.txt` ném cho Gemini.
4. Lấy kết quả đem dán vào thư mục `chat_import/{file}/chunk_xxx.txt`.
5. Ráp file lại: `python import_from_chat.py {file.tsv}`
6. Thành quả thu được ở `text/db_vi/{file.tsv}`.
