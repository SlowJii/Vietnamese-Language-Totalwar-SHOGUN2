Dưới đây là bản hướng dẫn chi tiết được đúc kết từ toàn bộ quá trình xử lý sự cố của chúng ta. Bản hướng dẫn này được thiết kế để giúp những người dùng Windows (sử dụng Visual Studio 2022) vượt qua các lỗi mạng hóc búa nhất khi cài đặt môi trường Craft.

---

# Hướng dẫn cài đặt Craft (KDE) trên Windows và Sửa lỗi Mạng (SSL/Treo Tải)

## 1. Nhận diện lỗi

Khi chạy lệnh cài đặt Craft trên Windows, hệ thống thường gọi `curl` hoặc `wget2` để tải các gói phần mềm (packages) từ máy chủ của KDE. Do xung đột bảo mật hoặc vấn đề định tuyến mạng, người dùng thường gặp 2 lỗi chí mạng sau:

* **Lỗi 1 (SSL Handshake):** Console báo đỏ `SEC_E_ILLEGAL_MESSAGE (0x80090326)` và tiến trình văng ra ngoài.
* **Lỗi 2 (Treo mạng/Timeout):** Console bị kẹt ở mức `0 B/s` hàng giờ đồng hồ (thường do `wget2` bị điều hướng sang các server dự phòng bị quá tải).

**Giải pháp cốt lõi:** Bỏ qua hệ thống tải tự động của Craft. Chúng ta sẽ đọc log, tải file thủ công qua trình duyệt, tạo đúng cây thư mục, và thả file vào đó để Craft đi thẳng tới bước giải nén.

## 2. Khởi tạo môi trường (Bước cơ bản)

Trước khi bắt đầu, đảm bảo máy tính đã cài đặt **Microsoft Visual Studio 2022** (hỗ trợ C++).

1. Mở PowerShell (không dùng quyền Admin), tạo xưởng làm việc và chạy lệnh Bootstrap:
```powershell
iex ((new-object net.webclient).DownloadString('https://raw.githubusercontent.com/KDE/craft/master/setup/install_craft.ps1'))

```


2. Khi script hỏi chọn trình biên dịch (Compiler), gõ **`1`** để chọn Visual Studio 2022.
3. Chờ tiến trình chạy cho đến khi gặp lỗi mạng đầu tiên. Từ lúc này, hãy áp dụng chiến thuật "Tải tay" bên dưới.

---

## 3. Cách Fix Bug: Chiến thuật "Tải tay đè Cache"

Dưới đây là các ví dụ điển hình dựa trên những gói phần mềm thường xuyên gây lỗi nhất.

*(**Lưu ý quan trọng cho người dùng mới:** Tên file trên server KDE luôn đính kèm mã thời gian - ví dụ: `...20251126T214805...`. Các link dưới đây là ví dụ minh họa cấu trúc. Bạn **bắt buộc** phải nhìn vào file log thực tế trên máy mình để copy đúng đường dẫn URL mới nhất).*

### Ví dụ 1: Xử lý gói nền móng `7zip-base` (Cần 2 file)

**Bước 1: Tạo thư mục chứa file**
Mở một cửa sổ PowerShell mới và chạy 2 lệnh sau để tạo thư mục:

```powershell
New-Item -ItemType Directory -Force -Path "C:\CraftRoot\download\cache\26.02\windows\cl\msvc2022\x86_64\RelWithDebInfo\dev-utils\7zip-base\"
New-Item -ItemType Directory -Force -Path "C:\CraftRoot\download\archives\dev-utils\7zip-base\"

```

**Bước 2: Tải và copy file**
Dùng trình duyệt tải 2 file sau (lấy link từ log báo lỗi của bạn):

