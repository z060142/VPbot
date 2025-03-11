#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
例外情況處理工具
提供處理遊戲中可能出現的各種意外情況的功能
"""

import time
import logging
from tasks.utils.navigation import is_at_main_screen

logger = logging.getLogger("ExceptionHandlers")

def handle_common_popups(engine):
    """處理常見的彈窗
    
    Args:
        engine: 核心引擎實例
    
    Returns:
        bool: 是否處理了彈窗
    """
    # 獲取圖像識別器和動作執行器
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 定義可能的彈窗及其處理方式
    popups = [
        {
            "name": "通知彈窗",
            "template": "ui/popup_notice.png",
            "button": "ui/close_button.png",
            "region": None  # 全屏檢測
        },
        {
            "name": "確認彈窗",
            "template": "ui/confirm_dialog.png",
            "button": "ui/ok_button.png",
            "region": None
        },
        {
            "name": "取消彈窗",
            "template": "ui/cancel_dialog.png",
            "button": "ui/cancel_button.png",
            "region": None
        },
        # 添加更多彈窗類型...
    ]
    
    for popup in popups:
        # 檢測彈窗
        dialog = image_detector.find_template(popup["template"], region=popup["region"])
        if dialog:
            logger.info(f"檢測到 {popup['name']} 彈窗，嘗試關閉")
            
            # 查找關閉按鈕
            button = image_detector.find_template(popup["button"])
            if button:
                x, y = button[0], button[1]
                action_executor.click_at(x, y)
                logger.debug(f"點擊了 {popup['name']} 的關閉按鈕")
                time.sleep(0.5)  # 等待彈窗消失
                return True
    
    # 檢查通用關閉按鈕 (右上角 X)
    close_button = image_detector.find_template("ui/generic_close_button.png")
    if close_button:
        x, y = close_button[0], close_button[1]
        action_executor.click_at(x, y)
        logger.debug("點擊了通用關閉按鈕")
        time.sleep(0.5)
        return True
    
    # 沒有檢測到彈窗
    return False

def recover_to_main_screen(engine, max_attempts=5):
    """嘗試恢復到主畫面
    
    Args:
        engine: 核心引擎實例
        max_attempts (int, optional): 最大嘗試次數
    
    Returns:
        bool: 是否成功恢復到主畫面
    """
    logger.info("嘗試恢復到主畫面")
    
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    for attempt in range(max_attempts):
        logger.debug(f"恢復嘗試 {attempt+1}/{max_attempts}")
        
        # 檢查是否已在主畫面
        is_main, _ = is_at_main_screen(engine)
        if is_main:
            logger.info("已在主畫面，恢復成功")
            return True
        
        # 處理彈窗
        if handle_common_popups(engine):
            logger.debug("處理了彈窗，繼續檢查")
            continue
        
        # 按ESC嘗試返回
        action_executor.key_press('esc')
        time.sleep(1)
        
        # 再次檢查是否返回主畫面
        is_main, _ = is_at_main_screen(engine)
        if is_main:
            logger.info("按ESC返回主畫面成功")
            return True
        
        # 尋找主頁按鈕
        home_button = engine.modules['image_detector'].find_template("ui/home_button.png")
        if home_button:
            x, y = home_button[0], home_button[1]
            action_executor.click_at(x, y)
            logger.debug("點擊了主頁按鈕")
            time.sleep(1.5)
            
            # 檢查是否返回主畫面
            is_main, _ = is_at_main_screen(engine)
            if is_main:
                logger.info("點擊主頁按鈕返回主畫面成功")
                return True
    
    logger.warning(f"經過 {max_attempts} 次嘗試，無法恢復到主畫面")
    return False

def handle_disconnection(engine):
    """處理斷線情況
    
    Args:
        engine: 核心引擎實例
    
    Returns:
        bool: 是否成功處理斷線
    """
    # 獲取圖像識別器和動作執行器
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 檢查斷線提示
    disconnect_notice = image_detector.find_template("ui/disconnect_notice.png")
    if not disconnect_notice:
        return False
    
    logger.warning("檢測到斷線提示")
    
    # 尋找重連按鈕
    reconnect_button = image_detector.find_template("ui/reconnect_button.png")
    if reconnect_button:
        x, y = reconnect_button[0], reconnect_button[1]
        action_executor.click_at(x, y)
        logger.info("點擊重連按鈕")
        
        # 等待重連
        time.sleep(10)
        
        # 檢查是否重連成功 (返回主畫面)
        is_main, _ = is_at_main_screen(engine)
        if is_main:
            logger.info("重連成功")
            return True
    
    # 如果重連失敗或找不到重連按鈕，可能需要重啟遊戲
    logger.error("重連失敗，需要重啟遊戲")
    return False

# 添加更多處理函數...