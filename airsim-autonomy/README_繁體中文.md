# 本專案 → AirSim 自主航點仿真包

此資料夾新增 AirSim 後端，重用 `../pc-control/mission_intelligence.py` 的航線解析與圍欄／地形檢查。既有 Android 與 PC 程式不需要修改。需保留本資料夾與 `pc-control` 的相對位置。

**先閱讀 [安裝部署與場景建置](docs/安裝部署與場景建置.md)**，含程式包來源、Windows 安裝、Unreal 編譯、自建物理場景與疑難排解。

山坡果園原型：雙擊 `Start-Orchard.cmd` 開啟 100 × 100 公尺坡地、64 棵果樹與 4 隻活動獼猴替身。建置、驗證及限制見 [山坡柑橘果園原型](docs/山坡柑橘果園原型.md)。目前為幾何原型，尚非寫實或實測場地。

## 導入範圍

```text
既有 PC 航線內容 / mission_intelligence 圍欄及地形資料
    → WGS84 CSV → mission.py 檢查及局部 NED 轉換
    → fly.py → localhost:41451 AirSim RPC
    → SimpleFlight → Unreal 物理場景、碰撞、相機、遙測
```

| 既有功能 | 本包導入方式 |
|---|---|
| 緯度,經度,相對高度 CSV | 原格式直接讀入（無標題列；支援 # 註解） |
| 圓形圍欄、地形淨空分析 | 重用現有 `MissionDatabase` / `route_report` |
| DJI 航點上傳與執行 | 以 AirSim `moveToPositionAsync` 取代執行後端 |
| 起飛、返航、降落 | 新增模擬專用自動流程 |
| PC GUI、8765 協定、ADB、LoRa | 未接到 AirSim；請用本包 CLI，不要把原 GUI 當作 AirSim 控制端 |
| DJI H.264 影像、熱像、MSX | 不移植；提供 AirSim RGB PNG 擷取，沒有校正熱像溫度 |
| 避障 AI / DJI 真機飛控 | 本包不模擬 DJI 韌體或提供 AI 避障；碰撞後中止屬事故偵測 |

MavicSim 只是模擬機名稱，物理模型是 AirSim 通用多旋翼，沒有校準為 Mavic 2 Enterprise Dual。這是航點演算法仿真，不能據此聲稱真機飛行已驗收。

## 第一次仿真飛行：指令集

全部從 `D:\ResearchCodes\Mavic2Autonomy` 執行。安裝及啟動場景依部署文件完成。

```powershell
# 1. 不需要 AirSim 的離線檢查（本包已附 square.csv）
py -3.10 .\airsim-autonomy\fly.py check

# 2. 場景啟動後確認機體及 Home
.\airsim-autonomy\.venv\Scripts\python.exe .\airsim-autonomy\fly.py status

# 3. 確認場景路線空曠，執行：起飛 → 爬升 10m → 4 點 → 返回 → 降落
.\airsim-autonomy\.venv\Scripts\python.exe .\airsim-autonomy\fly.py fly --speed 1

# 4. 擷取目前相機 RGB 圖（飛行前後或另一終端執行）
.\airsim-autonomy\.venv\Scripts\python.exe .\airsim-autonomy\fly.py image

# 5. 中止：在執行飛行的終端按 Ctrl+C，程式會嘗試取消任務與懸停
# 等原飛行程序結束後，明確執行原地降落；再次飛行請重啟場景
.\airsim-autonomy\.venv\Scripts\python.exe .\airsim-autonomy\fly.py land
```

正常完成應顯示 `Completed`，日誌最後有 `landed` 與 `complete`。若 Ctrl+C、碰撞、越界或逾時，程式回傳非零狀態並嘗試懸停；連線中斷時無法保證命令送達。保持 API 控制以便後續 `land`；不會在空中直接停槳。不要同時啟動兩個 `fly` 或在飛行程序仍執行時用另一程序 `land`。

## 將自己的任務導入

