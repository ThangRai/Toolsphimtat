import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
import psutil
import threading
import keyboard
import time
import json
import os

CONFIG_FILE = "apps_config.json"
DOUBLE_PRESS_INTERVAL = 0.5
apps = {}
key_listener_running = False

def save_apps():
    data = {}
    for key, app in apps.items():
        data[key] = {'name': app['name'], 'path': app['path']}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def load_apps():
    if not os.path.exists(CONFIG_FILE):
        return
    with open(CONFIG_FILE, 'r') as f:
        data = json.load(f)
        for hotkey, info in data.items():
            apps[hotkey] = {
                'name': info['name'],
                'path': info['path'],
                'running_pids': set(),
                'last_press_time': 0,
                'press_count': 0,
            }
            tree.insert("", "end", values=(info['name'], info['path'], hotkey.upper()))

def open_app(app):
    try:
        proc = subprocess.Popen(app['path'])
        app['running_pids'].add(proc.pid)
        log(f"✅ Đã mở {app['name']} (PID: {proc.pid})")
    except Exception as e:
        log(f"❌ Lỗi khi mở {app['name']}: {e}")

def close_app(app):
    if not app['running_pids']:
        log(f"⚠️ Không có tiến trình {app['name']} để đóng.")
        return

    for pid in list(app['running_pids']):
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
            log(f"✅ Đã đóng {app['name']} (PID: {pid})")
        except psutil.NoSuchProcess:
            log(f"⚠️ PID {pid} không tồn tại.")
        except Exception as e:
            log(f"❌ Lỗi khi đóng PID {pid}: {e}")
        finally:
            app['running_pids'].discard(pid)

def on_key_press(event):
    key = event.name.lower()
    if key in apps:
        app = apps[key]
        now = time.time()
        if now - app['last_press_time'] > DOUBLE_PRESS_INTERVAL:
            app['press_count'] = 0
        app['press_count'] += 1
        app['last_press_time'] = now

        if app['press_count'] == 2:
            if app['running_pids']:
                close_app(app)
            else:
                open_app(app)
            app['press_count'] = 0

def start_key_listener():
    global key_listener_running
    key_listener_running = True
    keyboard.on_press(on_key_press)
    log("▶ Script đang chạy... Nhấn ESC hoặc Dừng.")
    keyboard.wait('esc')
    stop_script()

def stop_script():
    global key_listener_running
    key_listener_running = False
    keyboard.unhook_all()
    btn_add.config(state=tk.NORMAL)
    btn_start.config(state=tk.NORMAL)
    btn_stop.config(state=tk.DISABLED)
    log("🔝 Đã dừng script.")

def add_app():
    name = entry_name.get().strip()
    path = entry_path.get().strip()
    hotkey = entry_hotkey.get().strip().lower()

    if not name or not path or not hotkey:
        messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ thông tin.")
        return
    if len(hotkey) != 1 or not hotkey.isalnum():
        messagebox.showwarning("Phím không hợp lệ", "Phím tắt phải là 1 ký tự chữ hoặc số.")
        return
    if hotkey in apps:
        messagebox.showwarning("Trùng phím", "Phím tắt này đã được dùng.")
        return

    apps[hotkey] = {
        'name': name,
        'path': path,
        'running_pids': set(),
        'last_press_time': 0,
        'press_count': 0,
    }
    tree.insert("", "end", values=(name, path, hotkey.upper()))
    entry_name.delete(0, tk.END)
    entry_path.delete(0, tk.END)
    entry_hotkey.delete(0, tk.END)
    save_apps()

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
    if file_path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)

def start_script():
    if not apps:
        messagebox.showwarning("Không có ứng dụng", "Thêm ít nhất một ứng dụng trước khi chạy.")
        return
    btn_add.config(state=tk.DISABLED)
    btn_start.config(state=tk.DISABLED)
    btn_stop.config(state=tk.NORMAL)
    threading.Thread(target=start_key_listener, daemon=True).start()

def log(message):
    text_log.config(state=tk.NORMAL)
    text_log.insert(tk.END, message + "\n")
    text_log.see(tk.END)
    text_log.config(state=tk.DISABLED)

root = tk.Tk()
root.title("✨ Trình tạo phím tắt ứng dụng")
root.geometry("800x700")
root.configure(bg="#2c3e50")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", rowheight=28, font=('Segoe UI', 11), background="#ecf0f1", fieldbackground="#ecf0f1", foreground="#2c3e50")
style.configure("TButton", font=('Segoe UI', 11), padding=6)
style.configure("TLabel", background="#2c3e50", foreground="white", font=('Segoe UI', 11))

title = tk.Label(root, text="⚙️ Trình cấu hình phím tắt ứng dụng", font=('Segoe UI', 16, 'bold'), bg="#2c3e50", fg="white")
title.pack(pady=15)

frame_form = tk.Frame(root, bg="#34495e", padx=20, pady=15)
frame_form.pack(pady=10, fill=tk.X, padx=20)

tk.Label(frame_form, text="Tên ứng dụng:", bg="#34495e", fg="white", font=('Segoe UI', 11)).grid(row=0, column=0, sticky="e", pady=5)
entry_name = tk.Entry(frame_form, font=('Segoe UI', 11), width=30)
entry_name.grid(row=0, column=1, padx=10)

tk.Label(frame_form, text="Đường dẫn file .exe:", bg="#34495e", fg="white", font=('Segoe UI', 11)).grid(row=1, column=0, sticky="e", pady=5)
entry_path = tk.Entry(frame_form, font=('Segoe UI', 11), width=30)
entry_path.grid(row=1, column=1, padx=10)
btn_browse = ttk.Button(frame_form, text="📂 Chọn file", command=browse_file)
btn_browse.grid(row=1, column=2, padx=5)

tk.Label(frame_form, text="Phím tắt (1 ký tự):", bg="#34495e", fg="white", font=('Segoe UI', 11)).grid(row=2, column=0, sticky="e", pady=5)
entry_hotkey = tk.Entry(frame_form, font=('Segoe UI', 11), width=10)
entry_hotkey.grid(row=2, column=1, sticky="w")

btn_add = ttk.Button(frame_form, text="➕ Thêm ứng dụng", command=add_app)
btn_add.grid(row=3, columnspan=3, pady=10)

tk.Label(root, text="📋 Danh sách ứng dụng", font=('Segoe UI', 13, 'bold'), bg="#2c3e50", fg="white").pack()
tree = ttk.Treeview(root, columns=("Tên", "Đường dẫn", "Phím"), show='headings', height=6)
tree.heading("Tên", text="Tên ứng dụng")
tree.heading("Đường dẫn", text="Đường dẫn")
tree.heading("Phím", text="Phím tắt")
tree.pack(pady=10, padx=20, fill=tk.X)

btn_frame = tk.Frame(root, bg="#2c3e50")
btn_frame.pack(pady=10)
btn_start = ttk.Button(btn_frame, text="▶ Bắt đầu chạy", command=start_script)
btn_start.pack(side=tk.LEFT, padx=10)
btn_stop = ttk.Button(btn_frame, text="⏹ Dừng", command=stop_script, state=tk.DISABLED)
btn_stop.pack(side=tk.LEFT, padx=10)

tk.Label(root, text="🧰 Nhật ký thao tác:", font=('Segoe UI', 13, 'bold'), bg="#2c3e50", fg="white").pack()
text_log = tk.Text(root, height=10, state=tk.DISABLED, font=('Consolas', 10), bg="#ecf0f1")
text_log.pack(fill=tk.BOTH, padx=20, pady=10, expand=True)

load_apps()
root.mainloop()
