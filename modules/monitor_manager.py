#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
監控管理器模組
負責全局監控項管理與檢測
"""

import time
import logging
import threading

class Monitor:
    """監控項類定義"""
    def __init__(self, name, priority, handler, patterns=None, check_interval=10):
        """初始化監控項
        
        Args:
            name (str): 監控項名稱
            priority (int): 優先級(0-100)
            handler (function): 處理函數
            patterns (list, optional): 要檢測的模式列表
            check_interval (int, optional): 檢查間隔(秒)
        """
        self.name = name
        self.priority = priority
        self.handler = handler
        self.patterns = patterns or []
        self.check_interval = check_interval
        self.is_active = True
        self.last_check_time = 0
        self.last_match_time = 0
    
    def should_check(self):
        """檢查是否應該執行檢測
        
        Returns:
            bool: 是否應該執行
        """
        # 如果不活躍則不檢測
        if not self.is_active:
            return False
        
        # 檢查間隔時間
        return (time.time() - self.last_check_time) >= self.check_interval

class MonitorManager:
    """監控管理器類"""
    def __init__(self):
        """初始化監控管理器"""
        self.logger = logging.getLogger("MonitorManager")
        self.global_monitors = []  # 全局監控項列表
        self.is_paused = False  # 是否暫停
        self.lock = threading.Lock()  # 線程鎖
        
        self.logger.info("監控管理器初始化完成")
    
    def add_global_monitor(self, name, priority, handler, patterns=None, check_interval=10):
        """添加全局監控項
        
        Args:
            name (str): 監控項名稱
            priority (int): 優先級(0-100)
            handler (function): 處理函數
            patterns (list, optional): 要檢測的模式列表
            check_interval (int, optional): 檢查間隔(秒)
        
        Returns:
            Monitor: 添加的監控項
        """
        with self.lock:
            # 檢查是否已存在同名監控項
            for monitor in self.global_monitors:
                if monitor.name == name:
                    self.logger.warning(f"已存在名為 '{name}' 的監控項，無法添加")
                    return None
            
            # 創建新監控項
            monitor = Monitor(name, priority, handler, patterns, check_interval)
            self.global_monitors.append(monitor)
            
            # 按優先級排序監控列表
            self.global_monitors.sort(key=lambda m: m.priority, reverse=True)
            
            self.logger.info(f"添加監控項 '{name}' (優先級: {priority})")
            return monitor
    
    def remove_global_monitor(self, name):
        """移除全局監控項
        
        Args:
            name (str): 監控項名稱
        
        Returns:
            bool: 是否成功移除
        """
        with self.lock:
            # 查找監控項
            for i, monitor in enumerate(self.global_monitors):
                if monitor.name == name:
                    # 移除監控項
                    self.global_monitors.pop(i)
                    self.logger.info(f"移除監控項 '{name}'")
                    return True
            
            self.logger.warning(f"找不到名為 '{name}' 的監控項，無法移除")
            return False
    
    def pause_global_monitoring(self):
        """暫停所有監控"""
        with self.lock:
            self.is_paused = True
            self.logger.info("全局監控已暫停")
    
    def resume_global_monitoring(self):
        """恢復所有監控"""
        with self.lock:
            self.is_paused = False
            self.logger.info("全局監控已恢復")
    
    def check_global_monitors(self, screen_image):
        """檢查所有全局監控項
        
        Args:
            screen_image: 當前屏幕圖像
        
        Returns:
            bool: 是否有監控項發現匹配並處理
        """
        # 如果監控已暫停，則不執行任何檢測
        if self.is_paused:
            return False
        
        with self.lock:
            current_time = time.time()
            
            # 按優先級檢查所有監控項
            for monitor in self.global_monitors:
                # 檢查是否應該執行檢測
                if not monitor.should_check():
                    continue
                
                # 更新最後檢查時間
                monitor.last_check_time = current_time
                
                # 如果沒有模式需要檢測，則跳過
                if not monitor.patterns:
                    continue
                
                # 檢測模式
                match_info = self._check_patterns(monitor, screen_image)
                
                # 如果有匹配，則調用處理器
                if match_info:
                    monitor.last_match_time = current_time
                    
                    try:
                        # 調用處理函數
                        self.logger.info(f"監控項 '{monitor.name}' 檢測到匹配，正在處理")
                        result = monitor.handler(match_info)
                        
                        if result:
                            self.logger.info(f"監控項 '{monitor.name}' 處理成功")
                        else:
                            self.logger.warning(f"監控項 '{monitor.name}' 處理失敗")
                        
                        # 不論處理成功與否，都返回True表示找到了匹配
                        return True
                    
                    except Exception as e:
                        self.logger.error(f"監控項 '{monitor.name}' 處理異常: {str(e)}")
                        return True  # 仍然返回True，因為發現了匹配
            
            # 沒有監控項發現匹配
            return False
    
    def _check_patterns(self, monitor, screen_image):
        """檢查監控項的模式是否匹配
        
        Args:
            monitor (Monitor): 監控項
            screen_image: 當前屏幕圖像
        
        Returns:
            dict: 匹配信息，如果沒有匹配則返回None
        """
        # 這個方法需要根據具體的模式類型來實現
        # 例如，可能是模板匹配、顏色檢測等
        
        # 假設patterns是一個字典列表，每個字典包含pattern和detector
        for pattern in monitor.patterns:
            detector = pattern.get('detector')
            template = pattern.get('template')
            threshold = pattern.get('threshold', 0.8)
            region = pattern.get('region')
            
            if detector and template:
                # 使用指定的檢測器進行檢測
                match = detector(template, screen_image, threshold, region)
                if match:
                    return {
                        'monitor': monitor.name,
                        'pattern': template,
                        'match': match
                    }
        
        # 沒有匹配
        return None
    
    def force_check_all(self, screen_image=None):
        """強制檢查所有監控項
        
        Args:
            screen_image: 當前屏幕圖像，如果為None則會重新截取
        
        Returns:
            bool: 是否有監控項發現匹配並處理
        """
        # 如果沒有提供屏幕圖像，則使用image_detector獲取
        # 注意: 這裡假設外部提供了屏幕圖像，因為這個類沒有直接引用image_detector
        
        # 臨時解除暫停狀態
        original_pause_state = self.is_paused
        self.is_paused = False
        
        # 執行檢查
        result = self.check_global_monitors(screen_image)
        
        # 恢復原來的暫停狀態
        self.is_paused = original_pause_state
        
        return result
    
    def get_monitor(self, name):
        """獲取監控項
        
        Args:
            name (str): 監控項名稱
        
        Returns:
            Monitor: 監控項對象，如果不存在則返回None
        """
        for monitor in self.global_monitors:
            if monitor.name == name:
                return monitor
        return None
    
    def activate_monitor(self, name):
        """啟用監控項
        
        Args:
            name (str): 監控項名稱
        
        Returns:
            bool: 是否成功啟用
        """
        monitor = self.get_monitor(name)
        if monitor:
            with self.lock:
                monitor.is_active = True
                self.logger.info(f"監控項 '{name}' 已啟用")
            return True
        
        self.logger.warning(f"找不到名為 '{name}' 的監控項，無法啟用")
        return False
    
    def deactivate_monitor(self, name):
        """禁用監控項
        
        Args:
            name (str): 監控項名稱
        
        Returns:
            bool: 是否成功禁用
        """
        monitor = self.get_monitor(name)
        if monitor:
            with self.lock:
                monitor.is_active = False
                self.logger.info(f"監控項 '{name}' 已禁用")
            return True
        
        self.logger.warning(f"找不到名為 '{name}' 的監控項，無法禁用")
        return False
    
    def get_all_monitors_status(self):
        """獲取所有監控項的狀態
        
        Returns:
            list: 監控項狀態列表
        """
        status_list = []
        
        for monitor in self.global_monitors:
            status = {
                "name": monitor.name,
                "priority": monitor.priority,
                "active": monitor.is_active,
                "check_interval": monitor.check_interval,
                "last_check_time": monitor.last_check_time,
                "last_match_time": monitor.last_match_time
            }
            status_list.append(status)
        
        return status_list