1. 在原 PC 工具規劃航線，將航線文字儲存到 `airsim-autonomy/routes/my-mission.csv`。內容為 `緯度,經度,相對起飛點高度`，不要加入欄名。
2. 將 `config/settings.json` 的 OriginGeopoint 設為該航線的預定 Home。高度 Altitude 是原點海拔；CSV 高度則相對起飛點，兩者不同。
3. 重啟 AirSim、執行 status，確認 Home。此包要求 MavicSim 的初始 X/Y/Z 為 0、落地且在出生點 2m 以內；不支援空中接續任務。
4. 檢查並執行：

```powershell
py -3.10 .\airsim-autonomy\fly.py check --route .\airsim-autonomy\routes\my-mission.csv
.\airsim-autonomy\.venv\Scripts\python.exe .\airsim-autonomy\fly.py fly --route .\airsim-autonomy\routes\my-mission.csv --speed 1
```

要在新 Home 產生小方形，可使用不重複的新檔名（已有檔案會拒絕覆寫）：

```powershell
py -3.10 .\airsim-autonomy\fly.py generate --route .\airsim-autonomy\routes\new-home.csv
```

沿用既有圍欄 JSON / 地形 CSV 的範例（檔案需自行匯入）：

```powershell
py -3.10 .\airsim-autonomy\fly.py check --route .\airsim-autonomy\routes\my-mission.csv --fences .\airsim-autonomy\config\fences.json --terrain .\airsim-autonomy\config\terrain.csv --home-elevation 30
```

正式 `fly` 也必須傳入相同 `--fences`、`--terrain` 與 `--home-elevation`，才會執行同一檢查。圍欄格式沿用 `{ "source":"survey", "updatedAt":"2026-10-16", "zones":[{"name":"building", "lat":25.0, "lon":121.0, "radiusM":5}] }`；地形 CSV 欄名為 `lat,lon,elevation_m`，海拔基準需與 Home 一致。未指定外部資料時只有幾何界限檢查，不能推論路徑淨空。

原模組以約 5m 間隔取樣、地形取鄰近資料，這是粗略檢查，可能漏掉小障礙或稀疏資料中的起伏。進場、航點段及返航水平路線也納入檢查，但起降垂直柱狀空域仍須在場景確認。飛行器每段直線移動，返航沿最後高度直線回出生點，沒有繞障規劃。

## 座標與執行規則

- NED：X 北、Y 東、Z 下，單位 m；CSV +10m 對應 Z=-10m。WGS84 使用 100m 範圍內的局部切平面近似，非長距離地圖投影。
- 保留專案幾何規則：2–20 點、高度 5–30m、半徑 100m、首點距 Home ≤30m、相鄰水平 ≥2m、航點間累積距離 ≤500m；速度 (0,2]m/s。
- 500m 不含起飛進場及返航。飛行中容許追蹤誤差，超出半徑 105m 或高度 32m 會中止。
- 每段位置誤差 ≤0.75m 算抵達，不保證每點停穩；約 5Hz 記錄位置與碰撞，RPC 等待會影響實際頻率。
- `logs/*.jsonl` 記錄 UTC、模擬 timestamp、NED、階段及錯誤；PNG 也在 logs。
- 固定單機 localhost:41451、MavicSim、ClockSpeed=1。自訂 settings 也需保持這些值；程式不提供遠端 DJI 通道。

## 驗收順序與交付狀態

1. 離線單元測試：座標方向、無效數值、路線界限、圍欄、成功與失敗的飛行控制流程。
2. Python 相依套件可安裝、`import airsim` 成功。
3. 場景啟動、status、影像、單次起飛與降落。
4. 空曠路徑四點飛行，確認回出生點落地與 complete 日誌。
5. 障礙碰撞、Ctrl+C 與場景關閉測試，確認錯誤不被報成成功。
6. 最後才導入自己的場地、路線與圍欄。

```powershell
py -3.10 -m unittest discover -s .\airsim-autonomy\tests -v
```

實際已完成的驗證見 [驗證紀錄](docs/驗證紀錄.md)。模擬場景、UE 編譯、安裝程式與套件下載不包含在原始碼包中，由腳本／官方來源取得。

