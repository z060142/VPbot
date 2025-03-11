#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
例外處理器模組
負責檢測並處理各種異常情況
"""

import time
import logging

class ExceptionHandler:
    """例外處理器類，用於處理遊戲中的各種例外情況"""
    
    def __init__(self, config, image_detector, action_executor):
        """初始化例外處理器
        
        Args:
            config (dict): 系統配置
            image_detector (ImageDetector): 圖像識別器
            action_executor (ActionExecutor): 動作執行器
        """
        self.config = config
        self.image_detector = image_detector
        self.action_executor = action_executor
        self.logger = logging.getLogger("ExceptionHandler")
        
        # 從配置載入例外處理設置
        self.exceptions_config = config.get('exceptions', {})
        
        self.logger.info("例外處理器初始化完成")
    
    def register_exception_monitors(self, monitor_manager):
        """註冊所有例外監控項
        
        Args:
            monitor_manager (MonitorManager): 監控管理器
        """
        self.logger.info("註冊例外監控項")
        
        # 註冊伺服器維護監控
        if 'maintenance' in self.exceptions_config:
            maintenance_config = self.exceptions_config['maintenance']
            monitor_manager.add_global_monitor(
                name="maintenance_monitor",
                priority=90,  # 高優先級
                handler=self.handle_maintenance,
                patterns=[{
                    'detector': self._template_detector,
                    'template': maintenance_config['template'],
                    'threshold': maintenance_config.get('threshold', 0.85)
                }],
                check_interval=maintenance_config.get('check_interval', 60)
            )
            self.logger.info("已註冊伺服器維護監控項")
        
        # 註冊異地登入監控
        if 'remote_login' in self.exceptions_config:
            remote_login_config = self.exceptions_config['remote_login']
            monitor_manager.add_global_monitor(
                name="remote_login_monitor",
                priority=100,  # 最高優先級
                handler=self.handle_remote_login,
                patterns=[{
                    'detector': self._template_detector,
                    'template': remote_login_config['template'],
                    'threshold': remote_login_config.get('threshold', 0.9)
                }],
                check_interval=remote_login_config.get('check_interval', 30)
            )
            self.logger.info("已註冊異地登入監控項")
        
        # 註冊彈窗廣告監控
        if 'popup_ad' in self.exceptions_config:
            popup_ad_config = self.exceptions_config['popup_ad']
            
            patterns = []
            # 支持多個模板
            for template in popup_ad_config.get('templates', []):
                patterns.append({
                    'detector': self._template_detector,
                    'template': template,
                    'threshold': popup_ad_config.get('threshold', 0.8)
                })
            
            if patterns:
                monitor_manager.add_global_monitor(
                    name="popup_ad_monitor",
                    priority=70,  # 中優先級
                    handler=self.handle_popup_ad,
                    patterns=patterns,
                    check_interval=popup_ad_config.get('check_interval', 20)
                )
                self.logger.info("已註冊彈窗廣告監控項")
        
        # 註冊網絡錯誤監控
        if 'network_error' in self.exceptions_config:
            network_error_config = self.exceptions_config['network_error']
            monitor_manager.add_global_monitor(
                name="network_error_monitor",
                priority=80,  # 高優先級
                handler=self.handle_network_error,
                patterns=[{
                    'detector': self._template_detector,
                    'template': network_error_config['template'],
                    'threshold': network_error_config.get('threshold', 0.9)
                }],
                check_interval=network_error_config.get('check_interval', 30)
            )
            self.logger.info("已註冊網絡錯誤監控項")
        
        # 可以根據需要添加更多監控項
    
    def _template_detector(self, template_path, screen_image, threshold, region=None):
        """模板檢測器
        
        Args:
            template_path (str): 模板路徑
            screen_image: 屏幕圖像
            threshold (float): 匹配閾值
            region (tuple, optional): 搜索區域
        
        Returns:
            tuple: 匹配位置，如果沒有匹配則返回None
        """
        # 使用圖像識別器進行模板匹配
        matches = self.image_detector.find_template(
            template_path,
            threshold=threshold,
            region=region,
            max_results=1
        )
        
        if matches:
            return matches[0]  # 返回第一個匹配位置
        return None
    
    def handle_maintenance(self, match_info):
        """處理伺服器維護
        
        Args:
            match_info (dict): 匹配信息
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.info("檢測到伺服器維護通知")
        
        # 獲取匹配位置
        x, y = match_info['match']
        
        # 基本處理：尋找並點擊確認按鈕
        confirm_button = self.image_detector.find_template("ui/confirm_button.png")
        if confirm_button:
            confirm_x, confirm_y = confirm_button[0], confirm_button[1]
            self.action_executor.click_at(confirm_x, confirm_y)
            self.logger.info("已點擊維護通知確認按鈕")
            time.sleep(1)
            return True
        
        # 如果找不到確認按鈕，可以嘗試點擊關閉按鈕 (X)
        close_button = self.image_detector.find_template("ui/close_button.png")
        if close_button:
            close_x, close_y = close_button[0], close_button[1]
            self.action_executor.click_at(close_x, close_y)
            self.logger.info("已點擊維護通知關閉按鈕")
            time.sleep(1)
            return True
        
        # 如果都找不到，可以嘗試按ESC
        self.action_executor.key_press('esc')
        self.logger.info("已嘗試按ESC關閉維護通知")
        time.sleep(1)
        
        # 無法確定是否處理成功，返回True以防再次觸發
        return True
    
    def handle_remote_login(self, match_info):
        """處理異地登入
        
        Args:
            match_info (dict): 匹配信息
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.warning("檢測到異地登入通知")
        
        # 獲取匹配位置
        x, y = match_info['match']
        
        # 基本處理：尋找並點擊確認按鈕
        confirm_button = self.image_detector.find_template("ui/confirm_button.png")
        if confirm_button:
            confirm_x, confirm_y = confirm_button[0], confirm_button[1]
            self.action_executor.click_at(confirm_x, confirm_y)
            self.logger.info("已點擊異地登入通知確認按鈕")
            time.sleep(1)
        
        # 不論是否找到確認按鈕，都需要重啟遊戲
        self.logger.info("需要重啟遊戲處理異地登入")
        
        # 返回True，實際重啟由game_manager通過檢測狀態來處理
        return True
    
    def handle_popup_ad(self, match_info):
        """處理彈窗廣告
        
        Args:
            match_info (dict): 匹配信息
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.info("檢測到彈窗廣告")
        
        # 獲取匹配位置
        x, y = match_info['match']
        
        # 基本處理：尋找並點擊關閉按鈕 (X)
        close_button = self.image_detector.find_template("ui/close_button.png")
        if close_button:
            close_x, close_y = close_button[0], close_button[1]
            self.action_executor.click_at(close_x, close_y)
            self.logger.info("已點擊彈窗廣告關閉按鈕")
            time.sleep(0.5)  # 短暫等待關閉動畫
            return True
        
        # 如果找不到關閉按鈕，可以嘗試點擊取消按鈕
        cancel_button = self.image_detector.find_template("ui/cancel_button.png")
        if cancel_button:
            cancel_x, cancel_y = cancel_button[0], cancel_button[1]
            self.action_executor.click_at(cancel_x, cancel_y)
            self.logger.info("已點擊彈窗廣告取消按鈕")
            time.sleep(0.5)
            return True
        
        # 如果都找不到，可以嘗試按ESC
        self.action_executor.key_press('esc')
        self.logger.info("已嘗試按ESC關閉彈窗廣告")
        time.sleep(0.5)
        
        # 無法確定是否處理成功，返回True以防再次觸發
        return True
    
    def handle_network_error(self, match_info):
        """處理網絡錯誤
        
        Args:
            match_info (dict): 匹配信息
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.warning("檢測到網絡錯誤")
        
        # 獲取匹配位置
        x, y = match_info['match']
        
        # 基本處理：尋找並點擊確認按鈕
        confirm_button = self.image_detector.find_template("ui/confirm_button.png")
        if confirm_button:
            confirm_x, confirm_y = confirm_button[0], confirm_button[1]
            self.action_executor.click_at(confirm_x, confirm_y)
            self.logger.info("已點擊網絡錯誤確認按鈕")
            time.sleep(1)
            return True
        
        # 如果找不到確認按鈕，可以嘗試點擊重試按鈕
        retry_button = self.image_detector.find_template("ui/retry_button.png")
        if retry_button:
            retry_x, retry_y = retry_button[0], retry_button[1]
            self.action_executor.click_at(retry_x, retry_y)
            self.logger.info("已點擊網絡錯誤重試按鈕")
            time.sleep(1)
            return True
        
        # 如果都找不到，可以嘗試按ESC
        self.action_executor.key_press('esc')
        self.logger.info("已嘗試按ESC關閉網絡錯誤")
        time.sleep(1)
        
        # 無法確定是否處理成功，返回True以防再次觸發
        return True
    
    def handle_wrong_screen(self, match_info):
        """處理畫面異常
        
        Args:
            match_info (dict): 匹配信息
        
        Returns:
            bool: 是否成功處理
        """
        self.logger.warning("檢測到畫面異常")
        
        # 嘗試按ESC回到主畫面
        self.action_executor.key_press('esc')
        time.sleep(1)
        
        # 檢查是否回到主畫面
        main_screen = self.image_detector.find_template("ui/main_screen_indicator.png")
        if main_screen:
            self.logger.info("已成功回到主畫面")
            return True
        
        # 如果還不是主畫面，再按一次ESC
        self.action_executor.key_press('esc')
        time.sleep(1)
        
        # 再次檢查
        main_screen = self.image_detector.find_template("ui/main_screen_indicator.png")
        if main_screen:
            self.logger.info("已成功回到主畫面")
            return True
        
        # 如果兩次ESC都失敗，嘗試點擊主頁按鈕
        home_button = self.image_detector.find_template("ui/home_button.png")
        if home_button:
            home_x, home_y = home_button[0], home_button[1]
            self.action_executor.click_at(home_x, home_y)
            self.logger.info("已點擊主頁按鈕")
            time.sleep(1)
            return True
        
        self.logger.warning("無法處理畫面異常")
        return False