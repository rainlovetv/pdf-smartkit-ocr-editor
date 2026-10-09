#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF SmartKit OCR & Editor
Ứng dụng Desktop xử lý PDF: OCR, chỉnh sửa, tách, gộp, xóa trang
Giao diện: CustomTkinter (Modern & Responsive)
"""

import os
import sys
import re
import threading
import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# ============================================================
# CẤU HÌNH TESSERACT (tự động tìm hoặc dùng config.py)
# ============================================================
try:
    from config import get_tesseract_path
    TESSERACT_PATH = get_tesseract_path()
except Exception:
    TESSERACT_PATH = None

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ============================================================
# HÀM HỖ TRỢ CHUNG
# ============================================================

def get_output_path(input_pdf_path: str, suffix: str) -> str:
    """Tạo đường dẫn file đầu ra dựa trên input file."""
    base = Path(input_pdf_path)
    return str(base.with_name(f"{base.stem}{suffix}{base.suffix}"))


def parse_page_list(raw_text: str):
    """
    Chuyển chuỗi trang ví dụ: '1-3', '5,7,9', '1-3,5,7-9'
    thành danh sách số trang 1-based.
    """
    if raw_text is None or raw_text.strip() == "":
        raise ValueError("Vui lòng nhập danh sách trang hợp lệ.")

    result = []
    for part in raw_text.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            if part.count("-") > 1:
                raise ValueError(f"Danh sách trang không hợp lệ: {part}")
            start_str, end_str = part.split("-", 1)
            if not start_str or not end_str:
                raise ValueError(f"Danh sách trang không hợp lệ: {part}")
            start = int(start_str)
            end = int(end_str)
            if start > end:
                start, end = end, start
            for i in range(start, end + 1):
                result.append(i)
        else:
            result.append(int(part))
    
    if not result:
        raise ValueError("Không có trang hợp lệ nào được chọn.")
    return sorted(set(result))


def ocr_page_to_text(image: Image.Image, lang: str = "vie+eng") -> str:
    """OCR 1 trang ảnh bằng pytesseract."""
    config = "--psm 6 --oem 3"
    return pytesseract.image_to_string(image, lang=lang, config=config)


def ocr_pdf_to_searchable_pdf(input_pdf_path: str, output_pdf_path: str):
    """OCR PDF scan sang PDF có thể tìm kiếm."""
    doc = fitz.open(input_pdf_path)
    out_pdf = fitz.open()
    total_pages = len(doc)

    for idx in range(total_pages):
        page = doc[idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        try:
            ocr_pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf")
            if ocr_pdf_bytes:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(ocr_pdf_bytes)
                    tmp_path = tmp.name
                tmp_doc = fitz.open(tmp_path)
                if tmp_doc.page_count > 0:
                    out_pdf.insert_pdf(tmp_doc, from_page=0, to_page=tmp_doc.page_count - 1)
                tmp_doc.close()
                os.unlink(tmp_path)
            else:
                raise ValueError("OCR PDF không tạo được")
        except Exception:
            # Fallback: thêm ảnh gốc nếu OCR thất bại
            temp_img_pdf = fitz.open()
            page_img = temp_img_pdf.new_page()
            rect = fitz.Rect(0, 0, pix.width, pix.height)
            page_img.insert_image(rect, stream=pix.tobytes("png"))
            if temp_img_pdf.page_count > 0:
                out_pdf.insert_pdf(temp_img_pdf, from_page=0, to_page=temp_img_pdf.page_count - 1)
            temp_img_pdf.close()

    out_pdf.save(output_pdf_path)
    out_pdf.close()
    doc.close()


def ocr_pdf_to_txt(input_pdf_path: str, output_txt_path: str):
    """OCR PDF scan sang file .txt."""
    doc = fitz.open(input_pdf_path)
    full_text_lines = []
    total_pages = len(doc)

    for idx in range(total_pages):
        page = doc[idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = ocr_page_to_text(img, lang="vie+eng")
        full_text_lines.append(f"--- PAGE {idx + 1} ---\n{text.strip()}\n")

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(full_text_lines))

    doc.close()


def replace_text_in_pdf(input_pdf_path: str, output_pdf_path: str, old_text: str, new_text: str):
    """Thay thế văn bản cũ bằng văn bản mới trong file PDF."""
    if not old_text or not old_text.strip():
        raise ValueError("Từ khóa cần tìm không được để trống.")

    doc = fitz.open(input_pdf_path)
    for page_index in range(len(doc)):
        page = doc[page_index]
        occurrences = page.search_for(old_text)
        if not occurrences:
            continue

        # Gắn khung trắng che chữ cũ
        for rect in occurrences:
            page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions()

        # Ghi chữ mới
        for rect in occurrences:
            fontsize = 11
            if len(new_text) > 18:
                fontsize = 9
            if len(new_text) > 30:
                fontsize = 7
            try:
                page.insert_text(rect.tl, new_text, fontsize=fontsize, color=(0, 0, 0), overlay=True)
            except Exception:
                pass

    doc.save(output_pdf_path)
    doc.close()


def extract_page_text(input_pdf_path: str, page_number: int):
    """Trích xuất text của trang."""
    doc = fitz.open(input_pdf_path)
    if page_number < 1 or page_number > len(doc):
        doc.close()
        raise ValueError("Số trang không hợp lệ.")
    
    page = doc[page_number - 1]
    text = page.get_text("text").strip()
    
    if not text:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = ocr_page_to_text(img, lang="vie+eng")
    
    doc.close()
    return text


def save_text_to_pdf(text: str, output_path: str):
    """Tạo file PDF mới từ text."""
    doc = fitz.open()
    page = doc.new_page()
    lines = text.splitlines() if text else [""]
    y = 50
    max_chars_per_line = 110

    for line in lines:
        wrapped = []
        current = ""
        for word in line.split(" "):
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars_per_line:
                current = candidate
            else:
                if current:
                    wrapped.append(current)
                current = word
        if current:
            wrapped.append(current)

        for wrap_line in wrapped or [""]:
            page.insert_text((50, y), wrap_line, fontsize=11, color=(0, 0, 0))
            y += 15
            if y > 760:
                page = doc.new_page()
                y = 50

    doc.save(output_path)
    doc.close()


def split_pdf_by_ranges(input_pdf_path: str, output_pdf_path: str, raw_ranges: str):
    """Tách các trang chỉ định từ PDF."""
    pages = parse_page_list(raw_ranges)
    doc_in = fitz.open(input_pdf_path)
    doc_out = fitz.open()
    page_numbers = [p - 1 for p in pages if 1 <= p <= len(doc_in)]

    for page_no in page_numbers:
        doc_out.insert_pdf(doc_in, from_page=page_no, to_page=page_no)

    doc_out.save(output_pdf_path)
    doc_out.close()
    doc_in.close()


def merge_pdfs(input_files: list, output_path: str):
    """Gộp nhiều PDF theo thứ tự."""
    if not input_files:
        raise ValueError("Chưa có file PDF nào được chọn để gộp.")
    
    out_doc = fitz.open()
    for f in input_files:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Không tìm thấy file: {f}")
        src = fitz.open(f)
        out_doc.insert_pdf(src)
        src.close()
    
    out_doc.save(output_path)
    out_doc.close()


def delete_pages_from_pdf(input_pdf_path: str, output_pdf_path: str, raw_pages: str):
    """Xóa các trang đã chọn khỏi PDF."""
    pages_to_delete = set(parse_page_list(raw_pages))
    doc_in = fitz.open(input_pdf_path)
    keep_pages = []
    total_pages = len(doc_in)

    for i in range(1, total_pages + 1):
        if i not in pages_to_delete:
            keep_pages.append(i)
    
    if not keep_pages:
        raise ValueError("Không còn trang nào để lưu sau khi xóa.")
    
    doc_out = fitz.open()
    for p in keep_pages:
        doc_out.insert_pdf(doc_in, from_page=p - 1, to_page=p - 1)
    
    doc_out.save(output_pdf_path)
    doc_out.close()
    doc_in.close()


# ============================================================
# MAIN APP
# ============================================================

class PDFSmartKitApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF SmartKit OCR & Editor")
        self.geometry("1200x760")
        self.minsize(980, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.current_pdf_path = ""
        self.merge_files = []

        self.create_sidebar()
        self.create_main_content()
        self.show_tab("ocr")

    # ========================================================
    # UI: SIDEBAR + TABS
    # ========================================================

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack_propagate(False)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)

        title = ctk.CTkLabel(
            self.sidebar,
            text="PDF SmartKit",
            font=ctk.CTkFont(size=26, weight="bold"),
            pady=12,
        )
        title.pack(fill="x", padx=18, pady=(20, 10))

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="OCR & Editor",
            font=ctk.CTkFont(size=13),
            text_color="#A6B5D8",
        )
        subtitle.pack(fill="x", padx=18, pady=(0, 20))

        self.tab_buttons = {}
        tab_names = [
            ("🔍 OCR", "ocr"),
            ("✏️ Sửa nội dung", "edit"),
            ("✂️ Tách PDF", "split"),
            ("🔗 Gộp PDF", "merge"),
            ("🗑️ Xóa trang", "delete"),
        ]

        for label, key in tab_names:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                height=42,
                corner_radius=10,
                command=lambda k=key: self.show_tab(k),
                fg_color="#2B2D31",
                hover_color="#3A3D45",
            )
            btn.pack(fill="x", padx=18, pady=8)
            self.tab_buttons[key] = btn

        # Theme switch
        theme_label = ctk.CTkLabel(self.sidebar, text="Theme", text_color="#A6B5D8", pady=8)
        theme_label.pack(fill="x", padx=18, pady=(20, 0))

        self.theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Dark / Light",
            command=self.toggle_theme,
        )
        self.theme_switch.pack(fill="x", padx=18, pady=(0, 20))

        # Footer
        footer = ctk.CTkLabel(
            self.sidebar,
            text="Offline • Local",
            font=ctk.CTkFont(size=12),
            text_color="#7B8AA8",
            pady=10,
        )
        footer.pack(side="bottom", fill="x", padx=18, pady=12)

    def toggle_theme(self):
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

    def create_main_content(self):
        self.main = ctk.CTkFrame(self, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

        self.tabs = {}

        # Tab OCR
        self.tabs["ocr"] = ctk.CTkFrame(self.main)
        self.tabs["ocr"].pack(fill="both", expand=True)
        self.build_ocr_tab()

        # Tab Edit
        self.tabs["edit"] = ctk.CTkFrame(self.main)
        self.tabs["edit"].pack(fill="both", expand=True)
        self.build_edit_tab()

        # Tab Split
        self.tabs["split"] = ctk.CTkFrame(self.main)
        self.tabs["split"].pack(fill="both", expand=True)
        self.build_split_tab()

        # Tab Merge
        self.tabs["merge"] = ctk.CTkFrame(self.main)
        self.tabs["merge"].pack(fill="both", expand=True)
        self.build_merge_tab()

        # Tab Delete
        self.tabs["delete"] = ctk.CTkFrame(self.main)
        self.tabs["delete"].pack(fill="both", expand=True)
        self.build_delete_tab()

        for key in self.tabs:
            self.tabs[key].pack_forget()

        # Progress bar
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self.main, variable=self.progress_var, width=600, height=18)
        self.progress_bar.pack(pady=(10, 0), padx=20, fill="x")
        self.progress_bar.pack_forget()

    def show_tab(self, key):
        for k, frame in self.tabs.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # ========================================================
    # TAB OCR
    # ========================================================

    def build_ocr_tab(self):
        container = self.tabs["ocr"]
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(
            container,
            text="🔍 Nhận diện OCR (Scan PDF → Searchable PDF / TXT)",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=20,
            pady=(20, 10),
            justify="left",
        )
        header.grid(row=0, column=0, sticky="w", padx=20)

        file_box = ctk.CTkFrame(container, corner_radius=12)
        file_box.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 10))

        self.ocr_file_label = ctk.CTkLabel(
            file_box,
            text="Chưa chọn file PDF",
            anchor="w",
            justify="left",
            padx=18,
            pady=18,
        )
        self.ocr_file_label.pack(side="left", fill="x", expand=True)

        btn_select = ctk.CTkButton(file_box, text="Chọn file PDF", command=self.choose_ocr_file)
        btn_select.pack(side="right", padx=12, pady=12)

        option_frame = ctk.CTkFrame(container, corner_radius=12)
        option_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkLabel(option_frame, text="Đầu ra: ", font=ctk.CTkFont(size=14)).pack(side="left", padx=18, pady=14)

        self.ocr_output_mode = ctk.StringVar(value="Searchable PDF")
        output_menu = ctk.CTkOptionMenu(
            option_frame,
            values=["Searchable PDF", "TXT"],
            variable=self.ocr_output_mode,
        )
        output_menu.pack(side="left", padx=10, pady=12)

        actions = ctk.CTkFrame(container, corner_radius=12)
        actions.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.ocr_btn = ctk.CTkButton(actions, text="Bắt đầu OCR", command=self.start_ocr_task, height=42)
        self.ocr_btn.pack(side="left", padx=18, pady=14)

        self.ocr_status = ctk.CTkLabel(actions, text="Sẵn sàng.", text_color="#A6B5D8")
        self.ocr_status.pack(side="left", padx=18, pady=14)

    def choose_ocr_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path:
            return
        self.current_pdf_path = file_path
        self.ocr_file_label.configure(text=file_path)

    def start_ocr_task(self):
        if not self.current_pdf_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file PDF đầu vào.")
            return
        self.ocr_status.configure(text="Đang xử lý OCR...")
        self.show_progress()

        threading.Thread(target=self.run_ocr_worker, daemon=True).start()

    def run_ocr_worker(self):
        try:
            output_mode = self.ocr_output_mode.get()
            input_pdf = self.current_pdf_path
            source_name = Path(input_pdf).stem

            if output_mode == "Searchable PDF":
                out_path = get_output_path(input_pdf, "_searchable")
                ocr_pdf_to_searchable_pdf(input_pdf, out_path)
                msg = f"Đã tạo file Searchable PDF:\n{out_path}"
            else:
                out_path = str(Path(input_pdf).with_name(f"{source_name}_ocr.txt"))
                ocr_pdf_to_txt(input_pdf, out_path)
                msg = f"Đã tạo file TXT:\n{out_path}"

            self.after(0, self.on_task_done, msg)
        except Exception as e:
            self.after(0, self.on_task_failed, str(e))
        finally:
            self.after(0, self.hide_progress)
            self.after(0, lambda: self.ocr_status.configure(text="Sẵn sàng."))

    # ========================================================
    # TAB SỬA NỘI DUNG PDF
    # ========================================================

    def build_edit_tab(self):
        container = self.tabs["edit"]
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            container,
            text="✏️ Sửa nội dung PDF",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=20,
            pady=(20, 10),
            justify="left",
        )
        header.grid(row=0, column=0, sticky="w", padx=20)

        file_box = ctk.CTkFrame(container, corner_radius=12)
        file_box.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        self.edit_file_label = ctk.CTkLabel(
            file_box,
            text="Chưa chọn file PDF",
            anchor="w",
            justify="left",
            padx=18,
            pady=18,
        )
        self.edit_file_label.pack(side="left", fill="x", expand=True)

        btn_select = ctk.CTkButton(file_box, text="Chọn PDF", command=self.choose_edit_file)
        btn_select.pack(side="right", padx=12, pady=12)

        section1 = ctk.CTkFrame(container, corner_radius=12)
        section1.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkLabel(section1, text="Cách 1: Tìm & Thay thế", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=18, pady=(18, 8))

        row = ctk.CTkFrame(section1)
        row.pack(fill="x", padx=18, pady=6)

        ctk.CTkLabel(row, text="Tìm: ").pack(side="left")
        self.old_text_var = ctk.StringVar(value="Nguyễn Văn A")
        ctk.CTkEntry(row, textvariable=self.old_text_var, width=280).pack(side="left", padx=10)

        row2 = ctk.CTkFrame(section1)
        row2.pack(fill="x", padx=18, pady=6)

        ctk.CTkLabel(row2, text="Thay: ").pack(side="left")
        self.new_text_var = ctk.StringVar(value="Nguyễn Văn B")
        ctk.CTkEntry(row2, textvariable=self.new_text_var, width=280).pack(side="left", padx=10)

        ctk.CTkButton(
            section1,
            text="Thực hiện Find & Replace",
            command=self.start_replace_task,
            height=40,
        ).pack(anchor="w", padx=18, pady=(10, 18))

        section2 = ctk.CTkFrame(container, corner_radius=12)
        section2.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))

        ctk.CTkLabel(section2, text="Cách 2: Trích xuất & Biên tập nhanh", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=18, pady=(18, 8))

        row_page = ctk.CTkFrame(section2)
        row_page.pack(fill="x", padx=18, pady=6)

        ctk.CTkLabel(row_page, text="Trang số: ").pack(side="left")
        self.page_number_var = ctk.StringVar(value="1")
        ctk.CTkEntry(row_page, textvariable=self.page_number_var, width=80).pack(side="left", padx=10)

        ctk.CTkButton(row_page, text="Trích xuất text", command=self.extract_page_text_to_editor).pack(side="left", padx=10)

        self.edit_textbox = ctk.CTkTextbox(section2, height=190, width=800)
        self.edit_textbox.pack(fill="both", expand=True, padx=18, pady=10)

        actions = ctk.CTkFrame(section2)
        actions.pack(fill="x", padx=18, pady=(0, 18))

        ctk.CTkButton(actions, text="Lưu thành PDF mới", command=self.save_edited_text_as_new_pdf, height=40).pack(side="left")

    def choose_edit_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file PDF để sửa",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path:
            return
        self.current_pdf_path = file_path
        self.edit_file_label.configure(text=file_path)

    def start_replace_task(self):
        if not self.current_pdf_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file PDF đầu vào.")
            return
        old_text = self.old_text_var.get().strip()
        new_text = self.new_text_var.get().strip()
        if not old_text:
            messagebox.showerror("Lỗi", "Từ khóa cần tìm không được để trống.")
            return

        self.show_progress()
        threading.Thread(
            target=self.run_replace_worker,
            args=(old_text, new_text),
            daemon=True,
        ).start()

    def run_replace_worker(self, old_text: str, new_text: str):
        try:
            output_path = get_output_path(self.current_pdf_path, "_replaced")
            replace_text_in_pdf(self.current_pdf_path, output_path, old_text, new_text)
            self.after(0, self.on_task_done, f"Đã lưu PDF sửa đổi:\n{output_path}")
        except Exception as e:
            self.after(0, self.on_task_failed, str(e))
        finally:
            self.after(0, self.hide_progress)

    def extract_page_text_to_editor(self):
        if not self.current_pdf_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file PDF đầu vào.")
            return
        try:
            page_number = int(self.page_number_var.get())
            text = extract_page_text(self.current_pdf_path, page_number)
            self.edit_textbox.delete("1.0", "end")
            self.edit_textbox.insert("1.0", text)
            messagebox.showinfo("Thành công", f"Đã trích xuất text của trang {page_number}.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def save_edited_text_as_new_pdf(self):
        text = self.edit_textbox.get("1.0", "end")
        if not self.current_pdf_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file PDF đầu vào.")
            return
        if not text.strip():
            messagebox.showwarning("Cảnh báo", "Không có nội dung nào để lưu.")
            return

        try:
            output_path = get_output_path(self.current_pdf_path, "_edited")
            save_text_to_pdf(text, output_path)
            messagebox.showinfo("Thành công", f"Đã lưu PDF mới:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    # ========================================================
    # TAB TÁCH PDF
    # ========================================================

    def build_split_tab(self):
        container = self.tabs["split"]
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            container,
            text="✂️ Tách PDF",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=20,
            pady=(20, 10),
            justify="left",
        )
        header.grid(row=0, column=0, sticky="w", padx=20)

        file_box = ctk.CTkFrame(container, corner_radius=12)
        file_box.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        self.split_file_label = ctk.CTkLabel(file_box, text="Chưa chọn file PDF", anchor="w", justify="left", padx=18, pady=18)
        self.split_file_label.pack(side="left", fill="x", expand=True)

        btn_select = ctk.CTkButton(file_box, text="Chọn file PDF", command=self.choose_split_file)
        btn_select.pack(side="right", padx=12, pady=12)

        input_frame = ctk.CTkFrame(container, corner_radius=12)
        input_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkLabel(input_frame, text="Khoảng trang: ", font=ctk.CTkFont(size=14)).pack(side="left", padx=18, pady=14)
        self.split_range_var = ctk.StringVar(value="1-3")
        ctk.CTkEntry(input_frame, textvariable=self.split_range_var, width=250).pack(side="left", padx=10, pady=12)

        action_frame = ctk.CTkFrame(container, corner_radius=12)
        action_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkButton(action_frame, text="Tách PDF", command=self.start_split_task, height=42).pack(side="left", padx=18, pady=14)

    def choose_split_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file PDF để tách",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path:
            return
        self.current_pdf_path = file_path
        self.split_file_label.configure(text=file_path)

    def start_split_task(self):
        if not self.current_pdf_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file PDF đầu vào.")
            return
        try:
            range_text = self.split_range_var.get()
            parse_page_list(range_text)
            output_path = get_output_path(self.current_pdf_path, "_split")
            self.show_progress()
            threading.Thread(
                target=self.run_split_worker,
                args=(output_path, range_text),
                daemon=True,
            ).start()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def run_split_worker(self, output_path: str, range_text: str):
        try:
            split_pdf_by_ranges(self.current_pdf_path, output_path, range_text)
            self.after(0, self.on_task_done, f"Đã tách PDF thành:\n{output_path}")
        except Exception as e:
            self.after(0, self.on_task_failed, str(e))
        finally:
            self.after(0, self.hide_progress)

    # ========================================================
    # TAB GỘP PDF
    # ========================================================

    def build_merge_tab(self):
        container = self.tabs["merge"]
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            container,
            text="🔗 Gộp PDF",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=20,
            pady=(20, 10),
            justify="left",
        )
        header.grid(row=0, column=0, sticky="w", padx=20)

        file_box = ctk.CTkFrame(container, corner_radius=12)
        file_box.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        ctk.CTkLabel(file_box, text="Danh sách file đã chọn", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=18, pady=(14, 8))
        self.merge_listbox = ctk.CTkTextbox(file_box, height=220)
        self.merge_listbox.pack(fill="both", padx=18, pady=(0, 14), expand=True)

        btn_frame = ctk.CTkFrame(container, corner_radius=12)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Chọn file PDF", command=self.choose_merge_files, height=38).pack(side="left", padx=18, pady=14)
        ctk.CTkButton(btn_frame, text="Gộp PDF", command=self.start_merge_task, height=38).pack(side="left", padx=10, pady=14)

    def choose_merge_files(self):
        files = filedialog.askopenfilenames(
            title="Chọn nhiều file PDF để gộp",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not files:
            return
        self.merge_files = list(files)
        self.merge_listbox.delete("1.0", "end")
        for idx, fp in enumerate(self.merge_files, start=1):
            self.merge_listbox.insert("end", f"{idx}. {fp}\n")

    def start_merge_task(self):
        if not self.merge_files:
            messagebox.showerror("Lỗi", "Chưa chọn file PDF nào để gộp.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Lưu file PDF đã gộp",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not output_path:
            return

        self.show_progress()
        threading.Thread(
            target=self.run_merge_worker,
            args=(self.merge_files, output_path),
            daemon=True,
        ).start()

    def run_merge_worker(self, files, output_path):
        try:
            merge_pdfs(files, output_path)
            self.after(0, self.on_task_done, f"Đã gộp PDF thành:\n{output_path}")
        except Exception as e:
            self.after(0, self.on_task_failed, str(e))
        finally:
            self.after(0, self.hide_progress)

    # ========================================================
    # TAB XÓA TRANG PDF
    # ========================================================

    def build_delete_tab(self):
        container = self.tabs["delete"]
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            container,
            text="🗑️ Xóa trang PDF",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=20,
            pady=(20, 10),
            justify="left",
        )
        header.grid(row=0, column=0, sticky="w", padx=20)

        file_box = ctk.CTkFrame(container, corner_radius=12)
        file_box.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        self.delete_file_label = ctk.CTkLabel(file_box, text="Chưa chọn file PDF", anchor="w", justify="left", padx=18, pady=18)
        self.delete_file_label.pack(side="left", fill="x", expand=True)

        btn_select = ctk.CTkButton(file_box, text="Chọn file PDF", command=self.choose_delete_file)
        btn_select.pack(side="right", padx=12, pady=12)

        page_frame = ctk.CTkFrame(container, corner_radius=12)
        page_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkLabel(page_frame, text="Số trang cần xóa: ", font=ctk.CTkFont(size=14)).pack(side="left", padx=18, pady=14)
        self.delete_pages_var = ctk.StringVar(value="2,4")
        ctk.CTkEntry(page_frame, textvariable=self.delete_pages_var, width=250).pack(side="left", padx=10, pady=12)

        action_frame = ctk.CTkFrame(container, corner_radius=12)
        action_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkButton(action_frame, text="Xóa trang", command=self.start_delete_task, height=42).pack(side="left", padx=18, pady=14)

    def choose_delete_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file PDF để xóa trang",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path:
            return
        self.current_pdf_path = file_path
        self.delete_file_label.configure(text=file_path)

    def start_delete_task(self):
        if not self.current_pdf_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file PDF đầu vào.")
            return
        try:
            parse_page_list(self.delete_pages_var.get())
            output_path = get_output_path(self.current_pdf_path, "_without_pages")
            self.show_progress()
            threading.Thread(
                target=self.run_delete_worker,
                args=(output_path, self.delete_pages_var.get()),
                daemon=True,
            ).start()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def run_delete_worker(self, output_path: str, page_text: str):
        try:
            delete_pages_from_pdf(self.current_pdf_path, output_path, page_text)
            self.after(0, self.on_task_done, f"Đã xóa trang và lưu file:\n{output_path}")
        except Exception as e:
            self.after(0, self.on_task_failed, str(e))
        finally:
            self.after(0, self.hide_progress)

    # ========================================================
    # UTILITY METHODS
    # ========================================================

    def show_progress(self):
        self.progress_bar.pack(pady=(10, 0), padx=20, fill="x")
        self.progress_bar.start()

    def hide_progress(self):
        try:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
        except Exception:
            pass

    def on_task_done(self, message: str):
        self.hide_progress()
        messagebox.showinfo("Thành công", message)

    def on_task_failed(self, error_text: str):
        self.hide_progress()
        messagebox.showerror("Lỗi", error_text)


# ============================================================
# CHẠY ỨNG DỤNG
# ============================================================

if __name__ == "__main__":
    try:
        app = PDFSmartKitApp()
        app.mainloop()
    except Exception as e:
        print(f"Lỗi khởi chạy ứng dụng: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
