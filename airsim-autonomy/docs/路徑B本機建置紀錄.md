# 路徑 B 本機建置紀錄

查核日期：2026-10-17（台北時間）。已完成 AirSim C++、UE BlocksEditor 編譯及 Editor Play／RPC 驗收。

## 2026-10-17 最終驗收

- UE 4.27.2 安裝於 `C:\Program Files\Epic Games\UE_4.27`，Build.version changelist 18319896。
- 直接呼叫引擎的 `UnrealBuildTool.exe -projectfiles` 成功產生 Blocks.sln，不依賴 Launcher 安裝清單或 `.uproject` 登錄項。
- BlocksEditor / Development / Win64：使用 VS 2022 14.44、Windows SDK 10.0.26100.0，11 項建置工作成功，結束碼 0；已產生 UE4Editor-Blocks.dll 與 UE4Editor-AirSim.dll。
- 以本專案 config/settings.json 啟動編輯器，在 FlyingExampleMap 執行 Play；確認遊戲模式為 AirSimGameMode。
- RPC 監聽 127.0.0.1:41451，程序為本次 UE4Editor；fly.py status 回傳 MavicSim、Home [25,121]、NED 約 [0,0,0.68]、landed_state=0。Z 偏移為出生後落至地面的結果，並非起點正好位於地面。
- 已於場景 Saved/Config/Windows/EditorSettings.ini 設定 bThrottleCPUWhenNotForeground=False。
- 驗收涵蓋場景載入與 RPC 狀態讀取，未執行完整航點任務或打包。

### 本次修正

1. Launcher「＋／安裝引擎」無反應：退出 Launcher，把 webcache_4430 改名備份後重新啟動，使用者確認恢復並完成引擎安裝。
2. 跳過 SUV 雖不影響 C++ 建置，但 Editor 載入時仍出現 7 個材質缺失。已下載官方 v1.2.0/car_assets.zip，將 SUV 目錄補入上游 plugin 及 Blocks plugin，重啟後缺失訊息消除。
3. Blocks 的 Config/DefaultEngine.ini 含過期的 MinimumiOSVersion=IOS_11，造成 LoadConfig 錯誤；已移除該覆寫，使用引擎預設值。這是本次唯一修改的上游受追蹤檔案。
4. 編譯時 Shell32.lib、dinput8.lib、dxguid.lib 路徑提示與新版 MSVC 提示並未導致失敗；實際連結完成，不必因此更換工具鏈。

重建場景：在專案目錄執行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Build-Blocks.ps1`。此腳本直接使用引擎工具，不會執行上游場景 clean.bat。

證據：logs/blocks-projectfiles.log、logs/blocks-build.log、logs/blocks-editor-status.json，以及場景 Saved/Logs/Blocks.log。

以下為 2026-10-16 的前置建置紀錄；「待完成」項目已於上述驗收完成。

## 已完成

- 原始碼：`vendor/AirSim`，commit `96235148a332fe7cb3d3525a0720e26faaca99e0`，同時對應 `v1.8.1` 和 `v1.8.1-windows`；沒有修改上游受追蹤原始碼。
- 工具：既有 VS 2022 Build Tools 17.14、MSVC 14.44、Windows SDK 10.0.19041.0、VS 隨附 CMake 3.31.6。另有 v142 工具集 14.29。
- 必要依賴：rpclib 2.3.0、Eigen 3.3.7；Eigen 從官方 GitLab tag 壓縮檔取得。
- AirSim solution：Debug 0 警告／0 錯誤；Release 3 警告／0 錯誤。
- AirLib、rpc、MavLinkCom 的 Debug／Release 靜態程式庫已同步至 Blocks 的 plugin。
- Epic Games Launcher 已安裝並啟動；引擎安裝清單仍為空。

## 問題與處理

| 問題 | 原因／處理 | 狀態 |
|---|---|---|
| 初次 `vswhere -all` 只列出 VS 2019 | Build Tools 需使用 `-products *` 查詢；已找到可用 VS 2022，無需重裝 | 已處理 |
| 預設 CMake 位於 MSYS2 | 建置入口優先使用 VS 隨附 Windows 版 CMake，避免產生器混用 | 已處理 |
| 選用 SUV 素材下載慢 | 使用上游支援的 `--no-full-poly-car`；不影響無人機建置 | 已處理 |
| CMake 最低版本棄用警告 | 舊 rpclib 的 CMake 宣告所致；此次仍成功產生與編譯，無需升級依賴 | 非阻塞 |
| Release 的 3 個 C4100 警告 | 上游 AirLibUnitTests 編譯涉及 `last_interval`、`connection`、`err` 未使用參數；不影響產物生成，保留原版程式碼 | 非阻塞 |
| 找不到 `HKEY_CLASSES_ROOT\Unreal.ProjectFile\shell\rungenproj`，接著顯示 `'/projectfiles' is not recognized` | 尚無 UE 引擎／UnrealVersionSelector 專案關聯，官方腳本取得的執行檔路徑為空 | 待安裝 UE 4.27.2 |
| 上述失敗仍回傳 0 | 官方最外層 `build.cmd` 未檢查產生專案結果；本機入口新增 Blocks.sln 缺失檢查，缺少時回傳 2 | 已補防誤判檢查 |

## 待完成

1. 使用者在 Epic Games Launcher 登入，於 Unreal Engine → Library 安裝 **4.27.2**；建議路徑 `C:\Program Files\Epic Games\UE_4.27`。
2. 註冊 `.uproject` 關聯並產生 `vendor/AirSim/Unreal/Environments/Blocks/Blocks.sln`。若引擎安裝後登錄項仍缺失，可直接使用該引擎的 UnrealBuildTool 產生專案，避免依賴上述登錄項。
3. 編譯 BlocksEditor／Development／Win64，確認 Editor DLL 生成與載入成功。
4. 以本專案 `config/settings.json` 啟動 UE4Editor，停用背景降速並按 Play。
5. 執行 `.venv\Scripts\python.exe fly.py status`，驗證 MavicSim、地理原點與 RPC；目前沒有把預編譯 Blocks 的結果當成本次源碼建置驗收。

## 證據與重跑

- 完整建置記錄：`logs/build-airsim.log`。
- 初次下載中止記錄：`logs/build-airsim-first-attempt.log`。
- 程式庫同步 SHA256 比對：`logs/build-airsim-artifacts.json`。
- 本機建置入口：專案目錄下執行 `cmd /d /c scripts\Build-AirSim.cmd`。此入口固定目前機器的 Build Tools 路徑；官方流程會清除 Blocks 的 Saved 等生成資料，重跑前先保留需要的自動存檔。
- 尚未執行整組上游 AirLibUnitTests：其中 SimpleFlightTest 含無限迴圈，不能當成會正常結束的安裝驗收。

官方參考：https://microsoft.github.io/AirSim/build_windows/
