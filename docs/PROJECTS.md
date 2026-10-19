# 四個分項專案與版本管理

| 分項 | 儲存庫 | 本次來源基準 |
|---|---|---|
| 無人機地面站 | [Mavic2-GroundStation](https://github.com/wangsungwen/Mavic2-GroundStation)（私人） | PC v2 0.3.0-preview；相容 PC 0.2.15；APP 0.2.16-research |
| 模擬器／室內飛行 | [MavicDualJoystick-Lab](https://github.com/wangsungwen/MavicDualJoystick-Lab)（私人） | PC 1.0.9；APP 1.0.8 |
| UE4 仿真 | [Mavic2-Orchard-Simulator](https://github.com/wangsungwen/Mavic2-Orchard-Simulator) | 果園 v1.1；DJI Connection Kit 0.1 |
| 術科模擬飛行 | [unity-drone-simulator](https://github.com/wangsungwen/unity-drone-simulator) | Unity 原生 0.2.2；Web 0.1.1 |

整理基準日：2026-10-19。本次建立 `baseline-2026-10-19` 標籤，表示分項版本管理快照，不提升上述產品版本，也不取代既有發行標籤。

程式、設定範本、測試及操作文件納入 Git。App Key、簽署檔、使用者資料庫、擷取影像、日誌、虛擬環境、引擎與建置快取不提交。APK 與 ZIP 不放入 Git；既有執行包保留原本 Releases 或本機交付資料夾，本次不另發佈含本機 App Key 的 APK。

後續在各自儲存庫建立分支、提交及推送；跨專案更新請同步檢查下列依賴。私人儲存庫需取得權限才能存取。

## 跨專案依賴

將 `MavicDualJoystick-Lab` 與 `Mavic2-Orchard-Simulator` clone 到同一層目錄。雙搖桿 UE4 啟動腳本預設尋找 `../Mavic2-Orchard-Simulator/airsim-autonomy`；仍可用 `-AirSimRoot` 或 `-Python` 覆寫。AirSim 原始碼、UE4 編輯器與 Python 環境必須依 UE4 儲存庫手冊另行建置。

UE4 儲存庫的 `pc-control/mission_intelligence.py` 是地面站模組的版本化副本，讓公開的仿真專案不依賴私人儲存庫才能執行。更新該副本時應同步測試 `airsim-autonomy/tests`。Unity 術科模擬器沒有 DJI 或 UE4 依賴。

GitHub Source code ZIP 是來源快照，不是已安裝依賴的完整本機環境。此版本管理整理不等同真機、跨裝置或 GPU 飛行驗收。
