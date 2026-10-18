# Mavic 2 修正版模型：備份與異地安裝

本包為 UE4.27.2 / AirSim 1.8.1 的模型資產備份，包含機身、四組可旋轉槳葉、材質、藍圖、相機資產依賴、原始來源及重建腳本。不是獨立可執行遊戲，未包含 Unreal Engine、完整 AirSim 原始碼／DLL、Blocks 地圖或 Python 環境。

## 1. 在新電腦準備環境

1. 安裝 Unreal Engine **4.27.2**，避免直接使用 UE5 開啟後覆存。
2. 準備可正常開啟、按 Play 後能啟動原始無人機的 AirSim Unreal 專案。建議使用與來源相同的 **AirSim 1.8.1**。若從原始碼建置，需要 Visual Studio C++ 工具鏈與 Windows SDK，先依 AirSim 的 Windows 建置說明完成：<https://microsoft.github.io/AirSim/build_windows/>。
3. 本機參考環境使用 VS2022 Build Tools、Windows SDK 10.0.19041.0。此組合不是對所有 AirSim checkout 的相容保證；請依所用原始碼建置要求處理。可將原電腦完整的 `vendor/AirSim` 原始碼與專案另外移轉，再重新建置。不要把本包的 `AirSimContentDependencies` 當成完整插件。
4. 若只有下載版 `Blocks.exe`，不能直接放入 uasset 或 FBX 更換模型。須先取得可編輯的 `.uproject`，或由安裝完成的來源專案重新打包。
5. 在目標電腦先驗證原本 AirSim 能運作，再關閉 UE4。

## 2. 解壓縮與驗證

將備份 ZIP 複製到新電腦，例如解壓縮到：

```text
D:\Mavic2Backup\
```

解壓後資料夾內有 `Content`、`config`、`fbx`、`scripts`、`AirSimContentDependencies` 及 `SHA256SUMS.json`。

在此資料夾的 PowerShell 執行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Backup.ps1
```

應顯示所有清單內檔案校驗通過。ZIP 自身的 SHA-256 存在 ZIP 同層的 `.sha256.txt`，也可用 `Get-FileHash -Algorithm SHA256` 比對。

## 3. 安裝模型資產

假設目標專案為 `D:\UEProjects\Blocks\Blocks.uproject`。

1. 確認 UE4 已關閉，先備份目標專案。
2. 將備份內的 **`Content\Mavic2` 整個資料夾**複製到目標專案的 `Content`。若已有同名資料夾，先另存舊版本，再完整替換。
3. 結果必須是：

```text
D:\UEProjects\Blocks\Content\Mavic2\Blueprints\BP_Mavic2.uasset
D:\UEProjects\Blocks\Content\Mavic2\Meshes\SM_Mavic2_Body.uasset
D:\UEProjects\Blocks\Content\Mavic2\Meshes\SM_Mavic2_Rotor0.uasset
...
D:\UEProjects\Blocks\Content\Mavic2\Materials\M_Mavic2_Propeller.uasset
```

不要多包一層 `Content`，也不要更名 `Mavic2`，否則既有資產路徑失效。

4. `dependencies.json` 列出藍圖遞迴依賴。`/Engine` 由 UE4 提供；`/Script/AirSim` 由已編譯 AirSim 插件提供。
5. 正常 AirSim 1.8.1 已包含 `/AirSim` 資產。若目標版本有缺少或修改，可在備份原檔後，將 `AirSimContentDependencies\Content` 的內容，按相同相對路徑複製到目標的 **`Plugins\AirSim\Content`**。此處只有模型用到的依賴，不是整個插件。不要複製到專案的 `Content\AirSim`，兩者掛載路徑不同。

## 4. 使用設定啟動

把本包 `config\settings-mavic2.json` 複製到目標專案，例如：

```text
D:\UEProjects\Blocks\Config\settings-mavic2.json
```

用 PowerShell 啟動（依實際安裝路徑修改）：

```powershell
& 'C:\Program Files\Epic Games\UE_4.27\Engine\Binaries\Win64\UE4Editor.exe' `
  'D:\UEProjects\Blocks\Blocks.uproject' `
  '-settings=D:\UEProjects\Blocks\Config\settings-mavic2.json'
