#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF SmartKit OCR & Editor - Auto Setup for Windows
Tự động cài đặt tất cả dependencies cho Windows
Chạy: python setup.py
"""

import os
import sys
import subprocess
import platform
import shutil
import time
import winreg
from pathlib import Path


class Colors:
    """Mã màu ANSI cho terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    """In tiêu đề setup."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("=" * 80)
    print("  📦 PDF SmartKit OCR & Editor - AUTO SETUP FOR WINDOWS")
    print("  Hệ thống tự động cài đặt môi trường hoàn toàn")
    print("=" * 80)
    print(f"{Colors.ENDC}\n")


def print_success(msg):
    """In thông báo thành công."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg):
    """In thông báo lỗi."""
    print(f"{Colors.RED}✗ {msg}{Colors.ENDC}")


def print_info(msg):
    """In thông báo thông tin."""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")


def print_warning(msg):
    """In cảnh báo."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.ENDC}")


def print_step(step_num, title):
    """In tên bước setup."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[Bước {step_num}] {title}{Colors.ENDC}")
    print("-" * 80)


def pause(message="Nhấn Enter để tiếp tục..."):
    """Tạm dừng và chờ người dùng nhấn Enter."""
    input(f"\n{Colors.YELLOW}{message}{Colors.ENDC}")


def is_windows():
    """Kiểm tra xem hệ thống có phải Windows không."""
    return platform.system() == "Windows"


def get_python_executable():
    """Lấy đường dẫn Python hiện tại."""
    return sys.executable


