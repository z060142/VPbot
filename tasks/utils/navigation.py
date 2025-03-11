#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
導航工具
提供在遊戲中導航到不同畫面的功能
"""

import time
import logging

logger = logging.getLogger("Navigation")

def navigate_to_position_screen(engine):
    """導航到職位申請畫面
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功導航
    """
    logger.debug("導航至職位申請畫面")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 檢查是否已在申請畫面
    if is_at_position_screen(engine):
        logger.debug("已在職位申請畫面")
        return True
    
    # 如果在其他畫面，先回到主畫面
    if not navigate_to_main_screen(engine):
        logger.error("無法導航至主畫面")
        return False
    
    # 從主畫面進入職位申請畫面
    # 嘗試最多3次
    for attempt in range(3):
        # 尋找職位管理入口按鈕
        position_menu_button = image_detector.find_template("ui/position_menu_button.png")
        
        if position_menu_button:
            x, y = position_menu_button[0], position_menu_button[1]
            action_executor.click_at(x, y)
            time.sleep(1.5)  # 等待進入
            
            # 檢查是否已進入申請畫面
            if is_at_position_screen(engine):
                logger.debug("成功導航至職位申請畫面")
                return True
        
        logger.warning(f"導航至職位申請畫面失敗，嘗試 {attempt+1}/3")
        time.sleep(1)
    
    logger.error("無法導航至職位申請畫面")
    return False

def navigate_to_position_list_screen(engine):
    """導航到職位列表畫面
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功導航
    """
    logger.debug("導航至職位列表畫面")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 檢查是否已在職位列表畫面
    if is_at_position_list_screen(engine):
        logger.debug("已在職位列表畫面")
        return True
    
    # 如果在其他畫面，先回到主畫面
    if not navigate_to_main_screen(engine):
        logger.error("無法導航至主畫面")
        return False
    
    # 從主畫面進入職位列表畫面
    # 嘗試最多3次
    for attempt in range(3):
        # 尋找職位列表入口按鈕
        position_list_button = image_detector.find_template("ui/position_list_button.png")
        
        if position_list_button:
            x, y = position_list_button[0], position_list_button[1]
            action_executor.click_at(x, y)
            time.sleep(1.5)  # 等待進入
            
            # 檢查是否已進入職位列表畫面
            if is_at_position_list_screen(engine):
                logger.debug("成功導航至職位列表畫面")
                return True
        
        logger.warning(f"導航至職位列表畫面失敗，嘗試 {attempt+1}/3")
        time.sleep(1)
    
    logger.error("無法導航至職位列表畫面")
    return False

def navigate_to_main_screen(engine, expected_type=None):
    """導航到主畫面
    
    Args:
        engine: 核心引擎實例
        expected_type (int, optional): 期望的主畫面類型(1或2)，如果為None則接受任意類型
    
    Returns:
        bool: 是否成功導航到期望的主畫面
    """
    logger.info(f"導航到主畫面 (期望類型: {expected_type if expected_type else '任意'})")
    
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    # 先檢查是否已經在期望的主畫面
    is_main, screen_type = is_at_main_screen(engine)
    
    if is_main and (expected_type is None or screen_type == expected_type):
        logger.debug(f"已在期望的主畫面 (類型: {screen_type})")
        return True
    
    # 如果在主畫面但不是期望的類型，可以通過特定導航進行切換
    if is_main and expected_type and screen_type != expected_type:
        logger.debug(f"當前在主畫面類型 {screen_type}，需要切換到類型 {expected_type}")
        
        # 根據實際情況實現主畫面類型之間的切換邏輯
        # 例如：點擊特定按鈕進行切換
        
        # 這裡簡單實現一個範例:
        if screen_type == 1 and expected_type == 2:
            # 從類型1切換到類型2的邏輯
            # 例如點擊某個導航按鈕
            button = engine.modules['image_detector'].find_template("ui/to_base_button.png")
            if button:
                x, y = button[0], button[1]
                action_executor.click_at(x, y)
                time.sleep(1.5)
                
                # 檢查是否成功切換
                is_main, new_type = is_at_main_screen(engine)
                return is_main and new_type == expected_type
            
        elif screen_type == 2 and expected_type == 1:
            # 從類型2切換到類型1的邏輯
            button = engine.modules['image_detector'].find_template("ui/to_world_button.png")
            if button:
                x, y = button[0], button[1]
                action_executor.click_at(x, y)
                time.sleep(1.5)
                
                # 檢查是否成功切換
                is_main, new_type = is_at_main_screen(engine)
                return is_main and new_type == expected_type
    
    # 如果不在任何主畫面，嘗試通過通用方法返回主畫面
    # 例如：按ESC返回，尋找並點擊主頁按鈕等
    
    # 嘗試最多5次
    for attempt in range(5):
        logger.debug(f"嘗試返回主畫面，第 {attempt+1}/5 次")
        
        # 1. 嘗試按ESC
        action_executor.key_press('esc')
        time.sleep(1)
        
        # 2. 檢查是否返回主畫面
        is_main, screen_type = is_at_main_screen(engine)
        if is_main and (expected_type is None or screen_type == expected_type):
            logger.info(f"成功返回主畫面 (類型: {screen_type})")
            return True
        
        # 3. 尋找並點擊返回按鈕或主頁按鈕
        home_button = engine.modules['image_detector'].find_template("ui/home_button.png")
        if home_button:
            x, y = home_button[0], home_button[1]
            action_executor.click_at(x, y)
            time.sleep(1.5)
            
            # 檢查是否返回主畫面
            is_main, screen_type = is_at_main_screen(engine)
            if is_main and (expected_type is None or screen_type == expected_type):
                logger.info(f"成功返回主畫面 (類型: {screen_type})")
                return True
        
        # 等待一段時間後再次嘗試
        time.sleep(1)
    
    logger.warning("無法導航到主畫面")
    return False

def is_at_position_screen(engine):
    """檢查是否在職位申請畫面
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否在職位申請畫面
    """
    # 獲取圖像識別器
    image_detector = engine.modules['image_detector']
    
    # 檢查職位申請畫面的特徵元素
    position_screen_indicator = image_detector.find_template("ui/position_screen_indicator.png")
    
    return position_screen_indicator is not None

def is_at_position_list_screen(engine):
    """檢查是否在職位列表畫面
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否在職位列表畫面
    """
    # 獲取圖像識別器
    image_detector = engine.modules['image_detector']
    
    # 檢查職位列表畫面的特徵元素
    position_list_indicator = image_detector.find_template("ui/position_list_indicator.png")
    
    return position_list_indicator is not None

def is_at_main_screen(engine):
    """檢測是否在遊戲主畫面，並處理不同狀況
    
    有三種可能的主畫面狀況:
    1. 第一種主畫面: 同時檢測到 'avatar1.png' 和 'world_buttom1.png'
    2. 第二種主畫面: 同時檢測到 'avatar1.png' 和 'base_buttom1.png'
    3. 需處理的狀況: 同時檢測到 'avatar2.png' 和 'base_buttom2.png'，需點擊按鈕進入主畫面
    
    Args:
        engine: 核心引擎實例
    
    Returns:
        tuple: (是否在主畫面, 主畫面類型[1 或 2 或 None])
    """
    logger.debug("檢測是否在遊戲主畫面")
    
    # 獲取圖像識別器和動作執行器
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 定義檢測區域 (這需要根據實際情況調整)
    avatar_region = (312, 212, 404, 294)  # 角色頭像區域
    button_region = (2073, 1177, 2212, 1267) # 按鈕區域
    
    # 檢測頭像
    avatar1 = image_detector.find_template("ui/avatar1.png", region=avatar_region)
    avatar2 = image_detector.find_template("ui/avatar2.png", region=avatar_region)
    
    # 檢測按鈕
    world_button1 = image_detector.find_template("ui/world_buttom1.png", region=button_region)
    base_button1 = image_detector.find_template("ui/base_buttom1.png", region=button_region)
    base_button2 = image_detector.find_template("ui/base_buttom2.png", region=button_region)
    
    # 情況1: 第一種主畫面
    if avatar1 and world_button1:
        logger.debug("檢測到第一種主畫面 (avatar1 + world_buttom1)")
        return (True, 1)
    
    # 情況2: 第二種主畫面
    if avatar1 and base_button1:
        logger.debug("檢測到第二種主畫面 (avatar1 + base_buttom1)")
        return (True, 2)
    
    # 情況3: 需要處理的狀況
    if avatar2 and base_button2:
        logger.debug("檢測到需要處理的狀況 (avatar2 + base_buttom2)，進行點擊")
        
        # 點擊按鈕位置
        if base_button2:
            x, y = base_button2[0], base_button2[1]
            action_executor.click_at(x, y)
            
            # 等待進入主畫面
            time.sleep(2)
            
            # 再次檢測是否進入了第二種主畫面
            if image_detector.find_template("ui/base_buttom1.png", region=button_region):
                logger.debug("已成功進入第二種主畫面")
                return (True, 2)
    
    # 不在任何主畫面
    logger.debug("未檢測到主畫面")
    return (False, None)

def handle_popup_dialogs(engine):
    """處理可能出現的彈出對話框
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功處理
    """
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 檢查各種可能的彈窗
    # 1. 通用確認彈窗
    confirm_button = image_detector.find_template("ui/confirm_button.png")
    if confirm_button:
        x, y = confirm_button[0], confirm_button[1]
        action_executor.click_at(x, y)
        time.sleep(0.5)
        return True
    
    # 2. 通用取消按鈕
    cancel_button = image_detector.find_template("ui/cancel_button.png")
    if cancel_button:
        x, y = cancel_button[0], cancel_button[1]
        action_executor.click_at(x, y)
        time.sleep(0.5)
        return True
    
    # 3. 關閉按鈕 (X)
    close_button = image_detector.find_template("ui/close_button.png")
    if close_button:
        x, y = close_button[0], close_button[1]
        action_executor.click_at(x, y)
        time.sleep(0.5)
        return True
    
    # 沒有檢測到彈窗
    return False