```

開啟後按 **Play**。若想直接開模擬視窗，在最後加上 `-game -windowed -ResX=1280 -ResY=720`。

此設定建立名為 **MavicSim** 的 SimpleFlight 無人機，RPC 使用本機 41451 連接埠。先關閉其他佔用該連接埠的模擬器。

若目標有既有 PX4、多機或相機設定，不要整份覆寫：合併以下 `PawnPaths`，並在要替換的車輛中新增 `"PawnPath": "Mavic2Pawn"`，保留原有 VehicleType 和其他設定。

```json
"PawnPaths": {
  "Mavic2Pawn": {
    "PawnBP": "Class'/Game/Mavic2/Blueprints/BP_Mavic2.BP_Mavic2_C'"
  }
}
```

直接雙擊 `.uproject` 不會自動採用本包設定，請用以上帶 `-settings` 的命令。來源工作區的 `Start-Mavic2.ps1` 僅適用原本的 `vendor/AirSim/Unreal/Environments/Blocks` 目錄結構，異地一般專案請使用上述命令。

## 5. 驗收

1. Content Browser 開啟 `Mavic2/Blueprints/BP_Mavic2`，Compile / Save 無錯誤。
2. BodyMesh 應是 `SM_Mavic2_Body`；Prop0–Prop3 應是各自的 `SM_Mavic2_Rotor0–3`，不應使用 `SM_Mavic2_Full` 作為機身。
3. `Rotation0–3` 保留原有控制關係，對應 Prop0–3。不要刪除或更名相機元件。
4. 按 Play 後，檢查模型、相機與槳葉。旋轉由 AirSim 馬達訊號控制；馬達啟用時運轉、解除啟用後停止，對角同向、相鄰反向。
5. 原來源曾驗證空中懸停約 514.5 rad/s，各槳角度持續變化。目標電腦仍需實際驗證，不能以此記錄代替異地驗收。
6. 若使用 Python API，可使用與 AirSim 1.8.1 相容的 client，車輛名稱設為 `MavicSim`。本包不附 Python 環境。

已知限制：原場景的 SimpleFlight 在接地後可能仍回報 Flying；原始無人機也出現同一現象。依賴 landed_state 的降落流程可能逾時，本次模型備份不含此飛控問題的修正。模型尺寸是視覺比例校正，飛行物理仍是 SimpleFlight，並非 DJI 真機精確動力模型。

## 6. 只有 FBX 時的使用方式

- `fbx\Mavic2_Corrected_Assembly.fbx`：完整組裝模型，包含機身與四個獨立槳葉節點，保留安裝位置；沒有 AirSim 控制邏輯或材質塗裝。
- `fbx\mavic2-separated`：五個獨立 FBX，各槳以馬達軸心為原點；`parts.json` 提供 UE4 公分座標的安裝位置。
- 需要恢復旋轉功能時，優先使用本包的 uasset 藍圖。只匯入完整 FBX 不會自動得到飛控或槳葉驅動。
- 如需重建，先安裝 Content/Mavic2 資產，將整個備份保留原目錄結構；使用已啟用 PythonScriptPlugin、EditorScriptingUtilities 的 UE4 對目標專案執行 `scripts/Import-Mavic2.py`。這會覆寫自訂資產，請先備份。拆分來源存在時會自動接續執行槳葉匯入。

## 7. 打包到另一台無需 UE4 的電腦

先在可正常編輯與運作的專案中：

1. Project Settings → Packaging → Additional Asset Directories to Cook 加入 `/Game/Mavic2`。
2. 確認要使用的地圖納入打包，並保留 AirSim 的必要資產設定。
3. Package Project → Windows，完成後將**整個輸出資料夾**移轉，不只複製 exe。
4. 將 `settings-mavic2.json` 隨附，啟動 exe 時用 `-settings` 指向其絕對路徑。
5. 目標電腦安裝打包輸出隨附的 UE prerequisites，確認顯示卡驅動，再重新驗收。

本次 ZIP 是模型備份，尚未替異地電腦產生或測試新的封裝版 exe。


## 2026-10-18 異地部署補充

實際異地啟動曾遇到下載成原始碼包而找不到 `Blocks.uproject`，以及缺少 `XAPOFX1_5.dll`、`X3DAudio1_7.dll`、`D3DCOMPILER_43.dll`、`XINPUT1_3.dll`。若伴隨 90 秒逾時，先處理 DLL 缺件。請依 [異地部署疑難排解](https://github.com/wangsungwen/Mavic2-Orchard-Simulator/blob/main/airsim-autonomy/docs/異地部署疑難排解.md) 完成套件選擇、UE prerequisites 與 DirectX 安裝；DirectX 解壓後必須執行 `DXSETUP.exe`。此補充尚未取得目標電腦修復成功的回報。原 v1 ZIP 與校驗碼保持不變，最新文件由 GitHub 與 Release 補充附件提供。
