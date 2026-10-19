# DJI 真機串接第一階段：USB 狀態通道與人工控制入口

版本：0.1，2026-10-19。設備：Mavic 2 Enterprise Dual + Smart Controller。使用者目前未連接設備，因此本階段只有軟體測試，未做 SDK 註冊、USB 實機通訊或實飛驗收。

## 本階段交付

- `DJIConnectionMonitor.exe`：獨立 Windows 只讀連線檢查工具，不需 Python 或 UE4。
- `dji_link.py`：對既有 Mavic Dual Joystick APP 的 8865 通道傳送驗證碼及固定 `status` 請求，不提供任意命令方法。
- 顯示模式、電量、姿態、高度、飛行與馬達狀態、前景與控制授權；資料過期／失敗立即清除。斷線不會自動恢復控制或自動重試驗證碼。
- 室內／戶外選項分開呈現，但兩者目前均未開放 UE4 自動到點。
- 來源版 `navigation_console.py` 新增只讀連線檢查與既有 DJI 人工控制台入口。已發佈的果園 v1.1 ZIP 不受此更新影響。

這是 PC 與 APP 的連線驗收工具，不是完成真機自主導航。現有 APP 可人工操控，但並未因此取得室內場地 XY。UE4 選點仍只控制 AirSim。

## 1. 準備 APP

沿用 `joystick-dual` 的 Mavic Dual Joystick Android **1.0.8**，套件名 `com.example.mavic2joystick`，PC 人工控制台 **1.0.9**。不需修改 Android 協定。

本機現有 APK 位於母專案 `joystick-dual/dist/MavicDualJoystick-1.0.8.apk`。部署到其他電腦時，另行取得 APP；本連線工具包不含 APK、DJI App Key、ADB 或完整人工搖桿控制台。

SDK 註冊需要與套件名稱對應的 DJI App Key；請依 `joystick-dual/docs/AppKey申請與編譯操作指南.md` 建置。不在本工具、GitHub 或對話中填入 App Key；連線只使用 APP 顯示的當次六位碼。

首次連線採地面停槳／拆槳驗收。開啟 APP，關閉其他占用 DJI 連線的 APP，確認 SDK 註冊、飛行器連線與 APP 前景。只讀工具不需要勾選飛行控制授權。

## 2. 建立 USB 通道

在目標電腦安裝 Android SDK Platform Tools，Smart Controller 以 USB 接到電腦；由使用者在裝置上完成 USB 偵錯授權。

在連線工具包根目錄開啟 PowerShell：

```powershell
# 改為自己的 adb.exe 路徑
$adbPath = 'C:\Android\platform-tools\adb.exe'
& $adbPath devices
powershell -NoProfile -ExecutionPolicy Bypass -File .\Connect-DJI-USB.ps1 -Adb $adbPath
```

裝置應顯示 `device`。若為 unauthorized，需在裝置端授權；offline 則重新確認線材及裝置。腳本只接受一台已授權裝置，多台時加 `-Serial 裝置序號`，避免連錯設備。腳本只建立 `tcp:8865` forward，不安裝 APK、不啟動 APP、不發送飛控命令。

開發者若需要安裝既有 APK，可自行在指定正確裝置後執行：

```powershell
& $adbPath -s '你的裝置序號' install -r '完整路徑\MavicDualJoystick-1.0.8.apk'
```

## 3. 開啟只讀連線檢查

1. 雙擊包內 `Start-DJI-Connection.cmd`。
2. HOST 使用 `127.0.0.1`，輸入 APP 的六位驗證碼，包含開頭的 0。
3. 按「連線／監看」，保留 APP 前景。
4. 查看機型、SDK 註冊、APP 模式與資料來源。`DJI_SIMULATOR` 表示 DJI 內建模擬器；`DJI_FLIGHT_CONTROLLER` 表示 APP 回報模擬器未啟動，不代表已獲准起飛。
5. `STALE` 時所有讀數清空；斷線或驗證失敗後需人工重新連線。錯誤五次可能觸發 APP 30 秒鎖定，不要反覆嘗試。

本工具不儲存驗證碼、不在日誌輸出驗證碼、不寫入真機位置。高度是飛控回報高度，不是相對果園坡地的淨空。非模擬器遙測也不代表已完成定位校準。

如需私人 LAN，僅使用受信任網路，在 APP 地面停槳時啟用私人 LAN，HOST 填控制器 IP。既有協定未使用 TLS，不提供公網部署。

## 4. 人工控制如何銜接

只讀確認完成後，可關閉監看視窗，在母專案啟動既有一般 PC 控制台：

```powershell
Set-Location 'C:\Users\wangs\Mavic2Autonomy\joystick-dual'
.\scripts\adb-forward.ps1 -Adb 'C:\Users\wangs\AppData\Local\Android\Sdk\platform-tools\adb.exe'
.\scripts\start-pc.ps1
```

路徑依目標電腦調整。此處不加 `-Demo`，也不使用 `Start-UE4-PC.cmd`：後者為 DJI 模擬器鏡像用途。一般 PC 控制台的真機影像另需 FFmpeg。

依既有 `PC與APP模式切換操作手冊-1.0.9.md` 完成地面模式確認、INDOOR、前景授權與控制來源互斥驗收。起飛、搖桿及接管流程由現場操作員依設備／場地條件執行。本次未發出任何實體飛行命令，未驗證此設備上的實際操控。

## 5. UE4 點選到真機：尚缺什麼

室內目前無可靠 GPS，也無外部定位。真機姿態、高度與速度不等於已校準的 XY；既有 `ue4Pose` 僅為 DJI 模擬器位置，不能當成真機位置。

下一階段需先選定定位方案（例如場地定位系統或經驗證的視覺定位），取得真機位置、航向、時間戳、品質與場地座標轉換，再開發目標預覽、確認、閉迴路到點及失定位處理。尚未有定位來源之前，真機到點按鈕保持停用。

戶外 GPS 功能另行開發，需 GPS 品質、場地與 WGS84 校準、航點預覽及 Android 執行回報。選擇「戶外」不會切換真機模式或解除限制。

## 6. 驗證清單

軟體已通過：28 項 Python 測試（6 項新增 DJI 連線測試），包括 JSON 協定、唯一 status 指令、驗證碼格式、錯誤回覆、過期遙測及禁止以模擬位置啟用真機到點。

待設備到場逐項記錄：SDK 註冊成功、型號正確、USB 通道可讀、電量與姿態對得上、拔 USB 後清空、APP 切背景狀態可見、DJI 模擬器／非模擬器來源可辨識。上述未通過前不宣稱完成實機串接驗收。

參考：現有 APP 原始碼與 [DJI Mobile SDK v4 Android 專案](https://github.com/dji-sdk/Mobile-SDK-Android)、[DJI Android Simulator / Virtual Stick 範例](https://developer.dji.com/mobile-sdk/documentation/android-tutorials/SimulatorDemo.html)。
