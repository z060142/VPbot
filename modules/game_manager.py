#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
遊戲進程管理器模組
負責遊戲進程的監控、啟動、重啟與關閉
"""

import os
import time
import logging
import subprocess
import psutil
from enum import Enum

class GameStatus(Enum):
    """遊戲狀態枚舉"""
    NOT_RUNNING = 0         # 遊戲未運行
    STARTING = 1            # 遊戲正在啟動中
    RUNNING_NORMAL = 2      # 遊戲正常運行
    RUNNING_IDLE = 3        # 遊戲運行但閒置中
    MAINTENANCE = 4         # 伺服器維護中
    REMOTE_LOGIN = 5        # 異地登入被檢測
    CRASH = 6               # 遊戲崩潰
    FROZEN = 7              # 遊戲卡死
    CLOSING = 8             # 遊戲正在關閉
    UNKNOWN = 9             # 未知狀態

class GameProcessManager:
    """遊戲進程管理器類"""
    
    def __init__(self, config):
        """初始化遊戲進程管理器
        
        Args:
            config (dict): 系統配置
        """
        self.config = config
        self.logger = logging.getLogger("GameManager")
        
        # 從配置中獲取遊戲相關設置
        self.game_path = config['game']['game_path']
        self.process_name = config['game']['process_name']
        self.window_title = config['game']['window_title']
        self.max_runtime = config['game']['max_runtime']
        self.startup_wait_time = config['game'].get('startup_wait_time', 30)
        
        # 初始化狀態
        self.process_id = None
        self.current_status = GameStatus.UNKNOWN
        self.start_time = None
        
        # 進行初始狀態檢測
        self.check_game_status()
        
        self.logger.info("遊戲進程管理器初始化完成")
    
    def check_game_status(self):
        """檢查遊戲當前狀態
        
        Returns:
            GameStatus: 遊戲狀態
        """
        # 嘗試查找遊戲進程
        process = self._find_game_process()
        
        if not process:
            self.current_status = GameStatus.NOT_RUNNING
            self.process_id = None
            self.start_time = None
            return self.current_status
        
        # 更新進程ID和啟動時間
        self.process_id = process.pid
        if not self.start_time:
            self.start_time = process.create_time()
        
        # 檢查進程是否響應
        if not self._is_process_responding(process):
            self.current_status = GameStatus.FROZEN
            return self.current_status
        
        # 檢查運行時間是否超過限制
        if self.max_runtime > 0 and time.time() - self.start_time > self.max_runtime:
            self.logger.warning(f"遊戲運行時間超過限制 ({self.max_runtime} 秒)，需要重啟")
            self.current_status = GameStatus.RUNNING_IDLE
            return self.current_status
        
        # 如果前面都沒有確定狀態，則根據窗口標題判斷
        if self.window_title and self._find_game_window():
            self.current_status = GameStatus.RUNNING_NORMAL
        else:
            self.current_status = GameStatus.RUNNING_IDLE
        
        return self.current_status
    
    def start_game(self):
        """啟動遊戲
        
        Returns:
            bool: 是否成功啟動
        """
        # 如果遊戲已經在運行，則直接返回
        if self.current_status != GameStatus.NOT_RUNNING:
            self.logger.warning("遊戲已經在運行，無需重新啟動")
            return True
        
        self.logger.info(f"正在啟動遊戲: {self.game_path}")
        self.current_status = GameStatus.STARTING
        
        try:
            # 使用subprocess啟動遊戲
            subprocess.Popen(self.game_path, shell=True)
            
            # 等待遊戲啟動
            start_wait_time = time.time()
            max_wait_time = self.startup_wait_time
            
            while time.time() - start_wait_time < max_wait_time:
                process = self._find_game_process()
                if process:
                    self.process_id = process.pid
                    self.start_time = process.create_time()
                    self.current_status = GameStatus.RUNNING_NORMAL
                    self.logger.info("遊戲啟動成功")
                    
                    # 添加以下代碼: 設置窗口位置和大小
                    # 等待窗口創建和初始化
                    time.sleep(3)  # 給遊戲一些時間創建窗口
                    
                    # 導入window_manager模塊，以直接調用設置窗口位置的方法
                    from modules.window_manager import WindowManager
                    
                    # 嘗試設置窗口位置和大小
                    for attempt in range(3):  # 最多嘗試3次
                        window_manager = WindowManager(self.config)
                        if window_manager.set_window_position():
                            self.logger.info("已設置遊戲窗口位置和大小")
                            break
                        else:
                            self.logger.warning(f"設置窗口位置失敗，嘗試 {attempt+1}/3")
                            time.sleep(2)  # 等待窗口穩定
                    
                    return True
                
                # 短暫休眠
                time.sleep(1)
            
            # 超時未檢測到遊戲進程
            self.logger.error(f"遊戲啟動超時 ({max_wait_time} 秒)")
            self.current_status = GameStatus.NOT_RUNNING
            return False
        
        except Exception as e:
            self.logger.error(f"啟動遊戲時出錯: {str(e)}")
            self.current_status = GameStatus.NOT_RUNNING
            return False
    
    def close_game(self, force=False):
        """關閉遊戲
        
        Args:
            force (bool, optional): 是否強制關閉
        
        Returns:
            bool: 是否成功關閉
        """
        # 如果遊戲未運行，則直接返回
        if self.current_status == GameStatus.NOT_RUNNING:
            return True
        
        self.logger.info(f"正在{'強制' if force else ''}關閉遊戲")
        self.current_status = GameStatus.CLOSING
        
        try:
            if self.process_id:
                process = psutil.Process(self.process_id)
                
                if force:
                    # 強制終止進程
                    process.kill()
                else:
                    # 嘗試溫和地終止進程
                    process.terminate()
                    
                    # 等待進程結束
                    try:
                        process.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        # 如果超時，則強制終止
                        self.logger.warning("進程未能正常終止，正在強制終止")
                        process.kill()
                
                self.logger.info("遊戲已關閉")
                self.current_status = GameStatus.NOT_RUNNING
                self.process_id = None
                self.start_time = None
                return True
            
            else:
                # 如果沒有進程ID，嘗試通過進程名稱查找並終止
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] == self.process_name:
                        if force:
                            proc.kill()
                        else:
                            proc.terminate()
                        
                        self.logger.info("遊戲已關閉")
                        self.current_status = GameStatus.NOT_RUNNING
                        self.process_id = None
                        self.start_time = None
                        return True
            
            self.logger.warning("找不到遊戲進程，無法關閉")
            self.current_status = GameStatus.NOT_RUNNING
            return False
        
        except Exception as e:
            self.logger.error(f"關閉遊戲時出錯: {str(e)}")
            # 假設遊戲已經關閉
            self.current_status = GameStatus.NOT_RUNNING
            self.process_id = None
            self.start_time = None
            return False
    
    def restart_game(self):
        """重啟遊戲
        
        Returns:
            bool: 是否成功重啟
        """
        self.logger.info("正在重啟遊戲")
        
        # 先關閉遊戲
        if not self.close_game(force=True):
            self.logger.warning("無法正確關閉遊戲，但仍將嘗試重新啟動")
        
        # 等待一段時間確保進程已完全終止
        time.sleep(3)
        
        # 啟動遊戲
        return self.start_game()
    
    def handle_maintenance(self):
        """處理伺服器維護
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.info("正在處理伺服器維護情況")
        
        # 在維護狀態下，可以選擇關閉遊戲或等待
        # 這裡選擇保持遊戲運行，並定期檢查
        
        # 更新狀態
        self.current_status = GameStatus.MAINTENANCE
        
        # 成功處理
        return True
    
    def handle_remote_login(self):
        """處理異地登入
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.info("正在處理異地登入情況")
        
        # 對於異地登入，通常需要重新啟動遊戲
        # 嘗試重啟遊戲
        return self.restart_game()
    
    def handle_scheduled_restart(self):
        """處理定期重啟
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.info("執行計劃中的遊戲重啟")
        
        # 簡單地重啟遊戲
        return self.restart_game()
    
    def _find_game_process(self):
        """查找遊戲進程
        
        Returns:
            psutil.Process: 進程對象，如果未找到則返回None
        """
        # 如果已有進程ID，則嘗試直接獲取
        if self.process_id:
            try:
                process = psutil.Process(self.process_id)
                # 檢查進程是否還在運行中
                if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                    return process
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # 如果通過ID找不到，則嘗試通過進程名稱查找
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == self.process_name:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return None
    
    def _find_game_window(self):
        """查找遊戲窗口
        
        Returns:
            bool: 是否找到遊戲窗口
        """
        import win32gui
        
        # 定義回調函數以找到窗口
        def enum_windows_callback(hwnd, result):
            title = win32gui.GetWindowText(hwnd)
            if self.window_title in title and win32gui.IsWindowVisible(hwnd):
                result.append(hwnd)
            return True
        
        window_handles = []
        win32gui.EnumWindows(enum_windows_callback, window_handles)
        
        return len(window_handles) > 0
    
    def _is_process_responding(self, process):
        """檢查進程是否響應
        
        Args:
            process (psutil.Process): 進程對象
        
        Returns:
            bool: 進程是否響應
        """
        try:
            # 檢查進程狀態
            status = process.status()
            
            # 如果進程狀態不是正常運行，則認為沒有響應
            if status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                return False
            
            # 如果能獲取到CPU時間，則認為進程在響應
            process.cpu_percent()
            return True
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False