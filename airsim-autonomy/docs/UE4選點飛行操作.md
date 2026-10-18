# Mavic 2／UE4 果園原型 v1 選點飛行操作手冊

更新日期：2026-10-18｜文件修訂：果園 v1 手冊同步版｜適用執行包：Mavic2Simulator-Orchard-v1-20261018.zip

本手冊適用於目前已完成的「UE4 選點 → 顯示目標與高度 → Enter 確認 → 模擬機飛到目標」功能。所有飛行操作皆作用於 AirSim 的 MavicSim；不需要開啟實體飛行器或 Smart Controller。

## 1. 功能與使用環境

| 項目 | 目前狀態 |
|---|---|
| UE4 俯視選點、座標預覽、設定高度 | 已提供 |
| 模擬起飛、單點飛行、到點懸停、取消 | 已提供 |
| 到點後繼續選下一點 | 已提供，逐點確認 |
| 一次排入多個點／儲存選點航線 | 尚未提供 |
| 自動避障、繞障、選點模式自動降落 | 尚未提供 |
| 室內真機自動到點 | 尚未提供；缺少場地定位整合 |
| 戶外 GPS 選點控制 | 保留獨立選項，尚未接入 |

本機專案資料夾：`C:\Users\wangs\Mavic2Autonomy\airsim-autonomy`。

可攜執行包已包含遊戲與控制程式，不需安裝 UE4 編輯器、Visual Studio 或 Python。來源專案開發方式則使用已安裝的 UE4.27、修改後的 Blocks 專案及 `.venv`；兩種啟動方式見下一節。日常操作不需要重新編譯。

### 果園原型內容

| 項目 | 說明 |
|---|---|
| 地形 | 100 × 100 公尺合成坡地，最高處約高於平地 12 公尺 |
| 果樹 | 64 棵，幾何樹冠、果實及灌木，中央農路 |
| 獼猴 | 4 隻幾何替身，按固定路徑移動及停留 |
| 起降區 | 西側 10 × 10 公尺平台 |
| 碰撞 | 地形、樹幹及平台有碰撞；樹冠、果實、灌木及獼猴替身無碰撞 |
| 俯視選點 | 起點附近寬約 30 公尺視野；不是全果園導覽 |

原型不是實測場地或寫實模型，尚未接入獼猴辨識、追蹤、爬樹或對飛行器反應。果園是戶外外觀的模擬場景，不代表已完成戶外 GPS 真機控制。

### 三種畫面的差別

| 畫面／工具 | 用途 | 是否控制 UE4 模擬機 |
|---|---|---|
| 導航功能入口 | 選擇並開啟工具 | 透過「啟動 UE4 選點飛行」啟動控制程式 |
| 選點模式的 UE4 俯視畫面 | 點選目標、調高度及確認飛行 | 是 |
| OFFLINE UI DEMO 雙搖桿 | 獨立的介面示範 | 否；也不連真機 |

DJI SDK 模擬器是另一套系統，不等於 AirSim 或 OFFLINE UI DEMO。本次不需要啟動 DJI 模擬器。

## 2. 啟動與場景切換

### 方式 A：可攜執行包（一般使用者建議）

1. 完整解壓 `Mavic2Simulator-Orchard-v1-20261018.zip` 到可寫入資料夾，例如 `D:\Mavic2Simulator`，不要直接從 ZIP 執行。
2. 若尚未安裝必要元件，執行包內 `Simulator\Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe`；可能需要管理員權限。
3. 可先雙擊 `Check-Runtime.cmd`，確認出現 Runtime OK、AirSim import OK。這只檢查控制程式套件，不代表場景驗收完成。
4. 關閉其他 UE4／AirSim 場景，再雙擊下表的啟動檔。
5. 保留控制終端，等 UE4 出現 READY 後開始選點。

| 包內啟動檔 | 開啟內容 |
|---|---|
| Start-Orchard.cmd | 果園原型＋點選飛行 |
| Start-Navigation.cmd | 與 Start-Orchard.cmd 相同，預設果園 |
| Start-Blocks.cmd | 原 Blocks 場景＋點選飛行 |

**切換場景：**先按 X，確認停止移動，關閉目前 UE4 並等控制終端退出，再開另一個啟動檔。不能在飛行中直接切換。不要單獨雙擊 Blocks.exe，否則沒有選點控制程式。

