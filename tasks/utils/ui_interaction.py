#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI交互工具
提供與遊戲UI元素交互的通用功能
"""

import time
import logging
import random

logger = logging.getLogger("UIInteraction")

def scroll_to_top(engine):
    """捲動列表到最頂端
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功執行
    """
    logger.debug("捲動列表到最頂端")
    
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    # 連續按HOME鍵或向上鍵多次，確保到達頂部
    # 先嘗試HOME鍵
    action_executor.key_press('home')
    time.sleep(0.5)
    
    # 再按幾次向上鍵確保到頂
    for _ in range(3):
        action_executor.key_press('up')
        time.sleep(0.2)
    
    return True

def scroll_to_bottom(engine):
    """捲動列表到最底部
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功執行
    """
    logger.debug("捲動列表到最底部")
    
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    # 連續按END鍵或向下鍵多次，確保到達底部
    # 先嘗試END鍵
    action_executor.key_press('end')
    time.sleep(0.5)
    
    # 再按幾次向下鍵確保到底
    for _ in range(3):
        action_executor.key_press('down')
        time.sleep(0.2)
    
    return True

def scroll_down_one_page(engine):
    """向下捲動一頁
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功執行
    """
    logger.debug("向下捲動一頁")
    
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    # 按PAGE DOWN鍵
    action_executor.key_press('pagedown')
    time.sleep(0.5)
    
    return True

def scroll_up_one_page(engine):
    """向上捲動一頁
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功執行
    """
    logger.debug("向上捲動一頁")
    
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    # 按PAGE UP鍵
    action_executor.key_press('pageup')
    time.sleep(0.5)
    
    return True

def click_on_template(engine, template_path, threshold=None, region=None, offset=(0, 0)):
    """尋找並點擊匹配的模板
    
    Args:
        engine (CoreEngine): 核心引擎實例
        template_path (str): 模板路徑
        threshold (float, optional): 匹配閾值
        region (tuple, optional): 搜索區域 (x, y, width, height)
        offset (tuple, optional): 點擊位置偏移量 (x, y)
    
    Returns:
        bool: 是否成功點擊
    """
    logger.debug(f"尋找並點擊模板 {template_path}")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 尋找模板
    match = image_detector.find_template(template_path, threshold, region)
    
    if match:
        # 計算實際點擊位置 (添加偏移量)
        x = match[0] + offset[0]
        y = match[1] + offset[1]
        
        # 點擊
        action_executor.click_at(x, y)
        time.sleep(0.3)  # 等待反應
        
        logger.debug(f"成功點擊模板 {template_path} 於位置 ({x}, {y})")
        return True
    
    logger.warning(f"找不到模板 {template_path} 以進行點擊")
    return False

def wait_and_click_on_template(engine, template_path, timeout=10, threshold=None, region=None, offset=(0, 0)):
    """等待並點擊匹配的模板
    
    Args:
        engine (CoreEngine): 核心引擎實例
        template_path (str): 模板路徑
        timeout (int, optional): 等待超時秒數
        threshold (float, optional): 匹配閾值
        region (tuple, optional): 搜索區域 (x, y, width, height)
        offset (tuple, optional): 點擊位置偏移量 (x, y)
    
    Returns:
        bool: 是否成功點擊
    """
    logger.debug(f"等待並點擊模板 {template_path}")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    # 等待模板出現
    match = image_detector.wait_for_template(template_path, timeout, threshold, region)
    
    if match:
        # 計算實際點擊位置 (添加偏移量)
        x = match[0] + offset[0]
        y = match[1] + offset[1]
        
        # 點擊
        action_executor.click_at(x, y)
        time.sleep(0.3)  # 等待反應
        
        logger.debug(f"成功點擊模板 {template_path} 於位置 ({x}, {y})")
        return True
    
    logger.warning(f"等待模板 {template_path} 超時")
    return False

def humanize_click(engine, x, y, deviation=5):
    """模擬人類點擊（添加小偏移）
    
    Args:
        engine (CoreEngine): 核心引擎實例
        x (int): 目標X座標
        y (int): 目標Y座標
        deviation (int, optional): 最大偏移像素
    
    Returns:
        tuple: 實際點擊位置 (x, y)
    """
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    # 添加隨機偏移
    offset_x = random.randint(-deviation, deviation)
    offset_y = random.randint(-deviation, deviation)
    
    actual_x = x + offset_x
    actual_y = y + offset_y
    
    # 執行點擊
    action_executor.click_at(actual_x, actual_y)
    
    # 添加隨機延遲
    delay = 0.2 + random.uniform(0, 0.3)
    time.sleep(delay)
    
    return (actual_x, actual_y)

def type_text_with_natural_delay(engine, text):
    """模擬人類輸入文字（帶有自然延遲）
    
    Args:
        engine (CoreEngine): 核心引擎實例
        text (str): 要輸入的文字
    
    Returns:
        bool: 是否成功輸入
    """
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    for char in text:
        # 輸入字符
        action_executor.type_string(char)
        
        # 添加隨機延遲
        delay = 0.05 + random.uniform(0, 0.15)
        time.sleep(delay)
    
    return True

def clear_text_field(engine):
    """清除文字框內容
    
    Args:
        engine (CoreEngine): 核心引擎實例
    
    Returns:
        bool: 是否成功清除
    """
    # 獲取動作執行器
    action_executor = engine.modules['action_executor']
    
    # 全選文字 (Ctrl+A)
    action_executor.key_press('ctrl')
    action_executor.key_press('a')
    action_executor.key_release('a')
    action_executor.key_release('ctrl')
    time.sleep(0.2)
    
    # 刪除所選文字
    action_executor.key_press('delete')
    time.sleep(0.2)
    
    return True

def handle_confirmation_dialog(engine, confirm=True):
    """處理確認對話框
    
    Args:
        engine (CoreEngine): 核心引擎實例
        confirm (bool, optional): 是否確認，True為確認，False為取消
    
    Returns:
        bool: 是否成功處理
    """
    logger.debug(f"處理確認對話框，選擇: {'確認' if confirm else '取消'}")
    
    # 獲取模組
    image_detector = engine.modules['image_detector']
    action_executor = engine.modules['action_executor']
    
    if confirm:
        # 尋找確認按鈕
        confirm_button = image_detector.find_template("ui/confirm_button.png")
        if confirm_button:
            x, y = confirm_button[0], confirm_button[1]
            action_executor.click_at(x, y)
            time.sleep(0.5)
            return True
        
        # 尋找"是"按鈕
        yes_button = image_detector.find_template("ui/yes_button.png")
        if yes_button:
            x, y = yes_button[0], yes_button[1]
            action_executor.click_at(x, y)
            time.sleep(0.5)
            return True
    else:
        # 尋找取消按鈕
        cancel_button = image_detector.find_template("ui/cancel_button.png")
        if cancel_button:
            x, y = cancel_button[0], cancel_button[1]
            action_executor.click_at(x, y)
            time.sleep(0.5)
            return True
        
        # 尋找"否"按鈕
        no_button = image_detector.find_template("ui/no_button.png")
        if no_button:
            x, y = no_button[0], no_button[1]
            action_executor.click_at(x, y)
            time.sleep(0.5)
            return True
    
    logger.warning("找不到確認/取消按鈕")
    return False