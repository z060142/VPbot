#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
快捷鍵系統模組
負責註冊和處理快捷鍵
"""

import time
import logging
import threading
import keyboard
from win10toast import ToastNotifier

class HotkeySystem:
    """快捷鍵系統類"""
    
    def __init__(self, config, core_engine):
        """初始化快捷鍵系統
        
        Args:
            config (dict): 系統配置
            core_engine: 核心引擎實例
        """
        self.config = config
        self.core_engine = core_engine
        self.logger = logging.getLogger("HotkeySystem")
        
        # 初始化狀態
        self.is_scheduler_paused = False
        self.is_detection_paused = False
        
        # 載入配置中的快捷鍵設置
        self.hotkey_config = config.get('hotkeys', {})
        
        # 初始化通知器
        try:
            self.notifier = ToastNotifier()
            self.notification_enabled = True
        except Exception as e:
            self.logger.warning(f"無法初始化通知器: {str(e)}")
            self.notification_enabled = False
        
        # 註冊快捷鍵
        self._register_hotkeys()
        
        self.logger.info("快捷鍵系統初始化完成")
    
    def _register_hotkeys(self):
        """註冊所有快捷鍵"""
        self.logger.info("註冊快捷鍵")
        
        try:
            # 註冊暫停/恢復所有功能的快捷鍵
            if 'toggle_all' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['toggle_all'],
                    self.toggle_all,
                    suppress=True
                )
                self.logger.info(f"註冊暫停/恢復所有功能的快捷鍵: {self.hotkey_config['toggle_all']}")
            
            # 註冊暫停/恢復排程器的快捷鍵
            if 'toggle_scheduler' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['toggle_scheduler'],
                    self.toggle_scheduler,
                    suppress=True
                )
                self.logger.info(f"註冊暫停/恢復排程器的快捷鍵: {self.hotkey_config['toggle_scheduler']}")
            
            # 註冊暫停/恢復檢測的快捷鍵
            if 'toggle_detection' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['toggle_detection'],
                    self.toggle_detection,
                    suppress=True
                )
                self.logger.info(f"註冊暫停/恢復檢測的快捷鍵: {self.hotkey_config['toggle_detection']}")
            
            # 註冊緊急停止的快捷鍵
            if 'emergency_stop' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['emergency_stop'],
                    self.emergency_stop,
                    suppress=True
                )
                self.logger.info(f"註冊緊急停止的快捷鍵: {self.hotkey_config['emergency_stop']}")
            
            # 註冊重啟當前任務的快捷鍵
            if 'restart_task' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['restart_task'],
                    self.restart_current_task,
                    suppress=True
                )
                self.logger.info(f"註冊重啟當前任務的快捷鍵: {self.hotkey_config['restart_task']}")
            
            # 註冊跳過當前任務的快捷鍵
            if 'skip_task' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['skip_task'],
                    self.skip_current_task,
                    suppress=True
                )
                self.logger.info(f"註冊跳過當前任務的快捷鍵: {self.hotkey_config['skip_task']}")
            
            # 註冊強制刷新檢測的快捷鍵
            if 'force_refresh' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['force_refresh'],
                    self.force_refresh,
                    suppress=True
                )
                self.logger.info(f"註冊強制刷新檢測的快捷鍵: {self.hotkey_config['force_refresh']}")
            
            # 註冊切換狀態顯示的快捷鍵
            if 'toggle_status' in self.hotkey_config:
                keyboard.add_hotkey(
                    self.hotkey_config['toggle_status'],
                    self.toggle_status_display,
                    suppress=True
                )
                self.logger.info(f"註冊切換狀態顯示的快捷鍵: {self.hotkey_config['toggle_status']}")
            
        except Exception as e:
            self.logger.error(f"註冊快捷鍵時出錯: {str(e)}")
    
    def toggle_all(self):
        """切換所有功能"""
        self.logger.info("快捷鍵觸發: 切換所有功能")
        
        if self.core_engine.is_paused:
            self.core_engine.resume_all()
            self._show_notification("系統已恢復", "所有功能已恢復運行")
        else:
            self.core_engine.pause_all()
            self._show_notification("系統已暫停", "所有功能已暫停")
    
    def toggle_scheduler(self):
        """切換排程功能"""
        self.logger.info("快捷鍵觸發: 切換排程功能")
        
        task_scheduler = self.core_engine.modules['task_scheduler']
        
        if task_scheduler.is_paused:
            task_scheduler.resume_scheduler()
            self.is_scheduler_paused = False
            self._show_notification("排程已恢復", "任務排程器已恢復運行")
        else:
            task_scheduler.pause_scheduler()
            self.is_scheduler_paused = True
            self._show_notification("排程已暫停", "任務排程器已暫停")
    
    def toggle_detection(self):
        """切換檢測功能"""
        self.logger.info("快捷鍵觸發: 切換檢測功能")
        
        monitor_manager = self.core_engine.modules['monitor_manager']
        
        if self.is_detection_paused:
            monitor_manager.resume_global_monitoring()
            self.is_detection_paused = False
            self._show_notification("檢測已恢復", "全局監控已恢復運行")
        else:
            monitor_manager.pause_global_monitoring()
            self.is_detection_paused = True
            self._show_notification("檢測已暫停", "全局監控已暫停")
    
    def emergency_stop(self):
        """緊急停止所有操作"""
        self.logger.info("快捷鍵觸發: 緊急停止")
        
        # 暫停所有功能
        self.core_engine.pause_all()
        
        # 停止所有動作
        self.core_engine.modules['action_executor'].stop_all_actions()
        
        # 重置任務排程器
        self.core_engine.modules['task_scheduler'].reset()
        
        self._show_notification("緊急停止", "所有操作已停止", "緊急")
    
    def restart_current_task(self):
        """重啟當前任務"""
        self.logger.info("快捷鍵觸發: 重啟當前任務")
        
        task_scheduler = self.core_engine.modules['task_scheduler']
        current_task = task_scheduler.get_current_task()
        
        if current_task:
            task_name = current_task.name
            task_scheduler.restart_task(current_task.id)
            self._show_notification("重啟任務", f"已重啟任務: {task_name}")
        else:
            self._show_notification("無法重啟", "當前沒有執行中的任務")
    
    def skip_current_task(self):
        """跳過當前任務"""
        self.logger.info("快捷鍵觸發: 跳過當前任務")
        
        task_scheduler = self.core_engine.modules['task_scheduler']
        current_task = task_scheduler.get_current_task()
        
        if current_task:
            task_name = current_task.name
            task_scheduler.skip_current_task()
            self._show_notification("跳過任務", f"已跳過任務: {task_name}")
        else:
            self._show_notification("無法跳過", "當前沒有執行中的任務")
    
    def force_refresh(self):
        """強制刷新檢測"""
        self.logger.info("快捷鍵觸發: 強制刷新檢測")
        
        # 強制刷新屏幕圖像
        image_detector = self.core_engine.modules['image_detector']
        screen_image = image_detector.get_screen_image(force_refresh=True)
        
        # 強制執行所有監控項檢測
        monitor_manager = self.core_engine.modules['monitor_manager']
        result = monitor_manager.force_check_all(screen_image)
        
        if result:
            self._show_notification("刷新檢測", "檢測到異常情況並處理")
        else:
            self._show_notification("刷新檢測", "未檢測到異常情況")
    
    def toggle_status_display(self):
        """切換狀態顯示"""
        self.logger.info("快捷鍵觸發: 切換狀態顯示")
        
        # 這個功能需要有狀態顯示界面才能實現
        # 例如，可以顯示一個帶有系統狀態的懸浮窗口
        
        # 目前只是顯示一個通知
        status_info = self._get_status_info()
        self._show_notification("系統狀態", status_info)
    
    def _get_status_info(self):
        """獲取系統狀態信息
        
        Returns:
            str: 狀態信息
        """
        # 獲取遊戲狀態
        game_status = self.core_engine.modules['game_manager'].current_status.name
        
        # 獲取當前任務
        task_scheduler = self.core_engine.modules['task_scheduler']
        current_task = task_scheduler.get_current_task()
        task_info = f"{current_task.name}" if current_task else "無"
        
        # 獲取暫停狀態
        system_paused = "是" if self.core_engine.is_paused else "否"
        scheduler_paused = "是" if task_scheduler.is_paused else "否"
        detection_paused = "是" if self.is_detection_paused else "否"
        
        # 組合狀態信息
        status_info = (
            f"遊戲狀態: {game_status}\n"
            f"當前任務: {task_info}\n"
            f"系統暫停: {system_paused}\n"
            f"排程暫停: {scheduler_paused}\n"
            f"檢測暫停: {detection_paused}"
        )
        
        return status_info
    
    def _show_notification(self, title, message, priority="normal"):
        """顯示系統通知
        
        Args:
            title (str): 通知標題
            message (str): 通知內容
            priority (str, optional): 通知優先級 ("normal" 或 "緊急")
        """
        if not self.notification_enabled:
            return
        
        # 在單獨的線程中顯示通知，避免阻塞主線程
        threading.Thread(
            target=self._show_notification_thread,
            args=(title, message, priority),
            daemon=True
        ).start()
    
    def _show_notification_thread(self, title, message, priority):
        """在線程中顯示通知
        
        Args:
            title (str): 通知標題
            message (str): 通知內容
            priority (str): 通知優先級
        """
        try:
            # 設置通知圖標和持續時間
            icon_path = None  # 可以設置自定義圖標
            duration = 5  # 普通通知持續5秒
            
            if priority == "緊急":
                duration = 10  # 緊急通知持續10秒
            
            # 顯示通知
            self.notifier.show_toast(
                title,
                message,
                icon_path=icon_path,
                duration=duration,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"顯示通知時出錯: {str(e)}")
    
    def shutdown(self):
        """關閉快捷鍵系統"""
        self.logger.info("關閉快捷鍵系統")
        
        # 解除所有註冊的快捷鍵
        try:
            keyboard.unhook_all()
        except:
            pass