API 參考：[AirSim API](https://microsoft.github.io/AirSim/apis/)、[固定版本 Python Client](https://github.com/microsoft/AirSim/blob/v1.8.1-windows/PythonClient/airsim/client.py)。


2026/10/18 AM 10:30
===================
建議採用 「同一份航線，先在 AirSim 驗證，再透過 DJI SDK 執行實機任務」。
目前 fly.py 只能控制 AirSim，尚未把 UE4 與實體 DJI 連接起來。另外，我檢查到你的 Android 程式目前只允許 Mavic 2 Enterprise Dual；如果實機是 Mavic 2 Pro 或 Zoom，需要先調整相容性。
1．剛才驗證的修改與結果
起飛逾時的原因是：
起飛前 NED Z：約 +0.91 m
起飛後 NED Z：約 -0.63 m
實際上升：約 1.54 m
原本程式要求 Z < -1，因此雖然飛機離地，仍判定逾時。現在改成：
起飛前的 Z - 目前的 Z >= 1.0
驗證結果：
- 16 項測試通過。
- 實際通過起飛、爬升、四個航點及返航。
- 降落尚未完整通過：接地後 SimpleFlight 可能仍回報 Flying。不能把這次驗證視為完整任務成功。
相關程式：[fly.py](C:/Users/wangs/Mavic2Autonomy/airsim-autonomy/fly.py)、[測試程式](C:/Users/wangs/Mavic2Autonomy/airsim-autonomy/tests/test_mission.py)。
2．重現模擬驗證的指令集
以下全部從這個目錄執行：
Set-Location C:\Users\wangs\Mavic2Autonomy

$python = ".\airsim-autonomy\.venv\Scripts\python.exe"
$settings = ".\airsim-autonomy\config\settings-mavic2.json"
$route = ".\airsim-autonomy\routes\my-mission.csv"
先關閉舊模擬視窗，再啟動修正版：
.\airsim-autonomy\scripts\Start-Mavic2.ps1
執行測試與航線檢查：
# 離線測試
& $python -m unittest discover -s .\airsim-autonomy\tests -v

# 航線格式、範圍等檢查
& $python .\airsim-autonomy\fly.py check `
  --settings $settings --route $route --speed 1
確認目前模擬狀態：
& $python .\airsim-autonomy\fly.py status --settings $settings
應確認 landed_state 為 0，且機體在出生點附近，再執行：
& $python .\airsim-autonomy\fly.py fly `
  --settings $settings --route $route --speed 1
可在另一個 PowerShell 視窗查詢狀態、擷取相機：
.\airsim-autonomy\.venv\Scripts\python.exe `
  .\airsim-autonomy\fly.py status `
  --settings .\airsim-autonomy\config\settings-mavic2.json

.\airsim-autonomy\.venv\Scripts\python.exe `
  .\airsim-autonomy\fly.py image `
  --settings .\airsim-autonomy\config\settings-mavic2.json
影像及飛行紀錄存於：
C:\Users\wangs\Mavic2Autonomy\airsim-autonomy\logs
中止時，在飛行指令所在終端按 Ctrl+C，程式會嘗試取消任務並懸停。等原程序結束後，才能另下降落命令：
& $python .\airsim-autonomy\fly.py land --settings $settings
目前降落指令仍可能因落地旗標問題逾時。 再測新任務時，關閉模擬視窗並重新啟動，不要在空中重複執行 fly。
3．如何在模擬器中改變飛行路線
目前航線由 CSV 決定，每列為：
緯度,經度,高度
你的四點航線是：
25.000044966,121.000000000,10.0
25.000044966,121.000148844,10.0
25.000179864,121.000148844,10.0
25.000179864,121.000000000,10.0
相對於設定中的 Home 25.0, 121.0，大致對應：
航點	北向距離	東向距離	目前 AirSim 目標 Z
1	5 m	0 m	−10 m
2	5 m	15 m	−10 m
3	20 m	15 m	−10 m
4	20 m	0 m	−10 m


操作流程是：
1. 編輯 CSV。
2. 執行 check。
3. 從全新場景執行 fly。
4. 查看軌跡、碰撞與日誌。
兩點需要留意：
- 修改 OriginGeopoint 只會改變經緯度對應，不會讓 Blocks 場景變成該處的真實地形。
- 現在 CSV 高度直接轉為 NED Z；由於落地位置有約 +0.91 m 偏移，Z=-10 不等於精確離地 10 公尺。實機移轉前要統一「起飛點相對高度」的定義。
4．你的實機串接架構
你已有的程式可作為串接基礎：
PC 航線控制程式
        │ USB ADB 或私人區域網路
        ▼
Smart Controller 上的 Android App
        │ DJI Mobile SDK
        ▼
DJI 遙控器鏈路
        ▼
實體 Mavic 2
我查到目前專案的實作如下：
部分	現況
PC 入口	pc-control/mavic_pc_control.py
Android SDK	DJI Mobile SDK 4.18
控制通道	TCP 8765
影像通道	TCP 8766
實機型號限制	MAVIC_2_ENTERPRISE_DUAL
UE4／AirSim 整合	尚未接入上述 PC 控制介面


DJI 官方文件列有 Mavic 2 系列的 Mobile SDK 支援，但官方支援某型號，不代表你現有 App 已支援它。DJI 產品支援文件
5．如果你的實機是 Enterprise Dual＋Smart Controller
先使用現有 App 做連線驗證，不必立即改 AirSim。
準備 PC 環境：
Set-Location C:\Users\wangs\Mavic2Autonomy

.\airsim-autonomy\.venv\Scripts\python.exe -m pip install `
  -r .\pc-control\requirements.txt

# 影像解碼使用；需另外安裝並加入 PATH
ffmpeg -version
啟動 PC 控制介面：
.\airsim-autonomy\.venv\Scripts\python.exe `
  .\pc-control\mavic_pc_control.py
接著：
1. Smart Controller 開啟 USB 偵錯，接受電腦授權。
2. 用資料線連接電腦。
3. 完全退出會占用 DJI 連線的其他 App，開啟「Mavic 2 自主航點」。
4. PC 按「連接 USB」。
5. 輸入控制器顯示的六位驗證碼。
6. 在控制器授權本次前景工作階段接受 PC 控制。
7. 先確認型號、連線、GPS、Home、電池及相機回報。
PC 的「連接 USB」已包含這些 ADB 動作，手動診斷時才需要：
adb devices
adb forward tcp:8765 tcp:8765
adb forward tcp:8766 tcp:8766
adb shell am start -n com.example.mavic2autonomy/.MainActivity
現有操作說明：[PC 控制端文件](C:/Users/wangs/Mavic2Autonomy/pc-control/README_繁體中文.md)。
6．先區分兩種「模擬器」
模式	實際控制對象	是否需要 DJI 硬體
UE4／AirSim	SimpleFlight 虛擬飛行器	不需要
App 的 SIMULATOR	DJI SDK 提供的模擬功能	依目前實作需要連接 DJI 飛控
App 的 OUTDOOR	實體飛行器	需要


PC 介面選擇 SIMULATOR，並不會連到目前 UE4 場景。
你現有專案的 DJI 模擬操作要求拆槳，並由 SDK 確認模擬器已啟動；不能僅憑 PC 下拉選單判定模式。這部分的硬體驗收仍需完成。[專案模擬操作說明](C:/Users/wangs/Mavic2Autonomy/docs/模擬工作階段-0.2.15.md)
7．接下來如何讓模擬航線用於實機
建議分成三步：
1. 共用航線資料
   AirSim 與 Android App 讀取同一份經緯度航線，各自透過自己的控制介面執行。實機航線必須以實際場地與起飛點重新確認，不能直接使用示範座標 25.0, 121.0。
2. 先做 DJI 模擬驗證，再執行實機任務
   驗證航線載入、上傳、狀態回報、暫停、終止與失聯行為。DJI 的航點任務有自己的載入／上傳／執行流程，不能直接呼叫 AirSim 的 moveToPositionAsync 控制真機。DJI 任務文件
3. 最後加入 UE4 遙測顯示
   將實機經緯度、高度與姿態傳回 PC，在 UE4 顯示實機位置。這個階段讓 UE4 作為監看畫面，避免把模擬器的馬達轉速直接送往真機。
