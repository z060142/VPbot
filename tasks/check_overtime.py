#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
超時職位檢查任務
負責檢測並罷黜任職超過閾值的職位
"""

import time
import logging
from tasks.utils.navigation import navigate_to_position_list_screen
from tasks.utils.ui_interaction import scroll_to_top

logger = logging.getLogger("CheckOvertime")

def check_overtime_task(engine):
    """檢查所有職位超時的任務
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功處理
    """
    logger.info("執行職位超時檢查任務")
    
    try:
        # 獲取模組
        position_manager = engine.modules['position_manager']
        
        # 考慮到30秒執行一次，可能不需要每次都導航到職位列表畫面
        # 我們可以使用一個計數器，只在必要時才進行完整導航
        
        # 靜態變量用於計數
        if not hasattr(check_overtime_task, "execution_count"):
            check_overtime_task.execution_count = 0
        
        # 每10次（約5分鐘）進行一次完整導航，其他時間直接檢測
        full_navigation = check_overtime_task.execution_count % 10 == 0
        check_overtime_task.execution_count += 1
        
        if full_navigation:
            # 導航至職位列表畫面
            if not navigate_to_position_list_screen(engine):
                logger.error("無法導航至職位列表畫面")
                return False
                
            # 捲動到列表最上方(如果需要)
            scroll_to_top(engine)
        
        # 檢查所有職位的超時情況
        result = position_manager.check_all_overtime()
        
        # 如果進行了完整導航，則返回主畫面
        if full_navigation:
            navigate_back_to_main_screen(engine)
        
        logger.info("職位超時檢查任務完成")
        return result
    
    except Exception as e:
        logger.error(f"檢查職位超時時出錯: {str(e)}")
        try:
            # 嘗試返回主畫面
            if full_navigation:
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

def check_position_overtime(engine, position):
    """檢查單個職位的超時情況
    
    Args:
        engine (CoreEngine): 核心引擎實例
        position (Position): 職位物件
    
    Returns:
        bool: 是否發現並處理超時
    """
    logger.info(f"檢查職位 '{position.name}' 的超時情況")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 檢查職位時間
    # 這裡需要實際根據遊戲界面設計識別時間的方法
    # 可能是通過模板匹配超時指示器或通過OCR讀取時間文本
    
    # 示例：尋找超時指示器
    overtime_indicator = image_detector.find_template(
        f"positions/overtime_indicator{position.index+1}.png",
        region=get_time_region_for_position(position)
    )
    
    if not overtime_indicator:
        logger.debug(f"職位 '{position.name}' 未檢測到超時")
        return False
    
    logger.info(f"檢測到職位 '{position.name}' 超時")
    
    # 點擊罷黜按鈕
    dismiss_button = image_detector.find_template(
        f"positions/dismiss_button{position.index+1}.png"
    )
    
    if not dismiss_button:
        logger.warning(f"找不到職位 '{position.name}' 的罷黜按鈕")
        return False
    
    # 點擊罷黜按鈕
    x, y = dismiss_button[0], dismiss_button[1]
    action_executor.click_at(x, y)
    time.sleep(1)
    
    # 確認罷黜操作
    if not confirm_dismissal(engine):
        logger.warning(f"無法確認罷黜職位 '{position.name}'")
        return False
    
    logger.info(f"已成功罷黜超時的職位 '{position.name}'")
    return True

def get_time_region_for_position(position):
    """根據職位獲取時間顯示區域
    
    Args:
        position (Position): 職位物件
    
    Returns:
        tuple: 區域坐標 (x, y, width, height)
    """
    # 這需要根據實際遊戲界面設計
    # 示例：假設時間顯示在職位右側
    base_x = 500
    base_y = 150 + position.index * 50
    return (base_x, base_y, 100, 30)

def confirm_dismissal(engine):
    """確認罷黜操作
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功確認
    """
    logger.debug("確認罷黜操作")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 尋找確認按鈕
    confirm_button = image_detector.wait_for_template(
        "positions/confirm_dismissal.png",
        timeout=3
    )
    
    if not confirm_button:
        logger.warning("找不到罷黜確認按鈕")
        return False
    
    # 點擊確認按鈕
    x, y = confirm_button[0], confirm_button[1]
    action_executor.click_at(x, y)
    time.sleep(1)
    
    # 檢查是否有成功提示
    success_indicator = image_detector.wait_for_template(
        "positions/dismissal_success.png", 
        timeout=5
    )
    
    if success_indicator:
        logger.debug("罷黜操作成功")
        return True
    else:
        logger.warning("無法確認罷黜操作是否成功")
        return False