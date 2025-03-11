遊戲職位管理自動化系統
專案概述
遊戲職位管理自動化系統是一個基於Python的自動化工具，專為「Last War」遊戲設計，用於自動化管理遊戲中的職位申請和任命流程。系統能夠自動檢測並處理申請者、罷黜超時人員，並處理各種遊戲中可能出現的例外情況。
主要功能

自動處理職位申請: 自動檢測並處理6個不同職位的申請者
職位獨立控制: Al個職位可獨立開啟或關閉處理功能
超時管理: 自動罷黜任職超過指定時間的人員
遊戲程式管理: 自動檢測、啟動、重啟遊戲程式
例外處理: 處理伺服器維護、彈窗廣告等例外情況
遠端控制: 支援通過Socket.IO伺服器進行遠端控制
快捷鍵支援: 提供全局快捷鍵來控制系統功能
狀態監控: 圖形介面顯示系統運行狀態和統計信息

系統需求

Python 3.8 或更高版本
Windows 10/11
支援的遊戲: Last War (Survival Game)

依賴庫

OpenCV (圖像處理)
PyAutoGUI/PyDirectInput (鍵鼠操作)
keyboard (熱鍵支持)
psutil (進程監控)
pywin32 (Windows API)
numpy (數值計算)
socketio (遠端控制)
PyYAML (配置文件)
win10toast (通知)
Tesseract-OCR (文字識別, 用於超時檢測)

安裝說明

確保已安裝Python 3.8+
安裝必要的依賴庫:

bashCopypip install -r requirements.txt

安裝Tesseract-OCR並設置環境變數或在配置文件中指定路徑
將配置文件config.yaml根據實際需求進行修改
確保images目錄下包含所有必要的模板圖像

配置說明
系統通過config.yaml文件進行配置，主要配置項說明如下:
核心設定
yamlCopycore:
  max_retry_count: 3           # 最大重試次數
  log_level: "INFO"            # 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  data_dir: "data/"            # 數據目錄
遊戲設定
yamlCopygame:
  game_path: "C:\\Path\\To\\Game\\Launch.exe"  # 遊戲路徑
  process_name: "GameProcess.exe"              # 進程名稱
  window_title: "Game Window Title"            # 窗口標題
  max_runtime: 28800                           # 最大運行時間(秒)
  position:                                    # 窗口位置和大小
    x: 0
    y: 0
    width: 1920
    height: 1080
職位設定
yamlCopypositions:
  - id: "position_1"
    name: "職位1"
    enabled: true
    application_region: [100, 150, 400, 300]  # 申請區域 [x, y, width, height]
    time_region: [500, 150, 100, 30]          # 時間顯示區域
    overtime_threshold: 10                    # 超時閾值(分鐘)
更多詳細配置請參考配置文件中的註釋說明。
使用方法
基本啟動
bashCopypython main.py
啟動參數
bashCopypython main.py --config custom_config.yaml  # 使用自定義配置文件
python main.py --log-level DEBUG            # 設置日誌級別
python main.py --no-remote                  # 禁用遠端控制
python main.py --no-ui                      # 禁用GUI界面
快捷鍵
快捷鍵功能F9暫停/恢復所有功能F10暫停/恢復排程器F11暫停/恢復檢測F12緊急停止所有操作Ctrl+F9重啟當前任務Ctrl+F10跳過當前任務Ctrl+F11強制刷新檢測Ctrl+Shift+S切換狀態顯示
遠端控制
系統支援通過Socket.IO協議進行遠端控制，支援的命令包括：

pause system/resume system: 暫停/恢復系統
restart system: 重啟系統
restart game: 重啟遊戲
reset scheduler: 重置排程
refresh detection: 刷新檢測
enable position#/disable position#: 啟用/禁用指定職位
remove [ID]: 罷黜特定ID的職位
say: [message]: 發送聊天訊息

項目結構
Copyproject/
├── main.py              # 主程序入口
├── config.yaml          # 配置文件
├── control_client.py    # 遠端控制客戶端
├── modules/             # 核心模組
│   ├── __init__.py
│   ├── core_engine.py   # 核心引擎
│   ├── game_manager.py  # 遊戲進程管理
│   ├── window_manager.py # 視窗管理
│   ├── image_detector.py # 圖像識別
│   ├── task_scheduler.py # 任務排程
│   ├── action_executor.py # 動作執行
│   ├── monitor_manager.py # 監控管理
│   ├── position_manager.py # 職位管理
│   ├── exception_handler.py # 例外處理
│   └── hotkey_system.py # 快捷鍵系統
├── tasks/               # 任務實現
│   ├── __init__.py
│   ├── process_positions_task.py
│   ├── check_overtime.py
│   └── utils/           # 任務通用工具
│       ├── __init__.py
│       ├── navigation.py
│       ├── ui_interaction.py
│       └── exception_handlers.py
├── ui_control.py        # UI控制介面
├── images/              # 圖像資源
│   ├── ui/              # UI元素圖像
│   ├── positions/       # 職位相關圖像
│   └── exceptions/      # 例外情況圖像
├── logs/                # 日誌目錄
└── data/                # 數據目錄
故障排除
常見問題

無法啟動遊戲

檢查遊戲路徑配置是否正確
確認遊戲本身是否可以正常啟動


無法識別遊戲元素

檢查圖像資源是否完整
調整匹配閾值
截取新的模板圖像


職位處理不正常

檢查職位區域配置是否正確
查看日誌了解詳細錯誤信息


遠端控制無法連接

檢查伺服器URL和認證信息
確認網絡連接是否正常



日誌查看
系統日誌位於logs/目錄下，按日期分類。查看最新日誌可以幫助排查問題。
開發者擴展
添加新功能

了解模組結構和設計
確定擴展的目標模組
實現新功能並與現有架構整合
在配置文件中添加相關設置

模板圖像準備
添加新的檢測項需準備模板圖像:

格式: PNG (支持透明度)
裁剪精確，去除不必要背景
按功能分類存放在images/目錄下

注意事項

本工具僅限於合法使用，請遵守遊戲服務條款
長時間使用可能會增加系統資源佔用
建議定期檢查日誌和更新模板圖像
使用前請備份重要數據

許可證
本專案採用MIT許可證。
貢獻
歡迎提交問題報告、功能建議或代碼貢獻。
聯絡方式
如有問題或建議，請通過以下方式聯繫:

電子郵件: support@example.com
項目主頁: https://github.com/yourusername/game-position-manager
