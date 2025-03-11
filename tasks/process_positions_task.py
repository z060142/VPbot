#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
職位申請處理任務
負責檢測並處理遊戲中的職位申請
"""

import time
import logging
from tasks.utils.navigation import is_at_main_screen, navigate_to_main_screen, navigate_to_position_screen
from tasks.utils.ui_interaction import scroll_to_top

logger = logging.getLogger("ProcessPositions")

def process_positions_task(engine):
    """處理職位申請的主任務
    
    Args:
        engine: 核心引擎實例
    
    Returns:
        bool: 是否成功完成任務
    """
    logger.info("開始執行職位申請處理任務")
    
    try:
        # 檢查遊戲是否在主畫面
        is_main, screen_type = is_at_main_screen(engine)
        
        # 如果不在主畫面，嘗試導航到主畫面
        if not is_main:
            logger.info("當前不在主畫面，嘗試導航到主畫面")
            if not navigate_to_main_screen(engine):
                logger.error("無法導航到主畫面，任務中止")
                return False
            
            # 再次檢查主畫面類型
            is_main, screen_type = is_at_main_screen(engine)
            
        logger.info(f"當前在主畫面類型: {screen_type}")
        
        # 導航到職位申請畫面
        if not navigate_to_position_screen(engine):
            logger.error("無法導航到職位申請畫面，任務中止")
            return False
        
        logger.info("已進入職位申請畫面")
        
        # 處理職位申請
        position_manager = engine.modules['position_manager']
        result = position_manager.process_all_positions()
        
        # 返回主畫面
        navigate_to_main_screen(engine)
        
        logger.info("職位申請處理任務完成" + (" (有處理申請)" if result else " (無申請需處理)"))
        return True
    
    except Exception as e:
        logger.error(f"處理職位申請時出錯: {str(e)}")
        # 嘗試返回主畫面
        try:
            navigate_to_main_screen(engine)
        except:
            pass
        return False

def check_overtime_task(engine):
    """檢查職位超時的任務
    
    Args:
        engine: 核心引擎實例
    
    Returns:
        bool: 是否成功完成任務
    """
    logger.info("開始執行職位超時檢查任務")
    
    try:
        # 檢查遊戲是否在主畫面
        is_main, screen_type = is_at_main_screen(engine)
        
        # 如果不在主畫面，嘗試導航到主畫面
        if not is_main:
            logger.info("當前不在主畫面，嘗試導航到主畫面")
            if not navigate_to_main_screen(engine):
                logger.error("無法導航到主畫面，任務中止")
                return False
        
        # 導航到職位列表畫面 (可能與職位申請畫面相同或不同，根據實際情況調整)
        if not navigate_to_position_screen(engine):
            logger.error("無法導航到職位列表畫面，任務中止")
            return False
        
        logger.info("已進入職位列表畫面")
        
        # 檢查職位超時
        position_manager = engine.modules['position_manager']
        result = position_manager.check_all_overtime()
        
        # 返回主畫面
        navigate_to_main_screen(engine)
        
        logger.info("職位超時檢查任務完成" + (" (有超時處理)" if result else " (無超時需處理)"))
        return True
    
    except Exception as e:
        logger.error(f"檢查職位超時時出錯: {str(e)}")
        # 嘗試返回主畫面
        try:
            navigate_to_main_screen(engine)
        except:
            pass
        return False

# 添加其他相關任務函數...