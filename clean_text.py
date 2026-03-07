import sys
import os

def clean_file(filepath):
    if not os.path.exists(filepath):
        print(f"Lỗi: Không tìm thấy file '{filepath}'.")
        sys.exit(1)
        
    # Đọc toàn bộ file và giữ lại các dòng chứa ký tự (không rỗng/chỉ chứa khoảng trắng)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    cleaned_lines = [line for line in lines if line.strip()]
    
    # Ghi đè vào chính file input
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
        
    print(f"Đã dọn dẹp {filepath}: Loại bỏ {len(lines) - len(cleaned_lines)} dòng trống.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Cách sử dụng: python clean_text.py <đường_dẫn_tới_file>")
        sys.exit(1)
    
    # Cho phép người dùng nhập nhiều file cùng một lúc
    for arg_path in sys.argv[1:]:
        clean_file(arg_path)
