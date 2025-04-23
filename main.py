import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyperclip
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re

## so simple
class GPTTextCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("GPT Text Cleaner")
        self.root.geometry("800x600")

        self.text_input = tk.Text(root, height=12, width=80)
        self.text_input.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=5, padx=10, fill=tk.X)

        self.btn_load_file = ttk.Button(btn_frame, text="Загрузить файл", command=self.load_file)
        self.btn_load_file.pack(side=tk.LEFT, padx=5)

        self.btn_load_clipboard = ttk.Button(btn_frame, text="Из буфера", command=self.load_from_clipboard)
        self.btn_load_clipboard.pack(side=tk.LEFT, padx=5)

        self.btn_process = ttk.Button(btn_frame, text="Обработать", command=self.process_text)
        self.btn_process.pack(side=tk.RIGHT, padx=5)

        self.result_text = tk.Text(root, height=12, width=80)
        self.result_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        save_frame = ttk.Frame(root)
        save_frame.pack(pady=5, padx=10, fill=tk.X)

        self.save_btn = ttk.Button(save_frame, text="Сохранить в Word", command=self.save_to_word)
        self.save_btn.pack(side=tk.LEFT, padx=5)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Текстовые файлы", "*.txt *.md *.json")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.text_input.delete('1.0', tk.END)
                self.text_input.insert(tk.END, f.read())

    def load_from_clipboard(self):
        try:
            clipboard_text = pyperclip.paste()
            self.text_input.delete('1.0', tk.END)
            self.text_input.insert(tk.END, clipboard_text)
        except:
            messagebox.showerror("Ошибка", "Не удалось загрузить текст из буфера")

    def clean_text(self, text):
        # Удаление ведущих markdown-символов и пробелов
        text = re.sub(r'^[\*\#\-\+]+\s*', '', text, flags=re.MULTILINE)

        # Упрощение длинных дефисов
        text = re.sub(r'—+', '—', text)

        # Полное удаление всех звездочек (включая ** и *)
        text = re.sub(r'\*+', '', text)

        # Удаление лишних пробелов в начале строк
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)

        # Обработка списков
        text = re.sub(r'^(\-|\*)\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+\.)\s+', r'\1 ', text, flags=re.MULTILINE)

        # Удаление лишних пробелов в конце строк
        text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)

        # Удаление лишних пустых строк (3+)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Удаление множественных пробелов между словами (только пробелы, не переносы)
        text = re.sub(r'[ ]{2,}', ' ', text)

        # Восстановление переносов после маркированных списков
        text = re.sub(r'(\n• )', r'\n\n• ', text)  # Добавляем перенос перед маркерами
        text = re.sub(r'(\n\d+\.\s)', r'\n\n\1', text)  # Добавляем перенос перед нумерованными пунктами

        return text.strip()

    def process_tables(self, text):
        tables = []
        lines = text.split('\n')
        current_table = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            if stripped and stripped.startswith('|'):
                if not in_table:
                    in_table = True
                current_table.append(line.strip('|').strip())
            else:
                if in_table:
                    if current_table:
                        tables.append(current_table)
                        current_table = []
                    in_table = False
        if current_table:
            tables.append(current_table)

        processed_tables = []
        for table in tables:
            rows = []
            headers = []
            separator_found = False
            for idx, row in enumerate(table):
                cells = [cell.strip() for cell in row.split('|')]
                if idx == 0:
                    headers = cells
                else:
                    if all(re.match(r'^[-\s]*$', cell) for cell in cells):
                        separator_found = True
                    else:
                        if separator_found:
                            rows.append(cells)
                        else:
                            if idx > 0:
                                rows.append(cells)
            processed_tables.append((headers, rows))
        return processed_tables

    def save_to_word(self):
        raw_text = self.text_input.get('1.0', tk.END)
        processed_text = self.clean_text(raw_text)
        tables = self.process_tables(processed_text)

        doc = Document()
        doc.styles['Normal'].font.name = 'Arial'

        for para in processed_text.split('\n\n'):
            if para.strip():
                p = doc.add_paragraph()
                p.add_run(para).bold = False
                p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

        for header, rows in tables:
            if not header:  # Проверка на пустые таблицы
                continue
            table = doc.add_table(rows=1, cols=len(header))
            hdr_cells = table.rows[0].cells
            for i in range(len(header)):
                hdr_cells[i].text = header[i]
                hdr_cells[i].paragraphs[0].runs[0].bold = True
                hdr_cells[i].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            for row in rows:
                row_cells = table.add_row().cells
                for i in range(len(row)):
                    row_cells[i].text = row[i]
                    row_cells[i].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            table.style = 'Table Grid'
            for row in table.rows:
                for cell in row.cells:
                    cell.vertical_alignment = 1

        file_path = filedialog.asksaveasfilename(defaultextension=".docx",
                                                 filetypes=[("Word Documents", "*.docx")])
        if file_path:
            doc.save(file_path)
            messagebox.showinfo("Успех", "Документ сохранён")

    def process_text(self):
        raw_text = self.text_input.get('1.0', tk.END).strip()
        processed_text = self.clean_text(raw_text)
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, processed_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = GPTTextCleaner(root)
    root.mainloop()