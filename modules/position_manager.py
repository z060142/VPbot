#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
職位管理器模組
負責處理6個職位的申請處理和超時檢查
"""

import time
import logging
from enum import Enum

class Position:
    """職位類定義"""
    def __init__(self, id, name, index, config):
        """初始化職位
        
        Args:
            id (str): 職位唯一標識
            name (str): 職位名稱
            index (int): 索引(0-5)
            config (dict): 職位配置
        """
        self.id = id
        self.name = name
        self.index = index
        self.config = config
        self.is_enabled = config.get('enabled', True)
        self.application_region = config.get('application_region')
        self.time_region = config.get('time_region')  # 時間顯示區域
        self.overtime_threshold = config.get('overtime_threshold', 10)  # 超時閾值(分鐘)
        self.last_processed_time = 0  # 上次處理時間
        self.application_count = 0  # 申請數量統計
        self.overtime_count = 0  # 超時數量統計

class PositionManager:
    """職位管理類"""
    def __init__(self, config, image_detector, action_executor):
        """初始化職位管理器
        
        Args:
            config (dict): 系統配置
            image_detector (ImageDetector): 圖像識別器
            action_executor (ActionExecutor): 動作執行器
        """
        self.config = config
        self.image_detector = image_detector
        self.action_executor = action_executor
        self.logger = logging.getLogger("PositionManager")
        self.positions = []
        self._initialize_positions(config)
    
    def _initialize_positions(self, config):
        """從配置中初始化所有職位
        
        Args:
            config (dict): 系統配置
        """
        position_configs = config.get('positions', [])
        
        for index, position_config in enumerate(position_configs):
            position = Position(
                id=position_config.get('id'),
                name=position_config.get('name'),
                index=index,
                config=position_config
            )
            self.positions.append(position)
        
        self.logger.info(f"已初始化 {len(self.positions)} 個職位")
    
    def process_all_positions(self):
        """處理所有啟用的職位申請"""
        self.logger.info("開始處理所有職位申請")
        processed_count = 0
        
        for position in self.positions:
            if position.is_enabled:
                try:
                    result = self._process_single_position(position)
                    if result:
                        processed_count += 1
                        position.last_processed_time = time.time()
                except Exception as e:
                    self.logger.error(f"處理職位 '{position.name}' 時出錯: {str(e)}")
        
        self.logger.info(f"職位申請處理完成，處理了 {processed_count} 個職位")
        return processed_count > 0
    
    def _process_single_position(self, position):
        """處理單個職位的申請
        
        Args:
            position (Position): 職位對象
            
        Returns:
            bool: 是否成功處理
        """
        self.logger.info(f"處理職位 '{position.name}' 的申請")
        
        # 這裡需要根據實際遊戲界面實現申請處理邏輯
        # 下面是一個框架示例
        
        # 1. 檢查是否在申請畫面，如不在則導航
        if not self._navigate_to_application_screen():
            self.logger.error("無法導航至申請畫面")
            return False
        
        # 2. 點擊指定職位
        if not self._click_position(position):
            self.logger.info(f"職位 '{position.name}' 沒有申請或無法點擊")
            return False
        
        # 3. 檢測申請者列表
        applicants = self._detect_applicants()
        if not applicants:
            self.logger.info(f"職位 '{position.name}' 沒有申請者")
            # 返回申請畫面
            self._navigate_back_to_position_list()
            return False
        
        # 4. 處理申請者
        approved_count = self._approve_applicants(applicants)
        position.application_count += approved_count
        
        # 5. 返回申請畫面
        self._navigate_back_to_position_list()
        
        self.logger.info(f"職位 '{position.name}' 處理完成，批准了 {approved_count} 個申請")
        return approved_count > 0
    
    def check_all_overtime(self):
        """檢查所有啟用職位的超時情況"""
        self.logger.info("開始檢查所有職位超時情況")
        overtime_count = 0
        
        for position in self.positions:
            if position.is_enabled:
                try:
                    result = self._check_single_position_overtime(position)
                    if result:
                        overtime_count += 1
                except Exception as e:
                    self.logger.error(f"檢查職位 '{position.name}' 超時時出錯: {str(e)}")
        
        self.logger.info(f"超時檢查完成，處理了 {overtime_count} 個超時職位")
        return overtime_count > 0
    
    def _check_single_position_overtime(self, position):
        """檢查單個職位的超時情況
        
        Args:
            position (Position): 職位對象
            
        Returns:
            bool: 是否有超時處理
        """
        self.logger.info(f"檢查職位 '{position.name}' 的超時情況")
        
        # 這裡需要根據實際遊戲界面實現超時檢查和罷黜邏輯
        # 下面是一個框架示例
        
        # 1. 檢查是否在職位列表畫面，如不在則導航
        if not self._navigate_to_position_list_screen():
            self.logger.error("無法導航至職位列表畫面")
            return False
        
        # 2. 檢測職位任職時間
        overtime = self._detect_position_overtime(position)
        if not overtime:
            self.logger.info(f"職位 '{position.name}' 沒有超時")
            return False
        
        # 3. 點擊罷黜按鈕
        if not self._click_dismiss_button(position):
            self.logger.error(f"無法點擊職位 '{position.name}' 的罷黜按鈕")
            return False
        
        # 4. 確認罷黜操作
        if not self._confirm_dismissal():
            self.logger.error(f"無法確認罷黜職位 '{position.name}'")
            return False
        
        position.overtime_count += 1
        
        self.logger.info(f"職位 '{position.name}' 超時處理完成，已罷黜")
        return True
    
    def enable_position(self, position_id):
        """啟用指定職位
        
        Args:
            position_id (str): 職位ID
            
        Returns:
            bool: 是否成功啟用
        """
        for position in self.positions:
            if position.id == position_id:
                position.is_enabled = True
                self.logger.info(f"職位 '{position.name}' 已啟用")
                return True
        
        self.logger.warning(f"找不到ID為 '{position_id}' 的職位")
        return False
    
    def disable_position(self, position_id):
        """禁用指定職位
        
        Args:
            position_id (str): 職位ID
            
        Returns:
            bool: 是否成功禁用
        """
        for position in self.positions:
            if position.id == position_id:
                position.is_enabled = False
                self.logger.info(f"職位 '{position.name}' 已禁用")
                return True
        
        self.logger.warning(f"找不到ID為 '{position_id}' 的職位")
        return False
    
    def toggle_position(self, position_id):
        """切換指定職位的啟用狀態
        
        Args:
            position_id (str): 職位ID
            
        Returns:
            tuple: (bool, str) 是否成功切換及新狀態
        """
        for position in self.positions:
            if position.id == position_id:
                position.is_enabled = not position.is_enabled
                new_state = "啟用" if position.is_enabled else "禁用"
                self.logger.info(f"職位 '{position.name}' 已切換為 {new_state}")
                return (True, new_state)
        
        self.logger.warning(f"找不到ID為 '{position_id}' 的職位")
        return (False, "未知")
    
    def get_all_positions_status(self):
        """獲取所有職位的狀態
        
        Returns:
            list: 職位狀態字典列表
        """
        status_list = []
        
        for position in self.positions:
            status = {
                "id": position.id,
                "name": position.name,
                "enabled": position.is_enabled,
                "applications": position.application_count,
                "overtimes": position.overtime_count,
                "last_processed": position.last_processed_time
            }
            status_list.append(status)
        
        return status_list
    
    # 以下是具體實現方法，需要根據實際遊戲界面來實現
    
    def _navigate_to_application_screen(self):
        """導航到申請畫面
        
        Returns:
            bool: 是否成功導航
        """
        # 實際實現需要根據遊戲界面設計
        # 例如，可能需要點擊特定菜單按鈕，然後點擊申請管理等
        self.logger.debug("導航至申請畫面")
        
        # 示例代碼:
        # 1. 檢查是否已在申請畫面
        menu_template = "images/ui/application_menu_icon.png"
        if self.image_detector.find_template(menu_template):
            self.logger.debug("已在申請畫面")
            return True
        
        # 2. 如不在，則先進入主菜單
        main_menu_template = "images/ui/main_menu_button.png"
        main_menu_match = self.image_detector.find_template(main_menu_template)
        if main_menu_match:
            x, y = main_menu_match[0], main_menu_match[1]
            self.action_executor.click_at(x, y)
            time.sleep(1)  # 等待菜單打開
        
        # 3. 點擊申請管理按鈕
        application_button_template = "images/ui/application_button.png"
        app_button_match = self.image_detector.find_template(application_button_template)
        if app_button_match:
            x, y = app_button_match[0], app_button_match[1]
            self.action_executor.click_at(x, y)
            time.sleep(2)  # 等待頁面加載
            
            # 確認是否成功進入申請畫面
            if self.image_detector.find_template(menu_template):
                self.logger.debug("成功導航至申請畫面")
                return True
        
        self.logger.warning("無法導航至申請畫面")
        return False
    
    def _click_position(self, position):
        """點擊指定職位
        
        Args:
            position (Position): 職位對象
            
        Returns:
            bool: 是否成功點擊
        """
        self.logger.debug(f"嘗試點擊職位 '{position.name}'")
        
        # 根據職位索引計算位置或使用模板匹配
        # 這裡使用模板匹配示例
        template_path = f"images/positions/position{position.index+1}_apply_button.png"
        match = self.image_detector.find_template(
            template_path, 
            region=position.application_region
        )
        
        if match:
            x, y = match[0], match[1]
            self.action_executor.click_at(x, y)
            time.sleep(1)  # 等待響應
            self.logger.debug(f"已點擊職位 '{position.name}'")
            return True
        
        self.logger.debug(f"找不到職位 '{position.name}' 的申請按鈕")
        return False
    
    def _detect_applicants(self):
        """檢測申請者列表
        
        Returns:
            list: 申請者位置列表
        """
        self.logger.debug("檢測申請者列表")
        
        # 實際實現需要根據遊戲界面設計
        # 例如，可能需要檢測特定的申請按鈕或列表元素
        
        # 示例代碼:
        applicant_template = "images/positions/applicant_item.png"
        matches = self.image_detector.find_multiple_templates(
            {"applicant": {"template": applicant_template, "threshold": 0.8}}
        )
        
        applicants = matches.get("applicant", [])
        self.logger.debug(f"檢測到 {len(applicants)} 個申請者")
        return applicants
    
    def _approve_applicants(self, applicants):
        """批准申請者
        
        Args:
            applicants (list): 申請者位置列表
            
        Returns:
            int: 批准的申請者數量
        """
        self.logger.debug(f"處理 {len(applicants)} 個申請者")
        
        # 實際實現需要根據遊戲界面設計
        # 例如，可能需要點擊每個申請者，然後點擊批准按鈕
        
        approved_count = 0
        
        # 示例代碼:
        for i, (x, y) in enumerate(applicants):
            # 點擊申請者
            self.action_executor.click_at(x, y)
            time.sleep(0.5)
            
            # 尋找並點擊批准勾選框
            checkbox_template = "images/positions/approve_checkbox.png"
            checkbox_match = self.image_detector.find_template(checkbox_template)
            
            if checkbox_match:
                checkbox_x, checkbox_y = checkbox_match[0], checkbox_match[1]
                self.action_executor.click_at(checkbox_x, checkbox_y)
                time.sleep(0.5)
                approved_count += 1
            
            # 如果是最後一個申請者，點擊確認按鈕
            if i == len(applicants) - 1:
                confirm_template = "images/positions/confirm_button.png"
                confirm_match = self.image_detector.find_template(confirm_template)
                
                if confirm_match:
                    confirm_x, confirm_y = confirm_match[0], confirm_match[1]
                    self.action_executor.click_at(confirm_x, confirm_y)
                    time.sleep(1)  # 等待確認
        
        self.logger.debug(f"已批准 {approved_count} 個申請者")
        return approved_count
    
    def _navigate_back_to_position_list(self):
        """返回職位列表畫面
        
        Returns:
            bool: 是否成功返回
        """
        self.logger.debug("返回職位列表畫面")
        
        # 示例代碼:
        back_button_template = "images/ui/back_button.png"
        back_match = self.image_detector.find_template(back_button_template)
        
        if back_match:
            x, y = back_match[0], back_match[1]
            self.action_executor.click_at(x, y)
            time.sleep(1)  # 等待返回
            self.logger.debug("成功返回職位列表畫面")
            return True
        
        self.logger.warning("無法返回職位列表畫面")
        return False
    
    def _navigate_to_position_list_screen(self):
        """導航到職位列表畫面
        
        Returns:
            bool: 是否成功導航
        """
        # 與申請畫面類似，但可能是不同的路徑
        # 實際實現需要根據遊戲界面設計
        
        self.logger.debug("導航至職位列表畫面")
        
        # 這裡可能需要實現類似申請畫面的導航邏輯
        # 由於實際界面未知，這裡僅提供框架
        
        return True  # 假設成功
    
    def _detect_position_overtime(self, position):
        """使用OCR檢測職位是否超時
        
        Args:
            position (Position): 職位對象
                
        Returns:
            bool: 是否超時
        """
        try:
            import pytesseract
            from PIL import Image
            import re
            import os
            
            # 設置Tesseract路徑 (Windows需要)
            if os.name == 'nt' and 'ocr' in self.config and 'tesseract_path' in self.config['ocr']:
                pytesseract.pytesseract.tesseract_cmd = self.config['ocr']['tesseract_path']
            
            # 獲取時間顯示區域的截圖
            if not position.time_region:
                self.logger.warning(f"職位 '{position.name}' 未配置時間區域")
                return False
                
            time_region = position.time_region
            time_image = self.image_detector.get_screen_image(region=time_region)
            
            # 轉換為PIL Image格式
            pil_image = Image.fromarray(time_image)
            
            # 是否進行圖像預處理
            if self.config.get('ocr', {}).get('preprocessing', True):
                # 將圖像轉換為灰度
                pil_image = pil_image.convert('L')
                
                # 可以添加更多預處理步驟，如果需要的話
                # 例如：增加對比度、二值化等
            
            # 使用OCR識別文本，設置配置以優化數字和冒號識別
            text = pytesseract.image_to_string(
                pil_image, 
                config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789:'
            )
            
            # 清理文本
            text = text.strip()
            self.logger.debug(f"職位 '{position.name}' OCR識別結果: '{text}'")
            
            # 使用正則表達式解析時間格式 "00:00:00"
            match = re.search(r'(\d+):(\d+):(\d+)', text)
            
            if not match:
                self.logger.warning(f"職位 '{position.name}' 無法解析時間格式: {text}")
                return False
            
            # 提取小時、分鐘和秒
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            
            # 轉換為總分鐘數
            total_minutes = hours * 60 + minutes + seconds / 60
            
            # 與閾值比較
            is_overtime = total_minutes > position.overtime_threshold
            
            if is_overtime:
                self.logger.info(f"職位 '{position.name}' 已超時: {hours}小時{minutes}分鐘{seconds}秒 (閾值: {position.overtime_threshold}分鐘)")
            else:
                self.logger.debug(f"職位 '{position.name}' 未超時: {hours}小時{minutes}分鐘{seconds}秒 (閾值: {position.overtime_threshold}分鐘)")
            
            # 如果啟用了調試圖像保存
            if self.config.get('ocr', {}).get('debug_save_images', False):
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug')
                os.makedirs(debug_dir, exist_ok=True)
                debug_path = os.path.join(debug_dir, f'time_region_pos{position.index}_{int(time.time())}.png')
                cv2.imwrite(debug_path, time_image)
                self.logger.debug(f"已保存時間區域截圖至: {debug_path}")
            
            return is_overtime
        
        except Exception as e:
            self.logger.error(f"檢測職位 '{position.name}' 時間時出錯: {str(e)}")
            return False
    
    def _click_dismiss_button(self, position):
        """點擊罷黜按鈕
        
        Args:
            position (Position): 職位對象
            
        Returns:
            bool: 是否成功點擊
        """
        self.logger.debug(f"嘗試點擊職位 '{position.name}' 的罷黜按鈕")
        
        # 示例代碼:
        dismiss_template = f"images/positions/dismiss_button{position.index+1}.png"
        match = self.image_detector.find_template(dismiss_template)
        
        if match:
            x, y = match[0], match[1]
            self.action_executor.click_at(x, y)
            time.sleep(1)  # 等待響應
            self.logger.debug(f"已點擊職位 '{position.name}' 的罷黜按鈕")
            return True
        
        self.logger.debug(f"找不到職位 '{position.name}' 的罷黜按鈕")
        return False
    
    def _confirm_dismissal(self):
        """確認罷黜操作
        
        Returns:
            bool: 是否成功確認
        """
        self.logger.debug("嘗試確認罷黜操作")
        
        # 示例代碼:
        confirm_template = "images/positions/confirm_dismissal.png"
        match = self.image_detector.find_template(confirm_template)
        
        if match:
            x, y = match[0], match[1]
            self.action_executor.click_at(x, y)
            time.sleep(1)  # 等待確認
            self.logger.debug("已確認罷黜操作")
            return True
        
        self.logger.debug("找不到罷黜確認按鈕")
        return False