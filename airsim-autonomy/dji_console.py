"""DJI connection commissioning UI. This tool only sends status requests."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from dji_link import StatusClient, assess, number


def main():
    app = tk.Tk()
    app.title('DJI 真機連線檢查 0.1 — 只讀遙測')
    app.geometry('800x640')
    frame = ttk.Frame(app, padding=18)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Smart Controller → APP → PC', font=('Microsoft JhengHei', 16)).pack(anchor='w')
    ttk.Label(frame, text='本工具只讀取狀態，不起飛、不切換模式、不接管搖桿。').pack(anchor='w', pady=8)
    row = ttk.Frame(frame)
    row.pack(fill='x')
    host, token = tk.StringVar(value='127.0.0.1'), tk.StringVar()
    ttk.Label(row, text='HOST').pack(side='left')
    ttk.Entry(row, textvariable=host, width=20).pack(side='left', padx=6)
    ttk.Label(row, text='APP 六位驗證碼').pack(side='left')
    ttk.Entry(row, textvariable=token, show='*', width=10).pack(side='left', padx=6)
    state = tk.StringVar(value='尚未連線')
    ttk.Label(frame, textvariable=state, wraplength=750).pack(anchor='w', pady=12)
    fields = [('model','機型'), ('registration','SDK 註冊'), ('controlProfile','APP 模式'),
              ('foreground','APP 前景'), ('remoteAllowed','前景控制授權'),
              ('owner','搖桿持有者'), ('virtualStickEnabled','搖桿啟用'),
              ('flying','飛行中'), ('motorsOn','馬達運轉'), ('battery','電量 %'),
              ('altitudeM','飛控高度 m（不是地形淨空）'), ('speedMps','速度 m/s'),
              ('yawDeg','航向 °'), ('pitchDeg','俯仰 °'), ('rollDeg','橫滾 °'),
              ('telemetryAgeMs','APP 遙測年齡 ms')]
    grid = ttk.Frame(frame)
    grid.pack(fill='x')
    values = {}
    for i, (key, label) in enumerate(fields):
        col, line = (i // 8) * 2, i % 8
        ttk.Label(grid, text=label).grid(row=line, column=col, sticky='w', padx=6, pady=3)
        values[key] = tk.StringVar(value='—')
        ttk.Label(grid, textvariable=values[key], width=24).grid(row=line, column=col+1, sticky='w')
    ttk.Separator(frame).pack(fill='x', pady=14)
    mode = tk.StringVar(value='INDOOR')
    ttk.Radiobutton(frame, text='室內：無可靠 GPS', variable=mode, value='INDOOR').pack(anchor='w')
    ttk.Radiobutton(frame, text='戶外：有 GPS（後續開發）', variable=mode, value='OUTDOOR').pack(anchor='w')
    ttk.Label(frame, text='真機 XY：未知；目前不向 UE4 機體套用假位置。\n室內缺少已校準定位；戶外 GPS 航點橋接尚未實作。\n非模擬器遙測不代表已通過飛行驗收或可自動導航。', wraplength=740).pack(anchor='w', pady=8)
    ttk.Button(frame, text='UE4 航點 → 真機到點（尚未開放）', state='disabled').pack(fill='x')
    events = queue.Queue(maxsize=8)
    generation, cancel, last = 0, threading.Event(), None

    def clear():
        for value in values.values():
            value.set('—')

    def disconnect():
        nonlocal generation, last
        cancel.set()
        generation += 1
        last = None
        clear()
        state.set('已停止監看；不會變更飛行器的既有控制狀態')
        connect_button.configure(state='normal')

    def connect():
        nonlocal cancel, generation, last
        try:
            client = StatusClient(host.get(), token.get())
        except ValueError as exc:
            messagebox.showerror('連線設定', str(exc))
            return
        disconnect()
        cancel = threading.Event()
        stop, gen = cancel, generation
        state.set('連線中…')
        connect_button.configure(state='disabled')

        def worker():
            while not stop.is_set():
                try:
                    data = client.read_status()
                    event = (gen, time.monotonic(), data, None)
                except Exception as exc:
                    # No automatic retries after authentication or transport failure.
                    event = (gen, time.monotonic(), None, type(exc).__name__)
                try:
                    events.put_nowait(event)
                except queue.Full:
                    break
                if event[3] is not None or stop.wait(.5):
                    break
        threading.Thread(target=worker, daemon=True).start()

    def tick():
        nonlocal last
        while True:
            try:
                gen, received, data, error = events.get_nowait()
            except queue.Empty:
                break
            if gen != generation:
                continue
            if error:
                disconnect()
                state.set('連線失敗／已斷線：核對 USB forward、APP 前景與六位碼。\n錯誤多次需等 30 秒；本工具不會自動重試。類型：' + error)
            else:
                last = (received, data)
        if last:
            received, data = last
            result = assess(data, time.monotonic() - received)
            state.set(result['source'] + '｜真機到點：未開放')
            if result['fresh']:
                for key, _ in fields:
                    value = data.get(key)
                    if type(value) is float:
                        value = f'{value:.2f}' if number(value) else '—'
                    values[key].set(str(value)[:60] if value is not None else '—')
            else:
                clear()
        app.after(100, tick)

    connect_button = ttk.Button(row, text='連線／監看', command=connect)
    connect_button.pack(side='left', padx=6)
    ttk.Button(row, text='斷線', command=disconnect).pack(side='left')
    app.protocol('WM_DELETE_WINDOW', lambda: (disconnect(), app.destroy()))
    tick()
    app.mainloop()


if __name__ == '__main__':
    main()
