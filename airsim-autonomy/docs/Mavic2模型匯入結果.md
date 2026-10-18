# Mavic 2 模型已匯入 UE4

使用的專案：`vendor/AirSim/Unreal/Environments/Blocks/Blocks.uproject`（UE4.27.2）。

## 開啟

雙擊專案根目錄的 `Start-Mavic2.cmd` 可開啟模擬視窗。

若要開啟 UE4 編輯器，先關閉目前模擬視窗，再在專案根目錄執行：

```powershell
.\scripts\Start-Mavic2.ps1 -Editor
```

在 Content Browser 開啟 `Content/Mavic2/Blueprints/BP_Mavic2`。按 Play 會以新的外觀生成 `MavicSim`。

請使用此入口，它明確載入 `config/settings-mavic2.json`。原本 `Start-Simulator.ps1` 啟動的是下載好的封裝版 Blocks，該執行檔不包含此次新增資產。

## 已建立的資產

- `/Game/Mavic2/Meshes/SM_Mavic2_Body`（不含槳葉的機身）
- `/Game/Mavic2/Meshes/SM_Mavic2_Rotor0` 至 `SM_Mavic2_Rotor3`
- `/Game/Mavic2/Materials/M_Mavic2_Grey`
- `/Game/Mavic2/Blueprints/BP_Mavic2`

來源 FBX：`fbx/ImageToStl.com_DJi+Mavic+2+pro+drone+Rail+2020-1.fbx`。

FBX 原始匯入尺寸約 5.86 × 1.24 × 5.22 公分，機體側躺。已套用匯入旋轉（Pitch 0、Yaw -90、Roll 90）、等比例放大 8 倍並置中；最終包圍盒約長 41.8 × 寬 46.9 × 高 9.9 公分（含槳葉）。這是視覺比例調整，不是 DJI 實測尺寸校正。

獨立藍圖保留 AirSim 的相機及旋轉控制元件。四組原始槳葉與輪轂已從機身拆出，取代 Prop0–Prop3，以各馬達軸心旋轉並跟隨 AirSim 轉速，兩組順時針、兩組逆時針。舊槳網格已被替換，隱藏陰影已關閉；可見槳葉與陰影使用同一組元件。使用灰色機身與深灰槳葉材質，沒有還原預覽圖的塗裝。碰撞為簡化形狀，飛行動力參數沿用原本的 SimpleFlight。

## 驗證與已知問題

- UE4 成功載入並顯示 Mavic 2；畫面存於 `artifacts/mavic2/ue4-preview.png`。
- RPC 可找到 `MavicSim`，前方相機輸出 640 × 480。
- 起飛與懸停成功。
- 降落後機體接觸 Ground 且速度歸零，但 SimpleFlight 的 `landed_state` 仍為 Flying。
- 換回原本 BP_FlyingPawn 做同樣測試也有相同問題，對照記錄在 `artifacts/mavic2/baseline-landing.json`。此問題未修改飛控程式處理，不能宣稱完整降落驗收通過。既有 `fly.py land` 依賴該旗標，可能逾時。

## 重新匯入與打包

`scripts/Import-Mavic2.py` 是 UE4 Python 匯入腳本，會覆寫上述三個自訂資產；自訂材質或藍圖後，重新執行前請先備份。它須在 UE4 的 PythonScriptPlugin 與 EditorScriptingUtilities 啟用時執行，不可直接用一般 Python 執行。

若之後打包，請在 Project Settings → Packaging → Additional Asset Directories to Cook 加入 `/Game/Mavic2`，並隨執行檔使用 `settings-mavic2.json`。本次未重新打包 exe。

## 槳葉動畫驗證（2026-10-17）

- 四組 Rotation 元件控制 Prop0–Prop3，執行中網格均為新拆分的 Mavic 2 槳葉。
- 懸停轉速約 514.5 rad/s（4,913 RPM），元件角速度約正負 29,479 度/秒，直接沿用 AirSim 馬達訊號。
- 連續取樣四組槳葉角度皆改變；馬達解除啟用後角速度降至零。
- 10,970 個匯入三角面完整分配到機身與四組槳葉，沒有保留重複的靜態槳葉。
- 畫面：`artifacts/mavic2/rotors-hover.png`；記錄：`artifacts/mavic2/rotor-runtime-evidence.txt`。

`scripts/Split-Mavic2-Rotors.py` 產生拆分 FBX，`scripts/Import-Mavic2-Rotors.py` 在 UE4 中匯入並連接元件。主匯入腳本偵測到拆分來源時會自動執行槳葉匯入，避免退回靜態版本。更新後使用原本的 `Start-Mavic2.cmd` 啟動即可。
