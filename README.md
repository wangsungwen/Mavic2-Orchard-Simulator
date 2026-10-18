# Mavic 2 果園模擬器 v1

Windows UE4 4.27 / AirSim 模擬環境，支援「滑鼠選點 → 顯示高度 → Enter 確認 → 模擬機飛往目標」。本版本只控制 AirSim 模擬機，尚未串接 DJI 真機。

## 下載與操作

在本儲存庫的 Releases 下載 `Mavic2Simulator-Orchard-v1-20261018.zip` 及 SHA256 檢查檔，完整解壓縮後執行 `Start-Orchard.cmd`。可攜包不需安裝 UE4 編輯器或 Python；若缺少系統執行元件，請參閱手冊。

- 左鍵選點，方向鍵上／下調整高度，Enter 確認，X 中止並懸停。
- 首次測試：起飛平台附近 N=2、E=2、高度 3 m。
- 選點半徑限制 20 m，高度 1–10 m，相對起飛地面；尚未提供地形跟隨或自動避障。
- `Start-Blocks.cmd` 啟動原有 Blocks 場景。

[完整操作手冊](airsim-autonomy/docs/UE4選點飛行操作.md) · [果園原型說明](airsim-autonomy/docs/山坡柑橘果園原型.md)

## 原始碼配置

`airsim-autonomy/` 包含 Python 控制器、測試、建置腳本與手冊。`pc-control/mission_intelligence.py` 為 CSV 航線功能使用的相依模組；不包含完整的實機控制 APP。

`airsim-autonomy/ue4-overlay/Blocks/` 保存目前 Blocks 專案的自訂 C++、設定及 Mavic2／果園資產，需覆蓋至完成相依建置的 AirSim Blocks 專案。上游版本見 `UPSTREAM.json`。UE4、AirSim 完整原始碼及編譯相依套件不放入此儲存庫；GitHub 自動產生的 Source code ZIP 不是可直接執行的安裝包。

開發環境步驟請參閱 [建置紀錄](airsim-autonomy/docs/路徑B本機建置紀錄.md) 與 [安裝部署](airsim-autonomy/docs/安裝部署與場景建置.md)。舊文件中的本機絕對路徑須改成自己的位置。將 AirSim 放在 `airsim-autonomy/vendor/AirSim`；覆蓋 overlay 前先備份既有專案，並確認依 AirSim 建置流程放置 Blocks 的 AirSim plugin。建置腳本使用的本機工具路徑亦需配合安裝位置。

## 驗證範圍

已完成同一台 Windows 電腦搬移至另一個含空白及中文路徑的執行測試、果園動物移動、模擬機到點及中止測試；尚未驗證另一台乾淨電腦。室內無額外定位設備時，不提供真機自動到點。

## 第三方來源

AirSim 授權見 [Licenses](Licenses/AirSim-LICENSE.txt)。UE4 與其他相依套件適用各自授權。Mavic 2 模型由使用者提供，來源為 [GrabCAD 模型頁](https://grabcad.com/library/dji-mavic-2-pro-drone-rail-2020-1)；本儲存庫不另行授予第三方模型的使用權。模型外觀不代表 Enterprise Dual 的完整物理或感測器模型。