Windows 若顯示 Blocks 防火牆提示，本版只使用本機 localhost，可由操作員選「取消」，不需開放公用網路。此包不自動修改系統安全設定。

### 方式 B：來源專案啟動果園選點（開發者）

關閉舊 UE4 場景及正在執行的 `fly.py` 任務，再執行：

```powershell
Set-Location C:\Users\wangs\Mavic2Autonomy\airsim-autonomy
.\.venv\Scripts\python.exe .\point_navigation.py --scene Orchard
```

程式會開啟帶選點功能的 UE4，顯示俯視畫面。等左上角顯示 READY 再操作。不要另跑 `fly.py fly`，兩個控制程式會互相干擾。

請保留執行這個指令的 PowerShell 視窗，控制程式會持續運作。不要把另一個程式的輸出或 `(base) PS ...>` 提示字元一起貼進指令。

改用 `--scene Blocks` 可開啟原場景；省略 --scene 時也是 Blocks。來源專案根目錄的 Start-Orchard.cmd 只開啟一般果園遊玩模式；與可攜包內同名檔案的「果園選點」用途不同。

### 來源專案既有導航入口

```powershell
Set-Location C:\Users\wangs\Mavic2Autonomy\airsim-autonomy
.\.venv\Scripts\python.exe .\navigation_console.py
```

1. 選擇「室內：無可靠 GPS（優先開發）」。
2. 按「啟動 UE4 選點飛行（先關閉舊 UE4 視窗）」。
3. 等待新開啟的控制終端與 UE4；看到 READY 才操作。

一般「開啟現有 UE4 / AirSim 場景」只啟動普通場景，沒有選點功能。若先按了這個按鈕，關閉該 UE4 後再啟動選點飛行。不要連按啟動按鈕；同時只能有一個場景使用 41451 連接埠。

關閉導航入口不等於停止已開啟的選點飛行程式；請依本手冊的結束流程操作。

目前來源專案的導航入口沒有果園選單，其「啟動 UE4 選點飛行」仍開啟預設 Blocks。要開果園選點，請使用上方 --scene Orchard 指令或可攜包的 Start-Orchard.cmd。

## 3. 選點與飛行

1. 在俯視畫面的空曠地面按一下左鍵。出現黃色標記與 Selected N/E，代表選點成功。
2. 上／下方向鍵調整高度，每次 0.5 公尺，範圍 1–10 公尺，預設 2 公尺。
3. 確認目標與高度後按 Enter。落地時先自動起飛，再調整高度，最後沿水平直線接近目標。
4. 顯示 ARRIVED 表示位置誤差進入 0.75 公尺容差，已送出懸停命令。可再次選點、調高度及按 Enter。
5. X 取消目前任務並要求懸停。執行途中按 Enter 的新目標會被忽略，沒有排隊與重播。
6. 結束測試可關閉 UE4；終端 Ctrl+C 會嘗試取消與懸停。這不是降落；本版不自動降落。需全新起點時關閉場景再重新啟動。

### 第一次操作範例

果園首次測試請留在起降平台附近：按兩次 ↑，將預設高度 2 公尺調為 3 公尺，在距離模型約 2–3 公尺的平台空曠處選點，例如 N/E 接近 2/2 公尺的位置。確認看到黃色標記及 Selected N/E/H；如果沒有看到標記，先讓 UE4 視窗取得焦點，再點一次。按 Enter 一次，觀察 TAKEOFF → HEIGHT → MOVING → ARRIVED。此範例不代表全果園或穿越果樹路線已驗收。

ARRIVED 後再選第二個附近點並按 Enter。要測試中止，在飛行途中按 X，確認出現 CANCELLED，並觀察飛機減速。X 是取消後送出懸停請求，不會瞬間停止，也不會降落或停槳。

### 按鍵速查

| 操作 | 結果 |
|---|---|
| 左鍵點地面並放開 | 更新黃色預覽點，不會立即起飛 |
| ↑ | 預覽高度增加 0.5 公尺 |
| ↓ | 預覽高度減少 0.5 公尺 |
| Enter | 執行目前預覽的點與高度；落地時會自動起飛 |
| X | 中止目前控制任務並要求懸停 |
| 控制終端 Ctrl+C | 結束橋接程式，嘗試取消及懸停 |

