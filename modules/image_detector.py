#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
圖像識別器模組
負責屏幕截圖與圖像處理，提供模板匹配等功能
"""

import os
import time
import logging
import numpy as np
import cv2
import pyautogui
from PIL import Image, ImageGrab

class ImageDetector:
    """圖像識別器類，提供屏幕截圖和模板匹配功能"""
    
    def __init__(self, config):
        """初始化圖像識別器
        
        Args:
            config (dict): 系統配置
        """
        self.config = config
        self.logger = logging.getLogger("ImageDetector")
        
        # 圖像緩存
        self.image_cache = {}
        
        # 屏幕相關
        self.last_screen_image = None
        self.last_full_screen_time = 0
        self.screen_refresh_interval = config['image_detection']['screen_refresh_interval']
        
        # 匹配閾值
        self.default_threshold = config['image_detection']['default_threshold']
        self.thresholds = config['image_detection'].get('thresholds', {})
        
        # 確保圖像目錄存在
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.images_dir = os.path.join(self.base_dir, 'images')
        
        self.logger.info("圖像識別器初始化完成")
    
    def load_template(self, template_path):
        """加載模板圖像
        
        Args:
            template_path (str): 模板圖像路徑，相對於images目錄
            
        Returns:
            numpy.ndarray: 模板圖像
        """
        # 檢查是否已緩存
        if template_path in self.image_cache:
            return self.image_cache[template_path]
        
        # 構建完整路徑
        full_path = os.path.join(self.images_dir, template_path)
        
        try:
            # 使用OpenCV加載圖像
            template = cv2.imread(full_path, cv2.IMREAD_UNCHANGED)
            
            if template is None:
                self.logger.error(f"無法加載模板圖像: {full_path}")
                return None
            
            # 如果圖像有Alpha通道，則處理透明度
            if template.shape[2] == 4:
                # 分離BGR和Alpha通道
                bgr = template[:, :, 0:3]
                alpha = template[:, :, 3]
                
                # 創建Alpha遮罩
                alpha_mask = alpha / 255.0
                
                # 處理透明背景
                for c in range(0, 3):
                    bgr[:, :, c] = bgr[:, :, c] * alpha_mask
                
                template = bgr
            
            # 緩存模板
            self.image_cache[template_path] = template
            
            return template
        
        except Exception as e:
            self.logger.error(f"加載模板圖像時出錯: {str(e)}")
            return None
    
    def get_screen_image(self, region=None, force_refresh=False):
        """獲取屏幕截圖
        
        Args:
            region (tuple, optional): 截圖區域 (x, y, width, height)
            force_refresh (bool, optional): 是否強制刷新
            
        Returns:
            numpy.ndarray: 屏幕圖像
        """
        current_time = time.time()
        
        # 如果指定了區域且有全屏截圖，則從全屏截圖中裁剪
        if region and self.last_screen_image is not None and not force_refresh:
            try:
                x, y, width, height = region
                # 確保區域有效
                max_h, max_w = self.last_screen_image.shape[:2]
                if x < max_w and y < max_h:
                    # 調整區域以確保不超出邊界
                    width = min(width, max_w - x)
                    height = min(height, max_h - y)
                    if width > 0 and height > 0:
                        # 從全屏圖像裁剪
                        return self.last_screen_image[y:y+height, x:x+width].copy()
            except Exception as e:
                self.logger.warning(f"從全屏截圖裁剪時出錯: {str(e)}")
        
        # 決定是否需要重新截圖
        need_refresh = (
            force_refresh or 
            self.last_screen_image is None or 
            (current_time - self.last_full_screen_time) > self.screen_refresh_interval
        )
        
        if need_refresh:
            try:
                # 使用PIL進行截圖
                if region:
                    screenshot = ImageGrab.grab(bbox=region)
                else:
                    screenshot = ImageGrab.grab()
                
                # 轉換為OpenCV格式 (BGR)
                screen_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # 如果是全屏截圖，則更新緩存
                if not region:
                    self.last_screen_image = screen_image
                    self.last_full_screen_time = current_time
                
                return screen_image
            
            except Exception as e:
                self.logger.error(f"獲取屏幕截圖時出錯: {str(e)}")
                return None
        
        # 如果不需要刷新且請求全屏，則返回緩存的全屏圖像
        elif not region:
            return self.last_screen_image
        
        # 如果不需要刷新但請求區域，則進行全屏截圖並裁剪
        else:
            try:
                # 更新全屏截圖
                screenshot = ImageGrab.grab()
                self.last_screen_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                self.last_full_screen_time = current_time
                
                # 裁剪區域
                x, y, width, height = region
                return self.last_screen_image[y:y+height, x:x+width].copy()
            
            except Exception as e:
                self.logger.error(f"獲取區域截圖時出錯: {str(e)}")
                return None
    
    def find_template(self, template_path, threshold=None, region=None, max_results=1):
        """查找模板
        
        Args:
            template_path (str): 模板圖像路徑
            threshold (float, optional): 匹配閾值
            region (tuple, optional): 搜索區域 (x, y, width, height)
            max_results (int, optional): 最大返回結果數
            
        Returns:
            list: 匹配位置列表 [(x, y), ...]
        """
        # 加載模板
        template = self.load_template(template_path)
        if template is None:
            self.logger.error(f"模板加載失敗: {template_path}")
            return []
        
        # 獲取屏幕圖像
        screen = self.get_screen_image(region)
        if screen is None:
            self.logger.error("獲取屏幕截圖失敗")
            return []
        
        # 決定匹配閾值
        if threshold is None:
            # 檢查是否有特定模板的閾值設置
            for key, value in self.thresholds.items():
                if key in template_path:
                    threshold = value
                    break
            # 否則使用默認閾值
            if threshold is None:
                threshold = self.default_threshold
        
        try:
            # 確保模板不大於屏幕
            if template.shape[0] > screen.shape[0] or template.shape[1] > screen.shape[1]:
                self.logger.warning(f"模板大小 {template.shape[:2]} 大於屏幕區域 {screen.shape[:2]}")
                return []
            
            # 進行模板匹配
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            
            # 查找匹配位置
            locations = []
            h, w = template.shape[:2]
            
            while len(locations) < max_results:
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold:
                    # 計算中心位置
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    
                    # 添加區域偏移
                    if region:
                        center_x += region[0]
                        center_y += region[1]
                    
                    locations.append((center_x, center_y))
                    
                    # 在結果中去除該匹配區域以找到下一個匹配
                    if len(locations) < max_results:
                        cv2.rectangle(
                            result, 
                            max_loc, 
                            (max_loc[0] + w, max_loc[1] + h), 
                            (0, 0, 0), 
                            -1
                        )
                else:
                    break
            
            return locations
        
        except Exception as e:
            self.logger.error(f"查找模板時出錯: {str(e)}")
            return []
    
    def wait_for_template(self, template_path, timeout=10, threshold=None, region=None):
        """等待模板出現
        
        Args:
            template_path (str): 模板圖像路徑
            timeout (int, optional): 超時秒數
            threshold (float, optional): 匹配閾值
            region (tuple, optional): 搜索區域 (x, y, width, height)
            
        Returns:
            tuple: 成功時返回匹配位置 (x, y)，失敗時返回 None
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            match = self.find_template(template_path, threshold, region)
            
            if match:
                self.logger.debug(f"在 {time.time() - start_time:.2f} 秒後找到模板 {template_path}")
                return match[0]
            
            # 短暫休眠以減少CPU使用
            time.sleep(0.2)
        
        self.logger.warning(f"等待模板 {template_path} 超時，已等待 {timeout} 秒")
        return None
    
    def find_multiple_templates(self, templates_config, region=None):
        """查找多個模板
        
        Args:
            templates_config (dict): 模板配置字典
                {
                    "name1": {"template": "path/to/template1.png", "threshold": 0.8},
                    "name2": {"template": "path/to/template2.png", "threshold": 0.9}
                }
            region (tuple, optional): 搜索區域 (x, y, width, height)
            
        Returns:
            dict: 匹配結果字典 {"name1": [(x1, y1), ...], "name2": [(x2, y2), ...]}
        """
        results = {}
        
        # 獲取區域屏幕截圖
        screen = self.get_screen_image(region)
        if screen is None:
            self.logger.error("獲取屏幕截圖失敗")
            return results
        
        for name, config in templates_config.items():
            template_path = config["template"]
            threshold = config.get("threshold", self.default_threshold)
            max_results = config.get("max_results", 10)
            
            matches = self.find_template(template_path, threshold, region, max_results)
            if matches:
                results[name] = matches
        
        return results
    
    def clear_cache(self):
        """清理圖像緩存"""
        self.logger.debug("清理圖像緩存")
        self.image_cache.clear()
        self.last_screen_image = None
        self.last_full_screen_time = 0