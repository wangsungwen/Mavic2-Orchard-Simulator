# Mavic 2 果園模擬器

新增 [v1.1 視角操作更新](https://github.com/wangsungwen/Mavic2-Orchard-Simulator/releases/tag/v1.1.0-camera)：滾輪縮放、WASD／中鍵平移、F 全果園、Home 起飛區。詳見 [操作說明](airsim-autonomy/docs/果園視角操作更新.md)。編譯及模擬飛行回歸通過；原生相機按鍵測試因 Windows 安全提示阻擋，尚未完成。

Windows UE4 4.27 / AirSim 模擬環境，支援「滑鼠選點 → 顯示高度 → Enter 確認 → 模擬機飛往目標」。本版本只控制 AirSim 模擬機，尚未串接 DJI 真機。

## 下載與操作

在 [Releases 發佈頁](https://github.com/wangsungwen/Mavic2-Orchard-Simulator/releases/tag/v1.0.0-orchard) 下載 `Mavic2Simulator-Orchard-v1-20261018.zip` 及 SHA256 檢查檔，完整解壓縮後執行 `Start-Orchard.cmd`。可攜包不需安裝 UE4 編輯器或 Python；若缺少系統執行元件，請參閱手冊。

- 左鍵選點，方向鍵上／下調整高度，Enter 確認，X 中止並懸停。
- 首次測試：起飛平台附近 N=2、E=2、高度 3 m。
- 選點半徑限制 20 m，高度 1–10 m，相對起飛地面；尚未提供地形跟隨或自動避障。
- `Start-Blocks.cmd` 啟動原有 Blocks 場景。

[完整操作手冊](airsim-autonomy/docs/UE4選點飛行操作.md) · [果園原型說明](airsim-autonomy/docs/山坡柑橘果園原型.md)

## 異地啟動出錯

若找不到 `Blocks.uproject`，請改下載 Releases 的完整執行包。若缺少 `XAPOFX1_5.dll`、`X3DAudio1_7.dll`、`D3DCOMPILER_43.dll` 或 `XINPUT1_3.dll`，請安裝舊版 DirectX 執行元件。完整步驟見 [異地部署疑難排解](airsim-autonomy/docs/異地部署疑難排解.md)，包含安裝後驗收與 90 秒逾時處理。

## 原始碼配置

`airsim-autonomy/` 包含 Python 控制器、測試、建置腳本與手冊。`pc-control/mission_intelligence.py` 為 CSV 航線功能使用的相依模組；不包含完整的實機控制 APP。

`airsim-autonomy/ue4-overlay/Blocks/` 保存目前 Blocks 專案的自訂 C++、設定及 Mavic2／果園資產，需覆蓋至完成相依建置的 AirSim Blocks 專案。上游版本見 `UPSTREAM.json`。UE4、AirSim 完整原始碼及編譯相依套件不放入此儲存庫；GitHub 自動產生的 Source code ZIP 不是可直接執行的安裝包。

開發環境步驟請參閱 [建置紀錄](airsim-autonomy/docs/路徑B本機建置紀錄.md) 與 [安裝部署](airsim-autonomy/docs/安裝部署與場景建置.md)。舊文件中的本機絕對路徑須改成自己的位置。將 AirSim 放在 `airsim-autonomy/vendor/AirSim`；覆蓋 overlay 前先備份既有專案，並確認依 AirSim 建置流程放置 Blocks 的 AirSim plugin。建置腳本使用的本機工具路徑亦需配合安裝位置。

## 驗證範圍

已完成同一台 Windows 電腦搬移至另一個含空白及中文路徑的執行測試、果園動物移動、模擬機到點及中止測試；尚未驗證另一台乾淨電腦。室內無額外定位設備時，不提供真機自動到點。

## 第三方來源

AirSim 授權見 [Licenses](Licenses/AirSim-LICENSE.txt)。UE4 與其他相依套件適用各自授權。Mavic 2 模型由使用者提供，來源為 [GrabCAD 模型頁](https://grabcad.com/library/dji-mavic-2-pro-drone-rail-2020-1)；本儲存庫不另行授予第三方模型的使用權。模型外觀不代表 Enterprise Dual 的完整物理或感測器模型。


## DJI 真機連線第一階段（0.1）

[連線工具下載](https://github.com/wangsungwen/Mavic2-Orchard-Simulator/releases/tag/v0.1.0-dji-connection) · [操作手冊](airsim-autonomy/docs/DJI真機串接第一階段.md)。使用既有 Mavic Dual Joystick APP 讀取狀態，未開放 UE4 真機到點，不包含 APK／App Key／ADB。設備尚未連接，本版只有軟體及介面啟動檢查。