飛行途中調整預覽點或高度不會改寫已送出的目標。執行中的新 Enter 指令會被忽略；需等待 ARRIVED，或先按 X，再確認新目標。

## 4. 畫面狀態說明

| 顯示文字 | 意義／下一步 |
|---|---|
| READY | 已連線、取得初始高度，可選點 |
| Selected N / E / H | 尚待確認的目標位置與高度 |
| COMMAND | 已收到操作指令，不代表飛行已完成 |
| TAKEOFF | 正在起飛 |
| HEIGHT | 正在目前水平位置調整高度 |
| MOVING | 正在接近目標 |
| ARRIVED within 0.75 m | 進入三維位置容差，已送出懸停命令 |
| BUSY | 已有任務，新目標被忽略 |
| CANCELLED | 已收到中止操作並要求懸停 |
| STOPPED | 碰撞、逾時、越界或指令錯誤；讀取後方原因 |

黃色標記是預覽目的地，並非實際飛機位置。ARRIVED 代表達到目前的判定容差，不代表精確停在標記中心。上方顯示的高度是設定值，不能當作實測高度。

## 5. 結束與重新開始

正常結束：先在 UE4 按 X，確認飛行已停止移動，再關閉 UE4。控制終端在偵測到場景結束後會退出。

若在控制終端按 Ctrl+C，UE4 可能仍開著；請確認場景狀態，再關閉 UE4。要開始新工作階段，可攜版重新執行 Start-Orchard.cmd；來源版重新執行 `point_navigation.py --scene Orchard`，不可直接沿用舊場景。取消／懸停請求需要 AirSim 連線正常才能送達。

本版沒有選點模式降落按鍵。既有 `fly.py land` 曾出現落地狀態逾時，這個問題尚未修正；不要在選點控制程式執行時另啟動 `fly.py land` 或 `fly.py fly`。

## 6. 座標與限制

- N 向北／UE X、E 向東／UE Y，以公尺表示。限定 MavicSim 出生設定 X/Y/Z=0，因此 global 與 vehicle-local NED 的 XY 一致。
- 高度是相對啟動時模型落地後機體位置的上升量，不是出生 NED 零點、海拔或點擊表面的離地高度；地面不平時不代表固定淨空。
- 點擊只決定 XY；點屋頂也不會自動將高度加到屋頂上方。請先在起點附近空地測試。
- 速度固定 0.5 m/s，目標水平半徑限制 20 公尺，俯視範圍寬 30 公尺。
- 此版採直線分段飛行，沒有障礙物繞行。碰撞檢測是碰撞後中止，不是預先避障。
- 新增合成果園，同時保留 Blocks；尚未建立實際場地測繪模型。
- 沒有連接 Smart Controller／DJI APP，也沒有使用 GPS 控制真機。戶外功能維持獨立、待開發。

果園 PlayerStart 的 UE 世界位置是 (-3600, 0, 45) 公分；選點顯示的 N/E 是相對出生原點的公尺座標，不是以整個果園的世界中心為零。不要把 UE 世界公分直接當成 N/E 公尺輸入。

例如果園啟動落地後若 D 約 +0.25 公尺，設定 H=3 公尺，目標 D 約為 −2.75 公尺；實際值由本次啟動讀取。舊 Blocks 的落地 D 曾約 +0.919，不能硬套到果園。上坡地面升高時，同一設定高度的淨空會變小，甚至可能低於地面；本版不會自動提高高度。

## 7. 常見問題

