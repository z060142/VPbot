#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
職位申請處理任務
負責檢測並處理6個職位的申請者
"""

import time
import logging
from tasks.utils.navigation import navigate_to_position_screen
from tasks.utils.ui_interaction import scroll_to_top

logger = logging.getLogger("ProcessApplications")

def process_applications_task(engine):
    """處理所有職位申請的任務
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功處理
    """
    logger.info("開始執行職位申請處理任務")
    
    try:
        # 獲取模組
        position_manager = engine.modules['position_manager']
        image_detector = engine.modules['image_detector']
        action_executor = engine.modules['action_executor']
        
        # 導航至職位申請畫面
        if not navigate_to_position_screen(engine):
            logger.error("無法導航至職位申請畫面")
            return False
        
        # 捲動到列表最上方(如果需要)
        scroll_to_top(engine)
        
        # 處理所有職位的申請
        result = position_manager.process_all_positions()
        
        # 任務完成，返回主畫面
        navigate_back_to_main_screen(engine)
        
        logger.info("職位申請處理任務完成")
        return result
    
    except Exception as e:
        logger.error(f"處理職位申請時出錯: {str(e)}")
        try:
            # 嘗試返回主畫面
            navigate_back_to_main_screen(engine)
        except:
            pass
        return False

def navigate_back_to_main_screen(engine):
    """返回主畫面
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功返回
    """
    logger.debug("嘗試返回主畫面")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 尋找返回按鈕或主頁按鈕
    back_button = image_detector.find_template("ui/back_button.png")
    
    if back_button:
        logger.debug("找到返回按鈕")
        x, y = back_button[0], back_button[1]
        action_executor.click_at(x, y)
        time.sleep(1)
        return True
    
    # 如果沒有找到返回按鈕，嘗試找主頁按鈕
    home_button = image_detector.find_template("ui/home_button.png")
    
    if home_button:
        logger.debug("找到主頁按鈕")
        x, y = home_button[0], home_button[1]
        action_executor.click_at(x, y)
        time.sleep(1)
        return True
    
    # 嘗試按ESC鍵退出
    logger.debug("找不到返回按鈕，嘗試按ESC鍵")
    action_executor.key_press('esc')
    time.sleep(1)
    
    # 再次檢查是否回到主畫面
    main_screen = image_detector.find_template("ui/main_screen_indicator.png")
    if main_screen:
        logger.debug("已成功返回主畫面")
        return True
    
    logger.warning("無法確認是否已返回主畫面")
    return False

def process_position_applications(engine, position):
    """處理單個職位的申請
    
    參數:
        engine (CoreEngine): 核心引擎實例
        position (Position): 職位物件
    
    返回:
        bool: 是否成功處理申請
    """
    logger.info(f"處理職位 '{position.name}' 的申請")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 檢查有無申請按鈕
    apply_button = image_detector.find_template(
        f"positions/position{position.index+1}_apply_button.png", 
        region=position.application_region
    )
    
    if not apply_button:
        logger.debug(f"職位 '{position.name}' 沒有申請或找不到申請按鈕")
        return False
    
    # 點擊申請按鈕
    x, y = apply_button[0], apply_button[1]
    action_executor.click_at(x, y)
    time.sleep(1)
    
    # 檢查是否成功進入申請處理界面
    if not image_detector.find_template("positions/applicant_screen_indicator.png"):
        logger.warning(f"無法進入職位 '{position.name}' 的申請處理界面")
        return False
    
    # 處理所有申請者
    processed = process_all_applicants(engine)
    
    # 返回職位列表
    back_button = image_detector.find_template("ui/back_button.png")
    if back_button:
        x, y = back_button[0], back_button[1]
        action_executor.click_at(x, y)
        time.sleep(1)
    
    return processed > 0

def process_all_applicants(engine):
    """處理所有申請者
    
    參數:
        engine (CoreEngine): 核心引擎實例
    
    返回:
        int: 處理的申請者數量
    """
    logger.debug("處理申請者")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 尋找申請者列表
    applicants = []
    max_attempts = 3
    current_attempt = 0
    
    while current_attempt < max_attempts:
        # 尋找申請者列表中的核取方框
        checkboxes = image_detector.find_multiple_templates(
            {"checkbox": {"template": "positions/applicant_checkbox.png", "threshold": 0.8, "max_results": 20}}
        )
        
        if checkboxes.get("checkbox"):
            applicants = checkboxes["checkbox"]
            break
        
        # 沒找到，可能需要滾動列表
        if current_attempt < max_attempts - 1:  # 最後一次不滾動
            action_executor.key_press('down')  # 按下方向鍵向下滾動
            time.sleep(0.5)
        
        current_attempt += 1
    
    # 未找到申請者
    if not applicants:
        logger.debug("找不到任何申請者")
        return 0
    
    logger.debug(f"找到 {len(applicants)} 個申請者")
    processed_count = 0
    
    # 處理每個申請者
    for i, (x, y) in enumerate(applicants):
        # 點擊核取方框
        action_executor.click_at(x, y)
        time.sleep(0.3)
        processed_count += 1
    
    # 找確認按鈕
    confirm_button = image_detector.find_template("positions/confirm_button.png")
    if confirm_button:
        x, y = confirm_button[0], confirm_button[1]
        action_executor.click_at(x, y)
        time.sleep(1)
        
        # 檢查是否有成功提示
        success_indicator = image_detector.wait_for_template(
            "positions/approval_success.png", 
            timeout=5
        )
        
        if success_indicator:
            logger.debug("申請處理成功")
        else:
            logger.warning("無法確認申請處理是否成功")
    else:
        logger.warning("找不到確認按鈕")
        processed_count = 0  # 如果找不到確認按鈕，視為沒有處理任何申請
    
    return processed_count