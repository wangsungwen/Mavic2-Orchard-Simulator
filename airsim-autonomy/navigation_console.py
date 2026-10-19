"""Navigation entry points only; no aircraft connection or flight commands."""
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = Path(__file__).resolve().parent


def launch_script(path, *args):
    if not path.is_file():
        raise FileNotFoundError(path)
    return subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(path), *args], cwd=str(path.parent),
        creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    app = tk.Tk()
    app.title("Mavic 2 Enterprise Dual — 導航功能入口")
    app.geometry("760x700")
    frame = ttk.Frame(app, padding=22)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="選擇使用場地", font=("Microsoft JhengHei", 16)).pack(anchor="w")
    mode = tk.StringVar(value="INDOOR")
    text = tk.StringVar()
    for value, label in [("INDOOR", "室內：無可靠 GPS（優先開發）"),
                         ("OUTDOOR", "戶外：有 GPS（後續追加）")]:
        ttk.Radiobutton(frame, text=label, variable=mode, value=value,
                        command=lambda: refresh()).pack(anchor="w", pady=6)
    ttk.Separator(frame).pack(fill="x", pady=12)
    ttk.Label(frame, textvariable=text, wraplength=650, justify="left").pack(anchor="w")

    def run(path, *args):
        try:
            launch_script(path, *args)
        except Exception as exc:
            messagebox.showerror("無法開啟", str(exc))

    simulation = ttk.Button(frame, text="開啟現有 UE4 / AirSim 場景",
        command=lambda: run(ROOT / "scripts/Start-Mavic2.ps1"))
    simulation.pack(fill="x", pady=(18, 6))
    def start_points():
        try:
            subprocess.Popen([str(ROOT / '.venv/Scripts/python.exe'), str(ROOT / 'point_navigation.py')],
                             cwd=str(ROOT), creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as exc:
            messagebox.showerror("無法開啟", str(exc))
    points = ttk.Button(frame, text="啟動 UE4 選點飛行（先關閉舊 UE4 視窗）", command=start_points)
    points.pack(fill="x", pady=6)
    demo = ttk.Button(frame, text="開啟雙搖桿離線示範（不連真機）",
        command=lambda: run(ROOT.parent / "joystick-dual/scripts/start-pc.ps1", "-Demo"))
    demo.pack(fill="x", pady=6)
    def start_dji_status():
        try:
            subprocess.Popen([str(ROOT / '.venv/Scripts/python.exe'), str(ROOT / 'dji_console.py')],
                             cwd=str(ROOT), creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as exc:
            messagebox.showerror("無法開啟", str(exc))
    ttk.Button(frame, text="DJI 真機連線檢查（只讀，不起飛）",
               command=start_dji_status).pack(fill="x", pady=6)
    live = ttk.Button(frame, text="開啟既有 DJI 人工控制台（需 APP 另行授權）",
        command=lambda: run(ROOT.parent / "joystick-dual/scripts/start-pc.ps1"))
    live.pack(fill="x", pady=6)
    target = ttk.Button(frame, text="真機：執行 UE4 航點（尚未提供）", state="disabled")
    target.pack(fill="x", pady=6)
    ttk.Label(frame, text="此視窗只選擇工具，不會切換飛控模式、連線、解鎖或起飛。",
              wraplength=650).pack(anchor="w", pady=12)

    def refresh():
        indoor = mode.get() == "INDOOR"
        text.set(
            "室內：目前沒有場地定位設備，真機自動到點不可用。\n"
            "選點飛行：UE4 點地面 → 上下鍵調高度 → Enter 確認 → X 中止。\n"
            "UE4 選點只控制 AirSim；DJI 真機先以只讀連線檢查確認遙測。"
            if indoor else
            "戶外：保留獨立功能選項，尚未接入本介面。\n"
            "後續以 GPS／起飛點與既有 DJI 航點 APP 串接。\n"
            "選擇此項不會解除室內限制，也不會改變飛行器模式。")
        simulation.configure(state="normal" if indoor else "disabled")
        demo.configure(state="normal" if indoor else "disabled")
        points.configure(state="normal" if indoor else "disabled")
        live.configure(state="normal" if indoor else "disabled")

    refresh()
    app.mainloop()


if __name__ == "__main__":
    main()
