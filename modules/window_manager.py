#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
視窗管理器模組
負責管理遊戲窗口的位置、大小和狀態
"""

import time
import logging
import win32gui
import win32con
import win32process
import ctypes
import psutil
import threading
from ctypes import wintypes

class WindowManager:
    """視窗管理器類，提供窗口控制功能"""
    
    def __init__(self, config):
        """初始化視窗管理器
        
        Args:
            config (dict): 系統配置
        """
        self.config = config
        self.logger = logging.getLogger("WindowManager")
        
        # 從配置中獲取窗口位置和大小
        window_config = config['game']['position']
        self.window_position = (window_config['x'], window_config['y'])
        self.window_size = (window_config['width'], window_config['height'])
        
        # 是否強制設置窗口位置和大小
        self.force_window_position = config['game'].get('force_window_position', False)
        
        # 檢查間隔(秒)
        self.window_position_check_interval = config['game'].get('window_position_check_interval', 10)
        
        # 上次檢查時間
        self.last_window_check_time = 0
        
        # 窗口處理句柄
        self.window_handle = None
        
        # 啟動窗口位置監控線程（如果需要）
        if self.force_window_position:
            self._start_window_position_monitor()
        
        self.logger.info("視窗管理器初始化完成")
        self.logger.info(f"窗口設置: 位置={self.window_position}, 大小={self.window_size}")
        
    def _start_window_position_monitor(self):
        """啟動窗口位置監控線程"""
        def monitor_window_position():
            self.logger.info("窗口位置監控線程已啟動")
            while True:
                try:
                    # 檢查遊戲窗口是否存在
                    hwnd = self.get_window_handle(refresh=True)
                    if hwnd:
                        # 檢查當前窗口位置和大小
                        current_rect = win32gui.GetWindowRect(hwnd)
                        current_x, current_y, current_x2, current_y2 = current_rect
                        current_width = current_x2 - current_x
                        current_height = current_y2 - current_y
                        
                        # 檢查是否需要調整
                        expected_x, expected_y = self.window_position
                        expected_width, expected_height = self.window_size
                        
                        position_changed = (
                            abs(current_x - expected_x) > 5 or 
                            abs(current_y - expected_y) > 5 or
                            abs(current_width - expected_width) > 5 or
                            abs(current_height - expected_height) > 5
                        )
                        
                        if position_changed:
                            self.logger.info(f"窗口位置或大小已變更，將調整回設定值")
                            self.logger.debug(f"當前: ({current_x}, {current_y}, {current_width}x{current_height})")
                            self.logger.debug(f"預期: ({expected_x}, {expected_y}, {expected_width}x{expected_height})")
                            self.set_window_position()
                    
                except Exception as e:
                    self.logger.error(f"窗口位置監控出錯: {str(e)}")
                
                # 等待下一次檢查
                time.sleep(self.window_position_check_interval)
        
        # 在背景線程中執行監控
        monitor_thread = threading.Thread(target=monitor_window_position, daemon=True)
        monitor_thread.start()
    
    def find_window_by_title(self, title, partial_match=True):
        """根據標題尋找窗口
        
        Args:
            title (str): 窗口標題
            partial_match (bool, optional): 是否部分匹配
        
        Returns:
            int: 窗口句柄，如果未找到則返回0
        """
        window_handles = []
        
        def enum_windows_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if partial_match and title in window_text:
                    results.append(hwnd)
                elif not partial_match and title == window_text:
                    results.append(hwnd)
            return True
        
        win32gui.EnumWindows(enum_windows_callback, window_handles)
        
        if window_handles:
            # 如果找到多個窗口，選擇第一個
            self.logger.debug(f"找到 {len(window_handles)} 個匹配標題 '{title}' 的窗口")
            return window_handles[0]
        
        self.logger.debug(f"找不到標題為 '{title}' 的窗口")
        return 0
    
    def find_window_by_process(self, process_name):
        """根據進程名稱尋找窗口
        
        Args:
            process_name (str): 進程名稱
        
        Returns:
            int: 窗口句柄，如果未找到則返回0
        """
        window_handles = []
        
        # 先查找進程ID
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == process_name:
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if not pids:
            self.logger.debug(f"找不到名為 '{process_name}' 的進程")
            return 0
        
        # 根據進程ID查找窗口
        def enum_windows_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid in pids:
                        results.append(hwnd)
                except:
                    pass
            return True
        
        win32gui.EnumWindows(enum_windows_callback, window_handles)
        
        if window_handles:
            # 如果找到多個窗口，選擇第一個
            self.logger.debug(f"找到 {len(window_handles)} 個屬於進程 '{process_name}' 的窗口")
            return window_handles[0]
        
        self.logger.debug(f"找不到屬於進程 '{process_name}' 的窗口")
        return 0
    
    def get_window_handle(self, refresh=False):
        """獲取遊戲窗口句柄
        
        Args:
            refresh (bool, optional): 是否強制刷新
        
        Returns:
            int: 窗口句柄
        """
        current_time = time.time()
        
        # 如果已有句柄且不需要刷新，則直接返回
        if self.window_handle and not refresh and current_time - self.last_window_check_time < 5:
            # 檢查窗口是否還存在
            if win32gui.IsWindow(self.window_handle):
                return self.window_handle
        
        # 更新檢查時間
        self.last_window_check_time = current_time
        
        # 嘗試根據標題查找窗口
        window_title = self.config['game']['window_title']
        self.window_handle = self.find_window_by_title(window_title)
        
        # 如果根據標題找不到，則嘗試根據進程名稱查找
        if not self.window_handle:
            process_name = self.config['game']['process_name']
            self.window_handle = self.find_window_by_process(process_name)
        
        return self.window_handle
    
    def bring_to_foreground(self, window_title=None):
        """將窗口置於前台
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
        
        Returns:
            bool: 是否成功
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            self.logger.warning(f"找不到標題為 '{window_title}' 的窗口，無法置前")
            return False
        
        # 檢查窗口是否已經在前台
        if self.is_foreground_window(window_title):
            return True
        
        try:
            # 嘗試激活窗口並置前
            # 首先確保窗口未最小化
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 使用SetForegroundWindow函數將窗口置前
            result = win32gui.SetForegroundWindow(hwnd)
            
            # 如果失敗，嘗試其他方法
            if not result:
                # 使用高級技術
                # 1. 獲取當前前台窗口線程
                current_thread = win32gui.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]
                # 2. 獲取目標窗口線程
                target_thread = win32gui.GetWindowThreadProcessId(hwnd)[0]
                # 3. 連接這兩個線程的輸入狀態，這可以允許SetForegroundWindow成功
                ctypes.windll.user32.AttachThreadInput(current_thread, target_thread, True)
                # 4. 再次嘗試設置前台窗口
                win32gui.SetForegroundWindow(hwnd)
                # 5. 分離線程輸入
                ctypes.windll.user32.AttachThreadInput(current_thread, target_thread, False)
            
            # 給窗口一些時間來響應
            time.sleep(0.1)
            
            # 確認窗口是否成功置前
            is_foreground = self.is_foreground_window(window_title)
            self.logger.debug(f"將窗口 '{window_title}' 置前{'成功' if is_foreground else '失敗'}")
            return is_foreground
        
        except Exception as e:
            self.logger.error(f"將窗口 '{window_title}' 置前時出錯: {str(e)}")
            return False
    
    def set_window_position(self, window_title=None, x=None, y=None, width=None, height=None):
        """設置窗口位置和大小
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
            x (int, optional): 左上角X坐標
            y (int, optional): 左上角Y坐標
            width (int, optional): 窗口寬度
            height (int, optional): 窗口高度
        
        Returns:
            bool: 是否成功
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            self.logger.warning(f"找不到標題為 '{window_title}' 的窗口，無法設置位置和大小")
            return False
        
        # 如果沒有指定參數，則使用配置中的設置
        if x is None:
            x = self.window_position[0]
        if y is None:
            y = self.window_position[1]
        if width is None:
            width = self.window_size[0]
        if height is None:
            height = self.window_size[1]
        
        try:
            # 首先確保窗口未最小化
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)  # 等待窗口恢復
            
            # 確保窗口為正常狀態（不是最大化）
            # 修正: 使用 GetWindowPlacement 來檢查窗口是否最大化
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_NORMAL)
                time.sleep(0.3)  # 等待窗口恢復到正常狀態
            
            # 獲取當前窗口樣式
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            
            # 移除某些可能阻止調整大小的樣式
            if style & win32con.WS_BORDER:
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style & ~win32con.WS_BORDER)
            
            # 設置窗口位置和大小
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            
            # 等待窗口調整完成
            time.sleep(0.3)
            
            # 記錄設置後的實際位置和大小
            actual_rect = win32gui.GetWindowRect(hwnd)
            actual_x, actual_y, actual_x2, actual_y2 = actual_rect
            actual_width = actual_x2 - actual_x
            actual_height = actual_y2 - actual_y
            
            self.logger.debug(f"設置窗口位置: 預期=({x}, {y}, {width}x{height}), 實際=({actual_x}, {actual_y}, {actual_width}x{actual_height})")
            
            # 更新記錄的位置和大小
            if abs(actual_x - x) < 10 and abs(actual_y - y) < 10 and abs(actual_width - width) < 10 and abs(actual_height - height) < 10:
                self.window_position = (x, y)
                self.window_size = (width, height)
                return True
            else:
                self.logger.warning(f"窗口位置設置不符合預期")
                return False
            
        except Exception as e:
            self.logger.error(f"設置窗口位置和大小時出錯: {str(e)}")
            return False
    
    def is_foreground_window(self, window_title=None):
        """檢查窗口是否為前景窗口
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
        
        Returns:
            bool: 是否為前景窗口
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            return False
        
        # 獲取當前前景窗口句柄
        foreground_hwnd = win32gui.GetForegroundWindow()
        
        return hwnd == foreground_hwnd
    
    def get_window_size(self, window_title=None):
        """獲取窗口大小
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
        
        Returns:
            tuple: (width, height)，如果窗口不存在則返回None
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            return None
        
        # 獲取窗口矩形
        rect = win32gui.GetWindowRect(hwnd)
        x1, y1, x2, y2 = rect
        
        return (x2 - x1, y2 - y1)
    
    def get_client_size(self, window_title=None):
        """獲取窗口客戶區大小
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
        
        Returns:
            tuple: (width, height)，如果窗口不存在則返回None
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            return None
        
        # 獲取客戶區矩形
        rect = wintypes.RECT()
        ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
        
        return (rect.right - rect.left, rect.bottom - rect.top)
    
    def maximize_window(self, window_title=None):
        """最大化窗口
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
        
        Returns:
            bool: 是否成功
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            self.logger.warning(f"找不到標題為 '{window_title}' 的窗口，無法最大化")
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return True
        except Exception as e:
            self.logger.error(f"最大化窗口 '{window_title}' 時出錯: {str(e)}")
            return False
    
    def minimize_window(self, window_title=None):
        """最小化窗口
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
        
        Returns:
            bool: 是否成功
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            self.logger.warning(f"找不到標題為 '{window_title}' 的窗口，無法最小化")
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            self.logger.error(f"最小化窗口 '{window_title}' 時出錯: {str(e)}")
            return False
    
    def restore_window(self, window_title=None):
        """還原窗口
        
        Args:
            window_title (str, optional): 窗口標題，如果為None則使用配置中的窗口標題
        
        Returns:
            bool: 是否成功
        """
        # 如果沒有指定窗口標題，則使用配置中的窗口標題
        if window_title is None:
            window_title = self.config['game']['window_title']
        
        # 獲取窗口句柄
        hwnd = self.find_window_by_title(window_title) if window_title else self.get_window_handle(refresh=True)
        
        if not hwnd:
            self.logger.warning(f"找不到標題為 '{window_title}' 的窗口，無法還原")
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return True
        except Exception as e:
            self.logger.error(f"還原窗口 '{window_title}' 時出錯: {str(e)}")
            return False
    
    def shutdown(self):
        """清理資源"""
        self.logger.info("關閉視窗管理器")
        # 目前沒有需要清理的資源