* **File ZIP (Binary):** [7zip-base-25.01-20-20251126T183144-windows-cl-msvc2022-x86_64.zip](https://files.kde.org/craft/Qt6/26.02/windows/cl/msvc2022/x86_64/RelWithDebInfo/dev-utils/7zip-base/7zip-base-25.01-20-20251126T183144-windows-cl-msvc2022-x86_64.zip)
👉 Copy file này vào thư mục: `C:\CraftRoot\download\cache\26.02\windows\cl\msvc2022\x86_64\RelWithDebInfo\dev-utils\7zip-base\`
* **File Source (.tar.xz):** [7z2501-extra.tar.xz](https://files.kde.org/craft/3rdparty/7zip/7z2501-extra.tar.xz)
👉 Copy file này vào thư mục: `C:\CraftRoot\download\archives\dev-utils\7zip-base\`

**Bước 3: Chạy lại lệnh cài đặt**
Sau khi copy xong, quay lại cửa sổ PowerShell đang mở môi trường Craft (có chữ `(craftRoot)`) và gõ lại lệnh:

```powershell
craft -i craft

```

---

### Ví dụ 2: Xử lý gói nặng `llvm` (Nhánh Release)

**Bước 1: Tạo thư mục chứa file**

```powershell
New-Item -ItemType Directory -Force -Path "C:\CraftRoot\download\cache\26.02\windows\cl\msvc2022\x86_64\Release\libs\llvm\"

```

*(Chú ý: Đường dẫn thư mục này nằm trong nhánh `Release` thay vì `RelWithDebInfo`).*

**Bước 2: Tải và copy file**
Dùng trình duyệt tải 1 file duy nhất sau:

* **File 7z (Binary):** [llvm-20.1.7-20-20251126T212527-windows-cl-msvc2022-x86_64.7z](https://files.kde.org/craft/Qt6/26.02/windows/cl/msvc2022/x86_64/Release/libs/llvm/llvm-20.1.7-20-20251126T212527-windows-cl-msvc2022-x86_64.7z)
👉 Copy file này vào thư mục: `C:\CraftRoot\download\cache\26.02\windows\cl\msvc2022\x86_64\Release\libs\llvm\`

**Bước 3: Chạy lại lệnh cài đặt**
Hủy tiến trình cũ bằng `Ctrl + C` và gõ lại lệnh cài đặt bạn đang thực hiện, ví dụ:

```powershell
craft -i kimageformats

```

---

### Ví dụ 3: Xử lý lỗi treo 0 B/s cho gói `libsdl2`

**Bước 1: Tạo thư mục chứa file**

```powershell
New-Item -ItemType Directory -Force -Path "C:\CraftRoot\download\cache\26.02\windows\cl\msvc2022\x86_64\RelWithDebInfo\libs\libsdl2\"

```

**Bước 2: Tải và copy file**
Dùng trình duyệt tải 1 file duy nhất sau:

* **File 7z (Binary):** [libsdl2-2.30.10-20-20251126T214805-windows-cl-msvc2022-x86_64.7z](https://files.kde.org/craft/Qt6/26.02/windows/cl/msvc2022/x86_64/RelWithDebInfo/libs/libsdl2/libsdl2-2.30.10-20-20251126T214805-windows-cl-msvc2022-x86_64.7z)
👉 Copy file này vào thư mục: `C:\CraftRoot\download\cache\26.02\windows\cl\msvc2022\x86_64\RelWithDebInfo\libs\libsdl2\`

**Bước 3: Chạy lại lệnh cài đặt**
Nhấn `Ctrl + C` để ngắt kết nối đang treo, sau đó chạy lại lệnh:

```powershell
craft -i kimageformats

```

---

## 4. Công thức chẩn đoán cho các gói khác

Nếu bạn gặp lỗi ở một gói bất kỳ không có trong danh sách trên, hãy làm theo quy tắc sau:

1. Nhìn vào cửa sổ console, tìm dòng log có chứa chữ `wget2` hoặc `curl` ngay trước khi hệ thống văng lỗi/treo.
2. Dòng log đó sẽ chứa link tải trực tiếp (bắt đầu bằng `https://files.kde.org/...`). Copy link đó để dán vào trình duyệt.
3. Đọc kỹ đường dẫn URL để xác định thư mục cần tạo. Nó thường có cấu trúc: `...\RelWithDebInfo\[tên_nhóm]\[tên_gói]\` hoặc `...\Release\[tên_nhóm]\[tên_gói]\`.
4. Tạo thư mục tương ứng trong `C:\CraftRoot\download\cache\...` (hoặc `download\archives\...` nếu file đuôi là `.tar.xz`).
5. Tải file, ném vào thư mục và chạy lại lệnh.

---
