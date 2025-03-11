#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
核心引擎模組
負責初始化系統、協調各模組工作並管理主循環
"""

import os
import sys
import time
import yaml
import logging
import traceback
from enum import Enum
from logging.handlers import RotatingFileHandler

# 自定義模組導入
from .game_manager import GameProcessManager, GameStatus
from .window_manager import WindowManager
from .image_detector import ImageDetector
from .task_scheduler import TaskScheduler
from .action_executor import ActionExecutor
from .monitor_manager import MonitorManager
from .position_manager import PositionManager
from .exception_handler import ExceptionHandler
from .hotkey_system import HotkeySystem

class CoreEngine:
    """核心引擎類，負責初始化和協調整個系統"""
    
    def __init__(self, config_path):
        """初始化核心引擎
        
        Args:
            config_path (str): 配置文件路徑
        """
        # 載入配置
        self.config = self._load_config(config_path)
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.control_client = None  # 遠程控制客戶端
        
        # 初始化日誌系統
        self._init_logger()
        self.logger = logging.getLogger("CoreEngine")
        
        # 初始化模組
        self.modules = {}
        self._init_modules()
        
        self.logger.info("核心引擎初始化完成")
    
    def _load_config(self, config_path):
        """載入配置文件
        
        Args:
            config_path (str): 配置文件路徑
            
        Returns:
            dict: 配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"載入配置文件失敗: {str(e)}")
            raise
    
    def _init_logger(self):
        """初始化日誌系統"""
        log_level = getattr(logging, self.config['core']['log_level'])
        
        # 確保日誌目錄存在
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 主日誌
        log_file = os.path.join(log_dir, 'position_manager.log')
        
        # 根日誌配置
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 添加文件處理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    def _init_modules(self):
        """初始化所有系統模組"""
        # 遊戲進程管理
        self.modules['game_manager'] = GameProcessManager(self.config)
        
        # 視窗管理
        self.modules['window_manager'] = WindowManager(self.config)
        
        # 圖像識別
        self.modules['image_detector'] = ImageDetector(self.config)
        
        # 動作執行器
        self.modules['action_executor'] = ActionExecutor(self.config)
        
        # 監控管理器
        self.modules['monitor_manager'] = MonitorManager()
        
        # 任務排程器
        self.modules['task_scheduler'] = TaskScheduler()
        
        # 職位管理器
        self.modules['position_manager'] = PositionManager(
            self.config,
            self.modules['image_detector'],
            self.modules['action_executor']
        )
        
        # 例外處理器
        self.modules['exception_handler'] = ExceptionHandler(
            self.config,
            self.modules['image_detector'],
            self.modules['action_executor']
        )
        
        # 快捷鍵系統
        self.modules['hotkey_system'] = HotkeySystem(
            self.config,
            self  # 傳入核心引擎以讓快捷鍵能控制系統
        )
        
        # 註冊例外監控項
        self.modules['exception_handler'].register_exception_monitors(
            self.modules['monitor_manager']
        )
        
        # 設置排程任務
        self._setup_scheduled_tasks()
    
    def _setup_scheduled_tasks(self):
        """設置排程任務"""
        # 使用新的職位任務處理模組
        from tasks.process_positions_task import process_positions_task, check_overtime_task
        
        task_scheduler = self.modules['task_scheduler']
        
        # 處理申請任務
        if self.config['tasks']['process_applications']['enabled']:
            process_interval = self.config['tasks']['process_applications'].get('interval_minutes')
            process_interval_seconds = self.config['tasks']['process_applications'].get('interval_seconds')
            
            if process_interval_seconds is not None:
                task_scheduler.add_task(
                    id="process_positions",
                    name="處理職位申請",
                    priority=80,
                    interval_seconds=process_interval_seconds,
                    action=lambda: process_positions_task(self)
                )
            else:
                task_scheduler.add_task(
                    id="process_positions",
                    name="處理職位申請",
                    priority=80,
                    interval_minutes=process_interval,
                    action=lambda: process_positions_task(self)
                )
        
        # 檢查超時任務
        if self.config['tasks']['check_overtime']['enabled']:
            overtime_interval_seconds = self.config['tasks']['check_overtime'].get('interval_seconds')
            overtime_interval_minutes = self.config['tasks']['check_overtime'].get('interval_minutes')
            
            if overtime_interval_seconds is not None:
                task_scheduler.add_task(
                    id="check_overtime",
                    name="檢查超時職位",
                    priority=70,
                    interval_seconds=overtime_interval_seconds,
                    action=lambda: check_overtime_task(self)
                )
            else:
                task_scheduler.add_task(
                    id="check_overtime",
                    name="檢查超時職位",
                    priority=70,
                    interval_minutes=overtime_interval_minutes,
                    action=lambda: check_overtime_task(self)
                )
    
    def start(self):
        """啟動系統主循環"""
        self.is_running = True
        self.start_time = time.time()
        self.logger.info("系統啟動中...")
        
        try:
            # 檢查並啟動遊戲
            self._ensure_game_running()
            
            # 啟動主循環
            self._main_loop()
        except Exception as e:
            self.logger.critical(f"主循環出現致命錯誤: {str(e)}")
            self.logger.critical(traceback.format_exc())
        finally:
            self.shutdown()
    
    def _ensure_game_running(self):
        """確保遊戲處於運行狀態"""
        game_manager = self.modules['game_manager']
        status = game_manager.check_game_status()
        
        if status == GameStatus.NOT_RUNNING:
            self.logger.info("遊戲未運行，正在啟動...")
            game_manager.start_game()
        elif status == GameStatus.CRASH or status == GameStatus.FROZEN:
            self.logger.warning(f"遊戲處於異常狀態: {status}，正在重啟...")
            game_manager.restart_game()
    
    def _main_loop(self):
        """主循環"""
        self.logger.info("主循環開始")
        
        while self.is_running:
            try:
                # 檢查遊戲狀態
                game_status = self.modules['game_manager'].check_game_status()
                self._handle_game_status(game_status)
                
                # 如果系統被暫停，則跳過處理
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                
                # 檢查遠程控制信號
                if self.control_client:
                    self._check_remote_control_signals()
                
                # 確保遊戲窗口在前台
                self._ensure_game_foreground()
                
                # 檢查全局監控項
                screen_image = self.modules['image_detector'].get_screen_image()
                if self.modules['monitor_manager'].check_global_monitors(screen_image):
                    continue  # 如果監控項有處理，則跳過當前循環的其他操作
                
                # 執行排程任務
                if not self.modules['task_scheduler'].is_paused:
                    self.modules['task_scheduler'].execute_current_task_step()
                
                # 短暫休眠以減少CPU使用
                time.sleep(0.1)
            
            except Exception as e:
                self.logger.error(f"主循環中遇到錯誤: {str(e)}")
                self.logger.error(traceback.format_exc())
                # 錯誤後稍微暫停一下，避免快速循環錯誤
                time.sleep(1)
    
    def _handle_game_status(self, status):
        """處理不同的遊戲狀態
        
        Args:
            status (GameStatus): 遊戲狀態枚舉
        """
        game_manager = self.modules['game_manager']
        
        if status == GameStatus.NOT_RUNNING:
            self.logger.warning("遊戲未運行，正在啟動...")
            game_manager.start_game()
        
        elif status == GameStatus.MAINTENANCE:
            self.logger.info("遊戲處於維護狀態，等待...")
            # 在維護狀態下暫停排程器
            self.modules['task_scheduler'].pause_scheduler()
            # 等待一段時間後再次檢查
            time.sleep(30)
        
        elif status == GameStatus.REMOTE_LOGIN:
            self.logger.warning("檢測到異地登入，正在處理...")
            # 處理異地登入
            game_manager.handle_remote_login()
        
        elif status == GameStatus.CRASH or status == GameStatus.FROZEN:
            self.logger.warning(f"遊戲處於異常狀態: {status}，正在重啟...")
            game_manager.restart_game()
            # 重啟後暫停一下以等待遊戲穩定
            time.sleep(10)
        
        elif status == GameStatus.RUNNING_NORMAL:
            # 確保排程器在正常狀態下運行
            if self.modules['task_scheduler'].is_paused:
                self.modules['task_scheduler'].resume_scheduler()
    
    def _ensure_game_foreground(self):
        """確保遊戲窗口在前台"""
        window_manager = self.modules['window_manager']
        game_manager = self.modules['game_manager']
        
        if game_manager.current_status == GameStatus.RUNNING_NORMAL:
            if not window_manager.is_foreground_window(game_manager.window_title):
                window_manager.bring_to_foreground(game_manager.window_title)
    
    def _check_remote_control_signals(self):
        """檢查遠程控制信號"""
        # 檢查暫停信號
        if self.control_client.check_system_pause():
            self.logger.info("收到暫停信號，暫停系統")
            self.pause_all()
            return True
        
        # 檢查恢復信號
        if self.control_client.check_system_resume():
            self.logger.info("收到恢復信號，恢復系統")
            self.resume_all()
            return True
        
        # 檢查系統重啟信號
        if self.control_client.check_restart_system():
            self.logger.info("收到系統重啟信號，重啟系統")
            self.restart()
            return True
        
        # 檢查遊戲重啟信號
        if self.control_client.check_restart_game():
            self.logger.info("收到遊戲重啟信號，重啟遊戲")
            self.modules['game_manager'].restart_game()
            return True
        
        # 檢查重置排程信號
        if self.control_client.check_reset_scheduler():
            self.logger.info("收到重置排程信號，重置排程器")
            self.modules['task_scheduler'].reset()
            return True
        
        # 檢查刷新檢測信號
        if self.control_client.check_refresh_detection():
            self.logger.info("收到刷新檢測信號，刷新檢測")
            # 在新線程中執行以避免阻塞主循環
            def refresh_detection():
                image_detector = self.modules['image_detector']
                screen_image = image_detector.get_screen_image(force_refresh=True)
                
                monitor_manager = self.modules['monitor_manager']
                monitor_manager.force_check_all(screen_image)
            
            threading.Thread(target=refresh_detection, daemon=True).start()
            return True
        
        # 檢查職位控制請求
        position_control = self.control_client.check_position_control()
        if position_control[0]:  # 如果有職位ID
            position_id = position_control[0]
            enable = position_control[1]
            self.logger.info(f"收到職位控制請求: {position_id} -> {'啟用' if enable else '禁用'}")
            
            position_manager = self.modules['position_manager']
            if enable:
                position_manager.enable_position(position_id)
            else:
                position_manager.disable_position(position_id)
            
            # 通知UI更新 - 新增此部分
            self._update_ui_after_position_change()
            
            return True
                
        # 檢查移除任務請求
        job_id = self.control_client.check_remove_job()
        if job_id:
            self.logger.info(f"收到移除任務請求，ID: {job_id}")
            self._handle_remove_job(job_id)
            return True
        
        # 檢查聊天請求
        chat_content = self.control_client.check_chat_request()
        if chat_content:
            self.logger.info(f"收到聊天請求: '{chat_content}'")
            self._handle_chat(chat_content)
            return True
        
        return False
    
    def _update_ui_after_position_change(self):
        """職位變更後更新UI"""
        # 檢查是否有UI模塊存在
        if hasattr(self, 'ui') and self.ui is not None:
            # 檢查UI是否有force_update方法
            if hasattr(self.ui, 'force_update'):
                try:
                    # 調用UI的強制更新方法
                    self.ui.force_update()
                    self.logger.debug("已觸發UI職位狀態更新")
                except Exception as e:
                    self.logger.error(f"觸發UI更新時出錯: {str(e)}")
    
    def _handle_remove_job(self, job_id):
        """處理移除任務請求
        
        Args:
            job_id (str): 任務ID
        """
        # 在實際實現中，這裡可以根據具體需要處理
        # 例如，可以調用特定的移除任務腳本
        self.logger.info(f"處理移除任務請求，ID: {job_id}")
        
        # 重置排程器，從頭開始重新排程
        self.modules['task_scheduler'].reset()
    
    def _handle_chat(self, content):
        """處理聊天請求
        
        Args:
            content (str): 聊天內容
        """
        # 在實際實現中，這裡需要根據遊戲特性實現聊天功能
        # 可能需要導航到聊天界面，輸入文字並發送
        self.logger.info(f"處理聊天請求: '{content}'")
        
        # 示例代碼：
        action_executor = self.modules['action_executor']
        
        # 假設需要按下Enter鍵開啟聊天框
        action_executor.key_press('enter')
        time.sleep(0.5)
        
        # 輸入聊天內容
        action_executor.type_string(content)
        time.sleep(0.5)
        
        # 再次按下Enter發送
        action_executor.key_press('enter')
        
        # 完成操作後重置排程器
        self.modules['task_scheduler'].reset()
    
    def pause_all(self):
        """暫停所有功能"""
        self.is_paused = True
        self.modules['task_scheduler'].pause_scheduler()
        self.modules['monitor_manager'].pause_global_monitoring()
        self.logger.info("所有功能已暫停")
    
    def resume_all(self):
        """恢復所有功能"""
        self.is_paused = False
        self.modules['task_scheduler'].resume_scheduler()
        self.modules['monitor_manager'].resume_global_monitoring()
        self.logger.info("所有功能已恢復")
    
    def restart(self):
        """重啟系統"""
        self.logger.info("正在重啟系統...")
        
        # 關閉遊戲
        self.modules['game_manager'].close_game()
        
        # 設置系統退出標記
        self.is_running = False
        
        # 返回不再進入主循環，由調用方處理後續重啟
    
    def shutdown(self):
        """關閉系統"""
        self.logger.info("正在關閉系統...")
        self.is_running = False
        
        # 關閉所有模組
        for name, module in self.modules.items():
            if hasattr(module, 'shutdown'):
                try:
                    module.shutdown()
                except Exception as e:
                    self.logger.error(f"關閉模組 {name} 時出錯: {str(e)}")
        
        # 關閉遠程控制客戶端
        if self.control_client:
            try:
                self.control_client.stop()
            except Exception as e:
                self.logger.error(f"關閉遠程控制客戶端時出錯: {str(e)}")
        
        self.logger.info("系統已關閉")