| 問題 | 處理方式 |
|---|---|
| `port 41451 in use` | 關閉已開啟的 UE4／AirSim，等它完全退出，再啟動一次 |
| 只有原本的低角度畫面，沒有選點提示 | 可攜版使用 Start-Orchard.cmd；來源版使用 `point_navigation.py --scene Orchard` |
| 開啟後仍是 Blocks | 確認執行的是新版可攜包 Start-Orchard.cmd，而非舊包；來源版須明確加 --scene Orchard |
| 看不到整個果園或四隻獼猴 | 俯視選點視野只涵蓋起點附近，動物可能位於視野外；目前沒有全景導覽或追蹤按鈕 |
| 點上坡後碰撞或飛得太低 | 高度相對起飛位置，未跟隨地形；重開後先在平台空地測試 |
| 按搖桿示範的 TAKEOFF，UE4 沒反應 | 該視窗是獨立示範；改在選點版 UE4 選地面並按 Enter |
| 點擊後沒有黃色標記 | 讓 UE4 取得焦點，點附近可見的平坦地面；牆面或未命中可碰撞表面不會選取 |
| 方向鍵或 Enter 沒反應 | 先切換到 UE4 視窗，再操作；不要把按鍵送到終端 |
| `Target outside limit` | 重新選半徑 20 公尺內的點，高度保持 1–10 公尺 |
| `Start a fresh scene` | 關閉舊場景，從新場景的地面起點重新開始 |
| `Collision detected` | 已發生碰撞；結束該次場景，重開後選空曠且路徑無障礙的位置 |
| `timed out` | 該階段未在期限內達標，查看場景及終端原因；重開場景再測試附近目標 |
| `UE4 did not start AirSim within 90 seconds` | 檢查錯誤視窗；可攜版先做套件校驗、確認必要元件與顯示卡驅動；來源版另檢查引擎與 DLL |
| 找不到 Python 或腳本 | 可攜版不需 Python，請直接用 cmd；來源版確認工作目錄與 `.venv` |
| 戶外或真機按鈕不能按 | 目前未提供，不是漏填驗證碼或連線錯誤 |

如仍失敗，保留終端錯誤及本次 `events.jsonl`，不要只依畫面中「API call was not received」這一行判斷任務成敗；請一併查看本程式的階段訊息。

## 8. 記錄與驗證

2026-10-18 果園可攜版驗證：建置成功、22 項 Python 測試通過；搬移至中文／空白路徑後，四隻獼猴在約六秒內移動約 0.87–2.51 公尺，RGB 果園畫面成功擷取。透過共用指令檔測試平台附近 N=2、E=2、H=3 公尺到點，以及第二段飛行取消，取消後速度約 0.047 m/s。詳細資料見包內「果園可攜版驗證記錄.md」。

原 Blocks 開發版曾以實際滑鼠驗證選點、Enter 及 X；本次果園獨立版沒有重做滑鼠端測試，而是以指令檔驗證控制。這是同一台電腦的路徑搬移驗證，不是另一台乾淨電腦、全果園巡航或精密室內定位驗收。

UE4 `Source/Blocks/NavigationPicker.*` 負責滑鼠射線選取、預覽與指令；`point_navigation.py` 負責 localhost:41451 的 AirSim 控制。每次啟動使用獨立 `logs/point-<隨機ID>/`，其中 `events.jsonl` 記錄指令與階段，舊工作階段不會重新執行。

可攜版已將選點模組編入 Blocks.exe，異地一般操作只需完整解壓並依第 2 節啟動；只有要修改／重建場景時才需要開發環境。單獨的 FBX 模型備份不包含選點功能。

可攜版記錄在包內 `Controller/logs/point-<隨機ID>/events.jsonl`，來源版則在專案 `logs/point-<隨機ID>/events.jsonl`。

查看可攜版最新工作階段記錄（在解壓後的包根目錄開啟 PowerShell）：

```powershell
$latestLog = Get-ChildItem .\Controller\logs\point-*\events.jsonl |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($latestLog) { Get-Content -LiteralPath $latestLog.FullName -Encoding UTF8 }
```

`events.jsonl` 記錄指令與階段，不是完整的連續飛行遙測或錄影。請勿在運作中編輯 `command.json`；它是控制程式與 UE4 的指令檔。

## 9. 維護與異地安裝注意事項

可攜版在包根目錄執行以下指令即可檢查完整性；修改設定或文件後雜湊不一致是預期結果，請勿混用不同版本的校驗清單。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1
```

更新包建議解壓到新資料夾，驗收後再改用新入口。不要覆蓋正在執行的舊包，舊 logs 可另行保存。文件更新後也必須重新產生 SHA256SUMS.json 與 ZIP 雜湊，本次已同步處理。

以下供開發維護使用，日常選點操作不需要執行。編譯前關閉 UE4，並先切換到本專案資料夾。

```powershell
& 'C:\Program Files\Epic Games\UE_4.27\Engine\Build\BatchFiles\Build.bat' BlocksEditor Win64 Development "-Project=$PWD\vendor\AirSim\Unreal\Environments\Blocks\Blocks.uproject" -WaitMutex -NoHotReloadFromIDE
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
