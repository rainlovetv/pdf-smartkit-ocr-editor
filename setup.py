#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# PDF SmartKit OCR & Editor - AUTO SETUP INSTALLER
# Tự động cài đặt tất cả thư viện cần thiết
# ============================================================

import os
import sys
import subprocess
import platform
import shutil
import time
from pathlib import Path


class Colors:
    """Mã màu cho terminal output."""
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
    print("=" * 70)
    print("  PDF SmartKit OCR & Editor - AUTO SETUP INSTALLER")
    print("  Hệ thống tự động cài đặt môi trường")
    print("=" * 70)
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
    print("-" * 70)


def get_python_executable():
    """Lấy đường dẫn Python hiện tại."""
    return sys.executable


def check_python_version():
    """Kiểm tra phiên bản Python >= 3.7."""
    print_step(1, "Kiểm tra Phiên bản Python")
    
    version = sys.version_info
    print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"Yêu cầu Python 3.7+, bạn đang dùng {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} OK")
    return True


def check_pip():
    """Kiểm tra pip đã được cài chưa."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        print_success("pip có sẵn")
        return True
    except Exception:
        print_error("pip không được tìm thấy")
        return False


def upgrade_pip():
    """Nâng cấp pip."""
    print_step(2, "Nâng cấp pip")
    print_info("Đang nâng cấp pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                            stdout=subprocess.DEVNULL)
        print_success("pip đã được nâng cấp")
        return True
    except Exception as e:
        print_warning(f"Không thể nâng cấp pip: {e}")
        return False


def check_module_installed(module_name):
    """Kiểm tra xem module Python đã được cài chưa."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def install_python_packages():
    """Cài đặt tất cả thư viện Python cần thiết."""
    print_step(3, "Cài đặt Thư viện Python")
    
    packages = [
        ("customtkinter", "customtkinter>=5.2.2"),
        ("pymupdf", "PyMuPDF>=1.24.0"),
        ("PIL", "Pillow>=10.4.0"),
        ("pytesseract", "pytesseract>=0.3.10"),
    ]
    
    failed = []
    
    for import_name, pip_name in packages:
        if check_module_installed(import_name):
            print_success(f"{pip_name.split('>=')[0]} đã được cài sẵn")
            continue
        
        print_info(f"Đang cài {pip_name}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pip_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print_success(f"{pip_name.split('>=')[0]} cài đặt thành công")
        except Exception as e:
            print_error(f"Lỗi cài {pip_name}: {e}")
            failed.append(pip_name)
    
    return len(failed) == 0, failed


def check_tesseract_installed():
    """Kiểm tra Tesseract OCR đã cài chưa."""
    system = platform.system()
    
    if system == "Windows":
        # Kiểm tra các vị trí phổ biến trên Windows
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return True, path
        return False, None
    
    elif system == "Darwin":  # macOS
        if shutil.which("tesseract"):
            return True, shutil.which("tesseract")
        return False, None
    
    elif system == "Linux":  # Linux
        if shutil.which("tesseract"):
            return True, shutil.which("tesseract")
        return False, None
    
    return False, None


def install_tesseract():
    """Hướng dẫn cài Tesseract OCR."""
    print_step(4, "Cài đặt Tesseract OCR Engine")
    
    is_installed, tesseract_path = check_tesseract_installed()
    
    if is_installed:
        print_success(f"Tesseract đã được cài sẵn tại: {tesseract_path}")
        return True, tesseract_path
    
    system = platform.system()
    print_warning("Tesseract OCR chưa được cài đặt trên hệ thống")
    
    if system == "Windows":
        print_info("Trên Windows, bạn có thể cài Tesseract bằng:")
        print(f"{Colors.YELLOW}")
        print("  1. Tải installer từ:")
        print("     https://github.com/UB-Mannheim/tesseract/wiki")
        print("  2. Hoặc nếu có winget, chạy:")
        print("     winget install --id Tesseract-OCR.Tesseract -e")
        print("  3. Hoặc dùng Chocolatey:")
        print("     choco install tesseract")
        print(f"{Colors.ENDC}")
        
        print_info("Đang cố gắng cài qua winget...")
        try:
            subprocess.check_call(["winget", "install", "--id", "Tesseract-OCR.Tesseract", "-e"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            print_success("Tesseract cài đặt thành công qua winget")
            return True, None
        except Exception:
            print_warning("Không thể cài via winget. Vui lòng cài thủ công từ đường link trên.")
            return False, None
    
    elif system == "Darwin":  # macOS
        print_info("Trên macOS, chạy lệnh:")
        print(f"{Colors.YELLOW}  brew install tesseract{Colors.ENDC}")
        
        if shutil.which("brew"):
            print_info("Đang cài Tesseract qua Homebrew...")
            try:
                subprocess.check_call(["brew", "install", "tesseract"],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
                print_success("Tesseract cài đặt thành công")
                return True, shutil.which("tesseract")
            except Exception as e:
                print_error(f"Lỗi cài Tesseract: {e}")
                return False, None
        else:
            print_warning("Homebrew không được tìm thấy. Vui lòng cài Tesseract thủ công.")
            return False, None
    
    elif system == "Linux":
        distro_msg = ""
        if os.path.exists("/etc/debian_version"):
            distro_msg = "Ubuntu/Debian"
            cmd = "sudo apt-get install -y tesseract-ocr tesseract-ocr-vie"
        elif os.path.exists("/etc/redhat-release"):
            distro_msg = "RedHat/CentOS"
            cmd = "sudo yum install -y tesseract tesseract-langpack-vie"
        else:
            distro_msg = "Linux"
            cmd = "sudo apt-get install -y tesseract-ocr"
        
        print_info(f"Trên {distro_msg}, chạy:")
        print(f"{Colors.YELLOW}  {cmd}{Colors.ENDC}")
        
        print_info("Đang cài Tesseract...")
        try:
            subprocess.check_call(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_success("Tesseract cài đặt thành công")
            return True, shutil.which("tesseract")
        except Exception as e:
            print_warning(f"Cần quyền sudo để cài. Vui lòng cài thủ công: {cmd}")
            return False, None
    
    return False, None


def create_launcher_script():
    """Tạo script khởi chạy (launcher.py) để thực thi app chính."""
    print_step(5, "Tạo Script Khởi Chạy")
    
    launcher_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF SmartKit OCR & Editor - Launcher
Khởi chạy ứng dụng với kiểm tra thư viện tự động
"""

import sys
import subprocess
from pathlib import Path

def main():
    # Kiểm tra xem app.py có tồn tại không
    app_path = Path(__file__).parent / "app.py"
    if not app_path.exists():
        print(f"Lỗi: {app_path} không được tìm thấy!")
        sys.exit(1)
    
    # Chạy app.py
    try:
        subprocess.run([sys.executable, str(app_path)], check=True)
    except KeyboardInterrupt:
        print("\\nỨng dụng đã bị dừng.")
    except Exception as e:
        print(f"Lỗi khi chạy ứng dụng: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    launcher_path = Path(__file__).parent / "launcher.py"
    try:
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_code)
        print_success(f"Tạo launcher.py thành công")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo launcher: {e}")
        return False


def create_run_scripts():
    """Tạo script chạy nhanh (run.bat cho Windows, run.sh cho Unix)."""
    print_step(6, "Tạo Script Chạy Nhanh")
    
    system = platform.system()
    script_dir = Path(__file__).parent
    
    if system == "Windows":
        # Tạo run.bat cho Windows
        bat_content = f'''@echo off
REM PDF SmartKit OCR & Editor - Quick Run Script
cd /d "%~dp0"
"{sys.executable}" launcher.py
pause
'''
        bat_path = script_dir / "run.bat"
        try:
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
            print_success(f"Tạo run.bat thành công - có thể double-click để chạy")
            return True
        except Exception as e:
            print_error(f"Lỗi tạo run.bat: {e}")
            return False
    
    else:  # macOS, Linux
        # Tạo run.sh cho Unix
        sh_content = f'''#!/bin/bash
# PDF SmartKit OCR & Editor - Quick Run Script
cd "$(dirname "$0")"
"{sys.executable}" launcher.py
'''
        sh_path = script_dir / "run.sh"
        try:
            with open(sh_path, "w", encoding="utf-8") as f:
                f.write(sh_content)
            os.chmod(sh_path, 0o755)  # Làm file executable
            print_success(f"Tạo run.sh thành công - có thể chạy ./run.sh")
            return True
        except Exception as e:
            print_error(f"Lỗi tạo run.sh: {e}")
            return False


def create_requirements_file():
    """Tạo requirements.txt để người dùng có thể cài lại nếu cần."""
    print_step(7, "Tạo File requirements.txt")
    
    requirements = """customtkinter>=5.2.2
PyMuPDF>=1.24.0
Pillow>=10.4.0
pytesseract>=0.3.10
"""
    
    req_path = Path(__file__).parent / "requirements.txt"
    try:
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(requirements)
        print_success(f"Tạo requirements.txt thành công")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo requirements.txt: {e}")
        return False


def create_config_file(tesseract_path):
    """Tạo file config.py để lưu cấu hình Tesseract."""
    print_step(8, "Tạo File Cấu Hình")
    
    config_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF SmartKit OCR & Editor - Configuration
Cấu hình tự động được tạo bởi setup.py
"""

import os
import platform

# Tesseract OCR Configuration
TESSERACT_PATH = {repr(tesseract_path)}

# Nếu bạn muốn thay đổi đường dẫn Tesseract, hãy sửa dòng trên
# Windows ví dụ: r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# macOS ví dụ: "/usr/local/bin/tesseract"
# Linux ví dụ: "/usr/bin/tesseract"

# Auto-detect Tesseract nếu chưa cấu hình
if not TESSERACT_PATH or not os.path.exists(str(TESSERACT_PATH) if TESSERACT_PATH else ""):
    import shutil
    detected = shutil.which("tesseract")
    if detected:
        TESSERACT_PATH = detected
    else:
        # Fallback cho Windows
        if platform.system() == "Windows":
            fallback = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            if os.path.exists(fallback):
                TESSERACT_PATH = fallback

# UI Configuration
UI_THEME = "dark"  # "dark" hoặc "light"
UI_COLOR = "blue"  # "blue", "green", "dark-blue"

# OCR Configuration
OCR_LANGUAGES = "vie+eng"  # Ngôn ngữ OCR mặc định
OCR_SCALE = 2  # Tỷ lệ phóng to ảnh trước OCR (1, 2, 3...)

# Debug mode
DEBUG = False
'''
    
    config_path = Path(__file__).parent / "config.py"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_code)
        print_success(f"Tạo config.py thành công")
        return True
    except Exception as e:
        print_error(f"Lỗi tạo config.py: {e}")
        return False


def verify_installation():
    """Kiểm tra lại toàn bộ cài đặt."""
    print_step(9, "Kiểm Tra Lại Cài Đặt")
    
    all_ok = True
    
    # Kiểm tra Python packages
    packages_to_check = [
        ("customtkinter", "CustomTkinter"),
        ("pymupdf", "PyMuPDF"),
        ("PIL", "Pillow"),
        ("pytesseract", "pytesseract"),
    ]
    
    print_info("Kiểm tra thư viện Python:")
    for import_name, display_name in packages_to_check:
        if check_module_installed(import_name):
            print_success(f"  {display_name} OK")
        else:
            print_error(f"  {display_name} CHƯA CÀI")
            all_ok = False
    
    # Kiểm tra Tesseract
    print_info("Kiểm tra Tesseract OCR:")
    is_installed, tesseract_path = check_tesseract_installed()
    if is_installed:
        print_success(f"  Tesseract OK ({tesseract_path})")
    else:
        print_warning(f"  Tesseract CHƯA CÀI (cần cài thủ công)")
        all_ok = False
    
    # Kiểm tra các file cần thiết
    print_info("Kiểm tra các file cần thiết:")
    required_files = ["app.py", "launcher.py", "config.py", "requirements.txt"]
    for fname in required_files:
        fpath = Path(__file__).parent / fname
        if fpath.exists():
            print_success(f"  {fname} OK")
        else:
            print_warning(f"  {fname} KHÔNG TÌM THẤY")
    
    return all_ok


def print_summary(all_ok, tesseract_ok):
    """In tóm tắt kết quả setup."""
    print_step(10, "Tóm Tắt Kết Quả")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}Trạng thái cài đặt:{Colors.ENDC}")
    print_success("Thư viện Python đã được cài đặt") if all_ok else print_error("Một số thư viện chưa được cài")
    print_success("Tesseract OCR đã được cài đặt") if tesseract_ok else print_warning("Tesseract OCR chưa được cài (cần thủ công)")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}Cách chạy ứng dụng:{Colors.ENDC}")
    system = platform.system()
    if system == "Windows":
        print(f"{Colors.YELLOW}  Cách 1: Double-click file run.bat{Colors.ENDC}")
        print(f"{Colors.YELLOW}  Cách 2: Chạy lệnh: python launcher.py{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}  Cách 1: ./run.sh{Colors.ENDC}")
        print(f"{Colors.YELLOW}  Cách 2: python3 launcher.py{Colors.ENDC}")
    
    if not tesseract_ok:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠ LƯU Ý QUAN TRỌNG:{Colors.ENDC}")
        print(f"{Colors.YELLOW}Tesseract OCR chưa được cài đặt. Tính năng OCR sẽ không hoạt động.")
        print(f"Vui lòng cài Tesseract theo hướng dẫn ở trên, sau đó khởi động lại ứng dụng.{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✓ Setup hoàn tất!{Colors.ENDC}\n")


def main():
    """Hàm chính."""
    print_header()
    
    # Bước 1: Kiểm tra Python
    if not check_python_version():
        print_error("Setup thất bại: Python version không phù hợp")
        sys.exit(1)
    
    time.sleep(1)
    
    # Bước 2: Nâng cấp pip
    if not check_pip():
        print_error("pip không được tìm thấy")
        sys.exit(1)
    
    upgrade_pip()
    time.sleep(1)
    
    # Bước 3: Cài Python packages
    packages_ok, failed = install_python_packages()
    time.sleep(1)
    
    # Bước 4: Cài Tesseract
    tesseract_ok, tesseract_path = install_tesseract()
    time.sleep(1)
    
    # Bước 5: Tạo launcher
    create_launcher_script()
    time.sleep(0.5)
    
    # Bước 6: Tạo run scripts
    create_run_scripts()
    time.sleep(0.5)
    
    # Bước 7: Tạo requirements.txt
    create_requirements_file()
    time.sleep(0.5)
    
    # Bước 8: Tạo config
    create_config_file(tesseract_path)
    time.sleep(0.5)
    
    # Bước 9: Kiểm tra lại
    all_ok = verify_installation()
    time.sleep(1)
    
    # Bước 10: In tóm tắt
    print_summary(all_ok, tesseract_ok)
    
    if not packages_ok or not all_ok:
        print_warning("Một số lỗi đã xảy ra. Vui lòng kiểm tra lại trên.")
    
    sys.exit(0 if all_ok and tesseract_ok else 1)


if __name__ == "__main__":
    main()