def check_python_version():
    """Kiểm tra phiên bản Python >= 3.7."""
    print_step(1, "Kiểm tra Phiên bản Python")
    
    version = sys.version_info
    python_path = get_python_executable()
    
    print_info(f"Python: {python_path}")
    print_info(f"Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"Yêu cầu Python 3.7+, bạn đang dùng {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")
    return True


def check_and_upgrade_pip():
    """Kiểm tra và nâng cấp pip."""
    print_step(2, "Kiểm tra và Nâng cấp pip")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print_info(result.stdout.strip())
    except Exception as e:
        print_error(f"Không thể kiểm tra pip: {e}")
        return False
    
    print_info("Đang nâng cấp pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
            timeout=60,
            check=True
        )
        print_success("pip đã được nâng cấp")
        return True
    except subprocess.CalledProcessError:
        print_warning("Không thể nâng cấp pip (không gián đoạn)")
        return True
    except Exception as e:
        print_warning(f"Lỗi nâng cấp pip: {e}")
        return True


def is_module_installed(module_name):
    """Kiểm tra xem module Python đã được cài chưa."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def install_python_packages():
    """Cài đặt tất cả thư viện Python cần thiết cho Windows."""
    print_step(3, "Cài đặt Thư viện Python")
    
    packages = [
        ("customtkinter", "customtkinter>=5.2.2", "CustomTkinter - Giao diện đẹp"),
        ("pymupdf", "PyMuPDF>=1.24.0", "PyMuPDF - Xử lý PDF"),
        ("PIL", "Pillow>=10.4.0", "Pillow - Xử lý ảnh"),
        ("pytesseract", "pytesseract>=0.3.10", "pytesseract - OCR Python wrapper"),
    ]
    
    failed_packages = []
    installed_count = 0
    
    for import_name, pip_name, description in packages:
        print_info(f"Kiểm tra {description}...")
        
        if is_module_installed(import_name):
            print_success(f"  {pip_name.split('>=')[0]} đã được cài sẵn")
            installed_count += 1
            continue
        
        print_warning(f"  {pip_name.split('>=')[0]} chưa được cài, đang cài...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
                timeout=120,
                check=True
            )
            print_success(f"  ✓ {pip_name.split('>=')[0]} cài đặt thành công")
            installed_count += 1
        except subprocess.CalledProcessError as e:
            print_error(f"  ✗ Lỗi cài {pip_name}: {e}")
            failed_packages.append(pip_name)
        except subprocess.TimeoutExpired:
            print_error(f"  ✗ Timeout khi cài {pip_name}")
            failed_packages.append(pip_name)
        except Exception as e:
            print_error(f"  ✗ Lỗi không xác định: {e}")
            failed_packages.append(pip_name)
        
        time.sleep(0.5)
    
    print_info(f"Tóm tắt: {installed_count}/{len(packages)} package cài đặt thành công")
    
    if failed_packages:
        print_warning(f"Các package lỗi: {', '.join(failed_packages)}")
        return False, failed_packages
    
    print_success("Tất cả thư viện Python đã được cài đặt ✓")
    return True, []


def find_tesseract_windows():
    """Tìm Tesseract trên Windows."""
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{username}\AppData\Local\Tesseract-OCR\tesseract.exe",
    ]
    
    # Thay {username} bằng tên người dùng hiện tại
    username = os.getenv("USERNAME", "")
    if username:
        common_paths.append(rf"C:\Users\{username}\AppData\Local\Tesseract-OCR\tesseract.exe")
    
    # Kiểm tra các đường dẫn phổ biến
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Tìm qua Windows Registry
    try:
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\tesseract.exe"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            path, _ = winreg.QueryValueEx(key, "")
            if os.path.exists(path):
                return path
    except Exception:
        pass
    
    return None


def install_tesseract_windows():
    """Cài Tesseract OCR trên Windows."""
    print_step(4, "Cài đặt Tesseract OCR Engine")
    
    tesseract_path = find_tesseract_windows()
    
    if tesseract_path:
        print_success(f"Tesseract đã được cài sẵn tại:\n  {tesseract_path}")
        return True, tesseract_path
    
    print_warning("Tesseract OCR chưa được cài đặt trên hệ thống")
    print_info("Tesseract là engine OCR mạnh mẽ, cần cài riêng ngoài Python")
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}Các cách cài Tesseract OCR trên Windows:{Colors.ENDC}")
    print(f"{Colors.YELLOW}")
    print("  [1] Cách nhanh nhất - Sử dụng Chocolatey (nếu đã cài)")
    print("      Mở PowerShell as Admin và chạy:")
    print("      choco install tesseract")
    print()
    print("  [2] Cách khác - Tải installer trực tiếp")
    print("      https://github.com/UB-Mannheim/tesseract/wiki")
    print("      Tải file: tesseract-ocr-w64-setup-v5.x.x.exe")
    print("      Chạy installer và nhớ đường dẫn cài đặt")
    print()
    print("  [3] Nếu bạn có winget (Windows 10+)")
    print("      winget install --id Tesseract-OCR.Tesseract -e")
    print(f"{Colors.ENDC}")
    
    print_info("Đang cố gắng cài Tesseract tự động qua winget...")
    
    try:
        # Thử cài via winget
        result = subprocess.run(
            ["winget", "install", "--id", "Tesseract-OCR.Tesseract", "-e", "--accept-source-agreements", "--accept-package-agreements"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            print_success("Tesseract đã được cài đặt thành công via winget!")
            # Tìm lại đường dẫn
            time.sleep(2)
            tesseract_path = find_tesseract_windows()
            if tesseract_path:
                return True, tesseract_path
            else:
                print_warning("Không thể tìm thấy đường dẫn Tesseract sau khi cài")
                return False, None
        else:
            print_warning("winget không khả dụng hoặc cài đặt không thành công")
            print_info(result.stderr[:200] if result.stderr else "Không có chi tiết lỗi")
    except FileNotFoundError:
        print_warning("winget không được tìm thấy trên hệ thống")
    except subprocess.TimeoutExpired:
        print_warning("Quá thời gian chờ cài đặt Tesseract")
    except Exception as e:
        print_warning(f"Lỗi khi cài Tesseract: {e}")
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠ HƯỚNG DẪN TIẾP THEO:{Colors.ENDC}")
    print(f"{Colors.YELLOW}")
    print("Tesseract không được cài tự động. Vui lòng thực hiện:")
    print()
    print("1. Tải Tesseract từ:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("2. Chạy installer (mặc định cài vào C:\\Program Files\\Tesseract-OCR)")
    print()
    print("3. Sau khi cài xong, chạy setup.py lại")
    print()
    print("4. Nếu không muốn cài, ứng dụng vẫn chạy được nhưng")
    print("   chức năng OCR sẽ thông báo lỗi.")
    print(f"{Colors.ENDC}")
    
    print_warning("Bạn có muốn tiếp tục mà không cài Tesseract? (y/n)")
    choice = input(f"{Colors.YELLOW}Lựa chọn: {Colors.ENDC}").strip().lower()
    
    if choice in ['y', 'yes', 'có']:
        return False, None
    else:
        print_info("Vui lòng cài Tesseract rồi chạy setup.py lại")
        return False, None


def create_launcher_script():
    """Tạo script launcher để khởi chạy app."""
    print_step(5, "Tạo Script Launcher")
    
    launcher_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF SmartKit OCR & Editor - Launcher
Kiểm tra dependencies trước khi khởi chạy ứng dụng
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Kiểm tra tất cả dependencies."""
    required_modules = [
        ("customtkinter", "CustomTkinter"),
        ("pymupdf", "PyMuPDF"),
        ("PIL", "Pillow"),
        ("pytesseract", "pytesseract"),
    ]
    
    missing = []
    for import_name, display_name in required_modules:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(display_name)
    
    if missing:
        print(f"[LỖI] Thiếu các thư viện: {', '.join(missing)}")
        print("Vui lòng chạy: python setup.py")
        return False
    
    return True

def main():
    # Kiểm tra app.py tồn tại
    app_path = Path(__file__).parent / "app.py"
    if not app_path.exists():
        print(f"[LỖI] {app_path} không được tìm thấy!")
        sys.exit(1)
    
    # Kiểm tra dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Kiểm tra config.py
    config_path = Path(__file__).parent / "config.py"
    if not config_path.exists():
        print("[CẢNH BÁO] config.py không tìm thấy, sử dụng cấu hình mặc định")
    
    # Import và chạy app
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from app import PDFSmartKitApp
        app = PDFSmartKitApp()
        app.mainloop()
    except KeyboardInterrupt:
        print("\\n[INFO] Ứng dụng đã bị dừng bởi người dùng.")
        sys.exit(0)
    except Exception as e:
        print(f"[LỖI] Lỗi khởi chạy ứng dụng: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    launcher_path = Path(__file__).parent / "launcher.py"
    try:
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_code)
        print_success(f"launcher.py tạo thành công")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo launcher.py: {e}")
        return False


def create_run_bat_script():
    """Tạo run.bat để Windows có thể double-click chạy."""
    print_step(6, "Tạo Script Chạy Nhanh (run.bat)")
    
    script_dir = Path(__file__).parent
    python_path = sys.executable
    
    bat_content = f'''@echo off
REM =========================================================
REM PDF SmartKit OCR & Editor - Quick Run Script
REM Double-click file này để chạy ứng dụng
REM =========================================================

chcp 65001 >nul
setlocal enabledelayedexpansion

REM Lấy thư mục hiện tại
cd /d "%~dp0"

REM Kiểm tra Python
"{python_path}" --version >nul 2>&1
if errorlevel 1 (
    echo [LỖI] Không tìm thấy Python!
    echo Vui lòng cài Python 3.7+ trước
    pause
    exit /b 1
)

REM Chạy launcher
echo [INFO] Đang khởi chạy PDF SmartKit OCR & Editor...
echo.
"{python_path}" launcher.py
if errorlevel 1 (
    echo.
    echo [LỖI] Ứng dụng bị lỗi!
    echo Vui lòng chạy: python setup.py
    pause
    exit /b 1
)

exit /b 0
'''
    
    bat_path = script_dir / "run.bat"
    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        print_success(f"run.bat tạo thành công")
        print_info("Bây giờ bạn có thể double-click run.bat để chạy ứng dụng")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo run.bat: {e}")
        return False


def create_config_file(tesseract_path):
    """Tạo file config.py."""
    print_step(7, "Tạo File Cấu Hình (config.py)")
    
    if tesseract_path:
        tesseract_line = f'TESSERACT_PATH = r"{tesseract_path}"'
    else:
        tesseract_line = 'TESSERACT_PATH = None  # Sẽ tìm tự động'
    
    config_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF SmartKit OCR & Editor - Configuration
Tệp cấu hình tự động được tạo bởi setup.py
"""

import os
import platform
from pathlib import Path

# ============================================================
# TESSERACT OCR CONFIGURATION
# ============================================================
{tesseract_line}

# Nếu TESSERACT_PATH là None, sẽ tìm tự động trong PATH
# Nếu không tìm được, chức năng OCR sẽ không hoạt động

# Ví dụ cấu hình tay:
# Windows: TESSERACT_PATH = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# macOS:   TESSERACT_PATH = "/usr/local/bin/tesseract"
# Linux:   TESSERACT_PATH = "/usr/bin/tesseract"

def get_tesseract_path():
    """Lấy đường dẫn Tesseract, tìm tự động nếu cần."""
    if TESSERACT_PATH and os.path.exists(TESSERACT_PATH):
        return TESSERACT_PATH
    
    # Tìm tự động
    import shutil
    found = shutil.which("tesseract")
    if found:
        return found
    
    return None

# ============================================================
# UI CONFIGURATION
# ============================================================
UI_THEME = "dark"  # "dark" hoặc "light"
UI_COLOR_THEME = "blue"  # "blue", "green", "dark-blue"
UI_WIDTH = 1200
UI_HEIGHT = 760
UI_MIN_WIDTH = 980
UI_MIN_HEIGHT = 600

# ============================================================
# OCR CONFIGURATION
# ============================================================
OCR_LANGUAGES = "vie+eng"  # Ngôn ngữ: vie (Tiếng Việt), eng (English)
OCR_SCALE = 2  # Tỷ lệ phóng to ảnh trước OCR (1, 2, 3)
OCR_PSM = 6  # Tesseract PSM mode (0-13)
OCR_OEM = 3  # Tesseract OEM mode (0, 1, 2, 3)

# ============================================================
# FILE & OUTPUT
# ============================================================
DEFAULT_OUTPUT_SUFFIX = "_output"
TEMP_DIR = str(Path(__file__).parent / ".temp")

# ============================================================
# DEBUG & LOGGING
# ============================================================
DEBUG = False
LOG_LEVEL = "INFO"  # "DEBUG", "INFO", "WARNING", "ERROR"
'''
    
    config_path = Path(__file__).parent / "config.py"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_code)
        print_success(f"config.py tạo thành công")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo config.py: {e}")
        return False


def create_requirements_file():
    """Tạo requirements.txt."""
    print_step(8, "Tạo File requirements.txt")
    
    requirements_content = '''customtkinter>=5.2.2
PyMuPDF>=1.24.0
Pillow>=10.4.0
pytesseract>=0.3.10
'''
    
    req_path = Path(__file__).parent / "requirements.txt"
    try:
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(requirements_content)
        print_success(f"requirements.txt tạo thành công")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo requirements.txt: {e}")
        return False


def create_readme_file():
    """Tạo README.md với hướng dẫn."""
    print_step(9, "Tạo File README.md")
    
    readme_content = '''# PDF SmartKit OCR & Editor

Ứng dụng Desktop đa năng xử lý PDF: OCR, chỉnh sửa, tách, gộp, xóa trang.

## ✨ Tính Năng

- **OCR (Nhận diện chữ)**: Chuyển PDF scan thành PDF có thể tìm kiếm hoặc TXT
- **Sửa nội dung PDF**: Tìm & thay thế text, hoặc trích xuất & biên tập nhanh
- **Tách PDF**: Cắt các trang nhất định từ PDF
- **Gộp PDF**: Ghép nhiều file PDF thành 1 file
- **Xóa trang PDF**: Loại bỏ trang không cần thiết

## 🚀 Cài Đặt & Chạy (Windows)

### Cách 1: Tự động cài (Khuyến nghị)

```bash
python setup.py
```

Script này sẽ:
- Kiểm tra Python version
- Cài tất cả thư viện cần thiết
- Kiểm tra & hướng dẫn cài Tesseract OCR
- Tạo file chạy nhanh `run.bat`

Sau khi xong, chỉ cần:
```bash
run.bat
```
hoặc
```bash
python launcher.py
```

### Cách 2: Cài thủ công

Nếu không muốn dùng `setup.py`:

```bash
pip install -r requirements.txt
python launcher.py
```

## 📋 Yêu Cầu Hệ Thống

- **Python**: 3.7+
- **Windows**: Windows 7+ (hỗ trợ tốt nhất trên Windows 10/11)
- **RAM**: 2GB tối thiểu
- **Tesseract OCR**: Để dùng tính năng OCR (cài riêng)

## 🔧 Cài Tesseract OCR (Bắt buộc cho OCR)

### Cách 1: Winget (Windows 10+)
```powershell
winget install --id Tesseract-OCR.Tesseract -e
```

### Cách 2: Chocolatey
```powershell
choco install tesseract
```

### Cách 3: Download installer
Tải từ: https://github.com/UB-Mannheim/tesseract/wiki

Chọn file `tesseract-ocr-w64-setup-v5.x.x.exe` và cài vào đường dẫn mặc định.

### Kiểm tra Tesseract
Sau khi cài, mở PowerShell và chạy:
```powershell
tesseract --version
```

## 📂 Cấu Trúc Project

```
pdf-smartkit-ocr-editor/
├── app.py              # Ứng dụng chính
├── setup.py            # Script cài đặt tự động
├── launcher.py         # Script khởi chạy với kiểm tra
├── config.py           # Cấu hình (tạo tự động)
├── requirements.txt    # Danh sách package Python
├── run.bat             # Shortcut chạy trên Windows (tạo tự động)
├── README.md           # Hướng dẫn này
└── LICENSE             # Giấy phép
```

## 💡 Cách Sử Dụng

### Tab OCR (Nhận diện chữ)
1. Chọn file PDF scan
2. Chọn loại đầu ra: "Searchable PDF" hoặc "TXT"
3. Nhấn "Bắt đầu OCR"
4. File mới sẽ được lưu cùng thư mục với file gốc

### Tab Sửa nội dung
**Cách 1: Tìm & Thay thế**
1. Chọn file PDF
2. Nhập từ cần tìm & từ cần thay thế
3. Nhấn "Thực hiện Find & Replace"

**Cách 2: Trích xuất & Biên tập nhanh**
1. Chọn file PDF
2. Nhập số trang (VD: 1)
3. Nhấn "Trích xuất text"
4. Sửa text trong ô nhập liệu
5. Nhấn "Lưu thành PDF mới"

### Tab Tách PDF
1. Chọn file PDF
2. Nhập khoảng trang (VD: "1-3" hoặc "2,5,7")
3. Nhấn "Tách PDF"

### Tab Gộp PDF
1. Nhấn "Chọn file PDF" để chọn nhiều file
2. Xem danh sách file đã chọn
3. Nhấn "Gộp PDF"
4. Chọn nơi lưu file kết quả

### Tab Xóa trang
1. Chọn file PDF
2. Nhập số trang cần xóa (VD: "2,4,6")
3. Nhấn "Xóa trang"

## 🐛 Khắc Phục Sự Cố

### Lỗi: "ModuleNotFoundError: No module named 'customtkinter'"
```bash
python setup.py
```

### Lỗi: "No module named 'fitz'"
Chạy lại:
```bash
pip install PyMuPDF --upgrade
python setup.py
```

### OCR không hoạt động
- Kiểm tra Tesseract đã cài: `tesseract --version`
- Nếu chưa cài, tải từ: https://github.com/UB-Mannheim/tesseract/wiki

### Giao diện bị lag/đơ
Đây là tính năng thiết kế - tác vụ OCR chạy trên luồng riêng để không làm đơ UI.
Chỉ cần chờ cho đến khi Progress Bar hoàn tất.

## 📝 Ghi Chú

- Ứng dụng hoạt động **offline** - không cần kết nối Internet
- Tất cả file được xử lý **cục bộ** - không gửi lên cloud
- File đầu vào **không bị xóa** - file output được lưu riêng

## 📄 Giấy Phép

MIT License - Xem file LICENSE để chi tiết

## 👨‍💻 Tác Giả

**rainlovetv** - https://github.com/rainlovetv

---

**Hỗ trợ & Báo cáo lỗi:**
Nếu gặp vấn đề, vui lòng tạo Issue trên GitHub.
'''
    
    readme_path = Path(__file__).parent / "README.md"
    try:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print_success(f"README.md tạo thành công")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo README.md: {e}")
        return False


def verify_installation():
    """Kiểm tra lại toàn bộ cài đặt."""
    print_step(10, "Kiểm Tra Lại Cài Đặt")
    
    all_ok = True
    
    # Kiểm tra Python packages
    print_info("Kiểm tra thư viện Python:")
    packages_to_check = [
        ("customtkinter", "CustomTkinter"),
        ("pymupdf", "PyMuPDF"),
        ("PIL", "Pillow"),
        ("pytesseract", "pytesseract"),
    ]
    
    for import_name, display_name in packages_to_check:
        if is_module_installed(import_name):
            print_success(f"  {display_name} ✓")
        else:
            print_error(f"  {display_name} ✗ CHƯA CÀI")
            all_ok = False
    
    # Kiểm tra Tesseract
    print_info("Kiểm tra Tesseract OCR:")
    tesseract_path = find_tesseract_windows()
    if tesseract_path:
        print_success(f"  Tesseract ✓ ({tesseract_path})")
    else:
        print_warning(f"  Tesseract ⚠ CHƯA CÀI")
    
    # Kiểm tra các file tạo ra
    print_info("Kiểm tra các file tạo ra:")
    required_files = ["launcher.py", "config.py", "requirements.txt", "run.bat", "README.md"]
    for fname in required_files:
        fpath = Path(__file__).parent / fname
        if fpath.exists():
            print_success(f"  {fname} ✓")
        else:
            print_warning(f"  {fname} ⚠ KHÔNG TÌM THẤY")
    
    return all_ok


def print_summary(all_ok, tesseract_ok):
    """In tóm tắt kết quả setup."""
    print_step(11, "Tóm Tắt & Hướng Dẫn Tiếp Theo")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══ KẾT QUẢ CÀI ĐẶT ═══{Colors.ENDC}")
    
    if all_ok:
        print_success("✓ Tất cả thư viện Python được cài đặt")
    else:
        print_error("✗ Một số thư viện chưa được cài đặt")
    
    if tesseract_ok:
        print_success("✓ Tesseract OCR được cài đặt")
    else:
        print_warning("⚠ Tesseract OCR chưa được cài đặt (có thể cài sau)")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══ CÁCH CHẠY ỨNG DỤNG ═══{Colors.ENDC}")
    print(f"{Colors.YELLOW}")
    print("  Cách 1 (Khuyến nghị):")
    print("    Double-click file: run.bat")
    print()
    print("  Cách 2: Dùng PowerShell")
    print("    python launcher.py")
    print()
    print("  Cách 3: Chạy trực tiếp")
    print("    python app.py")
    print(f"{Colors.ENDC}")
    
    if not tesseract_ok:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠ LƯU Ý QUAN TRỌNG:{Colors.ENDC}")
        print(f"{Colors.YELLOW}")
        print("Tesseract OCR chưa được cài đặt.")
        print("Ứng dụng vẫn chạy được, nhưng chức năng OCR sẽ không hoạt động.")
        print()
        print("Để cài Tesseract, hãy:")
        print("  1. Mở PowerShell as Administrator")
        print("  2. Chạy: winget install --id Tesseract-OCR.Tesseract -e")
        print("     HOẶC: choco install tesseract")
        print("     HOẶC tải từ: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  3. Chạy lại setup.py để cập nhật cấu hình")
        print(f"{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✓ SETUP HOÀN TẤT!{Colors.ENDC}\n")


def ask_run_app():
    """Hỏi người dùng có muốn chạy app ngay không."""
    print(f"{Colors.BOLD}{Colors.CYAN}Bạn có muốn khởi chạy ứng dụng ngay bây giờ? (y/n){Colors.ENDC}")
    choice = input(f"{Colors.YELLOW}Lựa chọn: {Colors.ENDC}").strip().lower()
    return choice in ['y', 'yes', 'có', 'c']


def run_launcher():
    """Chạy launcher.py để khởi chạy ứng dụng."""
    try:
        launcher_path = Path(__file__).parent / "launcher.py"
        subprocess.run([sys.executable, str(launcher_path)], check=True)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Ứng dụng đã bị dừng.{Colors.ENDC}")
    except Exception as e:
        print_error(f"Lỗi khởi chạy ứng dụng: {e}")


def main():
    """Hàm chính - điều phối toàn bộ setup."""
    
    # Kiểm tra Windows
    if not is_windows():
        print_error("Script này chỉ dành cho Windows!")
        print_info("Vui lòng sử dụng: python setup.py (trên macOS/Linux)")
        sys.exit(1)
    
    print_header()
    
    # Bước 1: Kiểm tra Python
    if not check_python_version():
        print_error("Setup thất bại!")
        sys.exit(1)
    time.sleep(1)
    
    # Bước 2: Nâng cấp pip
    check_and_upgrade_pip()
    time.sleep(1)
    
    # Bước 3: Cài Python packages
    packages_ok, failed = install_python_packages()
    time.sleep(1)
    
    # Bước 4: Cài Tesseract
    tesseract_ok, tesseract_path = install_tesseract_windows()
    time.sleep(1)
    
    # Bước 5-9: Tạo các file hỗ trợ
    create_launcher_script()
    time.sleep(0.5)
    
    create_run_bat_script()
    time.sleep(0.5)
    
    create_config_file(tesseract_path)
    time.sleep(0.5)
    
    create_requirements_file()
    time.sleep(0.5)
    
    create_readme_file()
    time.sleep(1)
    
    # Bước 10: Kiểm tra lại
    all_ok = verify_installation()
    time.sleep(1)
    
    # Bước 11: Tóm tắt
    print_summary(all_ok, tesseract_ok)
    
    # Hỏi chạy app ngay
    if all_ok:
        if ask_run_app():
            print_info("Đang khởi chạy ứng dụng...")
            print()
            run_launcher()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}\nSetup đã bị dừng bởi người dùng.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Lỗi không xác định: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
