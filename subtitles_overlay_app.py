import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import whisper
import pysubs2
import os
import subprocess # Додаємо бібліотеку для запуску зовнішніх команд (FFmpeg)
import sys

# --- Основна логіка ---
def create_ass_subtitles(video_path, max_words_per_segment, model_name="base"):
    """
    Створює .ass субтитри з точними часовими мітками за допомогою Whisper.
    Повертає шлях до створеного .ass файлу або None у разі помилки.
    """
    try:
        status_label.config(text="Статус: Завантаження моделі Whisper...")
        root.update_idletasks()
        model = whisper.load_model(model_name) 

        status_label.config(text="Статус: Транскрипція аудіо (це може зайняти багато часу)...")
        root.update_idletasks()
        
        result = model.transcribe(video_path, word_timestamps=True)

        status_label.config(text="Статус: Створення .ASS файлу...")
        root.update_idletasks()
        
        subs = pysubs2.SSAFile()
        default_style = pysubs2.SSAStyle(
            fontname='Arial', fontsize=24, primarycolor=pysubs2.Color(255, 255, 255),
            outlinecolor=pysubs2.Color(0, 0, 0), backcolor=pysubs2.Color(0, 0, 0, 128),
            bold=True, borderstyle=1, outline=1.5, shadow=0.5,
            alignment=pysubs2.Alignment.BOTTOM_CENTER, marginv=15
        )
        subs.styles['Default'] = default_style

        segments = result['segments']
        all_words = []
        for s in segments:
            if 'words' in s:
                all_words.extend(s['words'])

        current_pos = 0
        while current_pos < len(all_words):
            segment_words = all_words[current_pos : current_pos + max_words_per_segment]
            
            if not segment_words: break

            start_time = segment_words[0]['start'] * 1000
            end_time = segment_words[-1]['end'] * 1000
            text = " ".join(word['word'] for word in segment_words)
            
            event = pysubs2.SSAEvent(start=start_time, end=end_time, text=text.strip())
            subs.events.append(event)
            
            current_pos += max_words_per_segment

        output_path = os.path.splitext(video_path)[0] + ".ass"
        subs.save(output_path)
        return output_path
    except Exception as e:
        messagebox.showerror("Помилка при створенні .ass", str(e))
        return None

# --- НОВИЙ КОД: ФУНКЦІЯ ДЛЯ ВПАЮВАННЯ СУБТИТРІВ ---
def burn_in_subtitles(video_path, ass_path):
    """
    Використовує FFmpeg для накладання .ass файлу на відео.
    """
    try:
        status_label.config(text="Статус: Накладання субтитрів на відео (дуже повільно)...")
        root.update_idletasks()
        
        output_video_path = os.path.splitext(video_path)[0] + "_subtitled.mp4"
        
        # FFmpeg може мати проблеми зі шляхами Windows. Ця функція це виправляє.
        escaped_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")

        # Формуємо команду для FFmpeg
        # -y: перезаписувати вихідний файл без запитань
        # -i "{video_path}": вхідне відео
        # -vf "ass={escaped_ass_path}": відеофільтр для накладання ASS (без зайвих лапок)
        # -c:v libx264: популярний відеокодек
        # -preset veryfast: прискорює кодування за рахунок розміру файлу
        # -c:a copy: копіювати аудіодоріжку без перекодування (швидко)
        command = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', f"ass={escaped_ass_path}",
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
            '-c:a', 'copy',
            output_video_path
        ]

        # Запускаємо процес FFmpeg і захоплюємо вивід для логування помилок
        si = None
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', startupinfo=si)

        if result.returncode == 0:
            return output_video_path
        else:
            # Якщо сталася помилка, показуємо детальний звіт
            error_details = f"FFmpeg завершився з помилкою.\n\n" \
                            f"Код помилки: {result.returncode}\n\n" \
                            f"Повідомлення (stderr):\n{result.stderr}"
            messagebox.showerror("Помилка FFmpeg", error_details)
            return None

    except Exception as e:
        messagebox.showerror("Помилка накладання", str(e))
        return None

# --- Функції для GUI ---
def select_video_file():
    file_path = filedialog.askopenfilename(filetypes=[("Відеофайли", "*.mp4 *.avi *.mov *.mkv")])
    if file_path:
        video_path_entry.delete(0, tk.END)
        video_path_entry.insert(0, file_path)

def start_processing():
    video_path = video_path_entry.get()
    if not os.path.exists(video_path):
        messagebox.showwarning("Увага", "Будь ласка, оберіть існуючий відеофайл.")
        return
        
    try:
        max_words = int(max_words_entry.get())
        if max_words <= 0: raise ValueError
    except ValueError:
        messagebox.showwarning("Увага", "Кількість слів має бути цілим додатнім числом.")
        return
    
    # Створюємо .ass файл
    ass_file_path = create_ass_subtitles(video_path, max_words)
    
    if ass_file_path:
        # Перевіряємо, чи потрібно накладати субтитри
        if burn_in_var.get():
            final_video = burn_in_subtitles(video_path, ass_file_path)
            if final_video:
                status_label.config(text=f"Статус: Готово! Створено два файли.")
                messagebox.showinfo("Успіх", f"Створено два файли:\n1. Файл субтитрів: {os.path.basename(ass_file_path)}\n2. Відео з субтитрами: {os.path.basename(final_video)}")
        else:
            status_label.config(text=f"Статус: Готово! Файл {os.path.basename(ass_file_path)} створено.")
            messagebox.showinfo("Успіх", f"Файл субтитрів успішно створено:\n{ass_file_path}")

# --- Налаштування графічного інтерфейсу (GUI) ---
root = tk.Tk()
root.title("Професійний Створювач Субтитрів (Whisper + ASS)")
root.geometry("550x240")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(expand=True, fill=tk.BOTH)

# ... (решта коду GUI без змін)
tk.Label(frame, text="Відеофайл:").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
video_path_entry = tk.Entry(frame, width=60)
video_path_entry.grid(row=1, column=0, pady=2, sticky="ew")
tk.Button(frame, text="Огляд...", command=select_video_file).grid(row=1, column=1, padx=5)

tk.Label(frame, text="Макс. слів у сегменті:").grid(row=2, column=0, sticky="w", pady=(10, 2))
max_words_entry = tk.Entry(frame, width=20)
max_words_entry.insert(0, "7")
max_words_entry.grid(row=3, column=0, sticky="w")

# --- ЗМІНИ В ІНТЕРФЕЙСІ: ДОДАЄМО CHECKBOX ---
burn_in_var = tk.BooleanVar()
burn_in_checkbox = tk.Checkbutton(frame, text="Накласти субтитри на відео (повільно)", variable=burn_in_var)
burn_in_checkbox.grid(row=4, column=0, sticky="w", pady=5)

generate_button = tk.Button(frame, text="Створити Субтитри", command=start_processing, height=2, font=("Segoe UI", 10, "bold"))
generate_button.grid(row=3, column=1, rowspan=2, pady=(10,0), padx=10, sticky="nsew")

status_label = tk.Label(root, text="Статус: очікування...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

frame.columnconfigure(0, weight=3)
frame.columnconfigure(1, weight=1)

root.mainloop()