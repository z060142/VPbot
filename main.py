#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
遊戲職位管理自動化腳本系統
主入口程式

功能:
- 自動檢測並處理6個不同職位的申請者
- 自動罷黜任職超過指定時間的人員
- 檢測並處理遊戲程式狀態(不存在、需要重啟等)
- 處理遊戲例外狀況(伺服器維護、彈窗廣告等)
- 支援遠端控制
- 提供快捷鍵暫停、恢復功能
"""

import os
import sys
import time
import logging
import signal
import traceback
import argparse
import threading

# 添加當前目錄到搜索路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入核心引擎
from modules.core_engine import CoreEngine

# 導入遠程控制客戶端
from control_client import ControlClient

# 導入UI控制模組 (如果可用)
try:
    from ui_control import StatusUI
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False

# 全局變量
engine = None
config_path = None
args = None
ui = None

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='遊戲職位管理自動化腳本系統')
    
    parser.add_argument(
        '--config', 
        default='config.yaml',
        help='配置文件路徑 (默認: config.yaml)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=None,
        help='日誌級別 (覆蓋配置文件設置)'
    )
    
    parser.add_argument(
        '--no-remote',
        action='store_true',
        help='禁用遠程控制'
    )
    
    parser.add_argument(
        '--no-ui',
        action='store_true',
        help='禁用GUI界面'
    )
    
    return parser.parse_args()

def setup_control_client():
    """設置遠程控制客戶端"""
    global engine
    
    # 如果命令行參數指定不使用遠程控制，或配置中禁用遠程控制
    if args.no_remote or not engine.config['remote_control']['enabled']:
        return None
    
    try:
        # 創建控制客戶端
        client = ControlClient(
            server_url=engine.config['remote_control']['server_url'],
            client_key=engine.config['remote_control']['client_key']
        )
        
        # 註冊其他客製化命令
        # 使現有命令擴展支持我們的特定需求:
        # - restart / restart wolf: 重啟遊戲
        # - restart bot: 重啟整個腳本系統
        # - reset: 重置排程器
        # - remove: 處理remove_job.py (可根據需要實現)
        # - say: 聊天命令 (可根據需要實現)
        
        # 啟動客戶端線程
        client_thread = client.run_in_thread()
        
        # 存到引擎中以便後續使用
        engine.control_client = client
        
        logging.info("遠程控制客戶端已啟動")
        return client
    
    except Exception as e:
        logging.error(f"啟動遠程控制客戶端時出錯: {str(e)}")
        return None

def setup_ui():
    """設置UI界面"""
    global engine, ui
    
    # 如果命令行參數指定不使用UI，或UI不可用
    if args.no_ui or not UI_AVAILABLE:
        return None
    
    try:
        # 創建UI實例
        ui = StatusUI(engine)
        
        # 將UI引用存儲到引擎中，使引擎可以與UI交互 - 新增此行
        engine.ui = ui
        
        # 在新線程中啟動UI
        ui_thread = threading.Thread(target=ui.show, daemon=True)
        ui_thread.start()
        
        logging.info("UI界面已啟動")
        return ui
    
    except Exception as e:
        logging.error(f"啟動UI界面時出錯: {str(e)}")
        return None

def signal_handler(sig, frame):
    """處理終止信號"""
    logging.info("收到終止信號，正在關閉系統...")
    shutdown()
    
def shutdown():
    """關閉系統"""
    global engine, ui
    
    try:
        # 關閉UI
        if ui:
            ui.shutdown()
        
        # 關閉引擎
        if engine:
            engine.shutdown()
    except Exception as e:
        logging.error(f"關閉系統時出錯: {str(e)}")
    
    logging.info("系統已關閉")
    sys.exit(0)

def restart_script():
    """重啟整個腳本"""
    logging.info("正在重啟腳本...")
    
    # 關閉系統
    if engine:
        engine.shutdown()
    
    # 使用Python重啟自身
    python = sys.executable
    os.execl(python, python, *sys.argv)

def main():
    """主函數"""
    global engine, config_path, args, ui
    
    # 解析命令行參數
    args = parse_arguments()
    
    # 設置配置文件路徑
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        args.config
    )
    
    try:
        # 初始化核心引擎
        engine = CoreEngine(config_path)
        
        # 如果命令行指定了日誌級別，則覆蓋配置
        if args.log_level:
            log_level = getattr(logging, args.log_level)
            logging.getLogger().setLevel(log_level)
            logging.info(f"日誌級別已設為: {args.log_level}")
        
        # 設置信號處理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 設置遠程控制
        control_client = setup_control_client()
        
        # 設置UI界面
        if not args.no_ui and UI_AVAILABLE:
            ui_setup = setup_ui()
        
        # 啟動引擎
        engine.start()
    
    except KeyboardInterrupt:
        logging.info("收到鍵盤中斷，正在關閉...")
    except Exception as e:
        logging.critical(f"主程序出現致命錯誤: {str(e)}")
        logging.critical(traceback.format_exc())
    finally:
        shutdown()

if __name__ == "__main__":
    main()