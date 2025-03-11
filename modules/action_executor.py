#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
動作執行器模組
負責執行鍵盤滑鼠操作
"""

import time
import random
import logging
import threading
from enum import Enum

# 嘗試導入適用於遊戲的直接輸入庫，如果不可用則使用pyautogui
try:
    import pydirectinput as directinput
    DIRECT_INPUT_AVAILABLE = True
except ImportError:
    DIRECT_INPUT_AVAILABLE = False
    
import pyautogui

class InputMode(Enum):
    """輸入模式枚舉"""
    AUTO = 0         # 自動選擇最合適的模式
    DIRECT = 1       # 使用DirectInput (遊戲優先)
    GUI = 2          # 使用PyAutoGUI (一般應用)

class ActionExecutor:
    """動作執行器類，提供鍵盤滑鼠操作功能"""
    
    def __init__(self, config):
        """初始化動作執行器
        
        Args:
            config (dict): 系統配置
        """
        self.config = config
        self.logger = logging.getLogger("ActionExecutor")
        
        # 初始化狀態
        self.last_action_time = 0
        self.current_action = None
        self.is_running = True
        self.action_lock = threading.Lock()
        
        # 安全設置
        pyautogui.FAILSAFE = True  # 啟用故障安全（移動到屏幕邊緣可中斷）
        
        # 根據配置設置默認輸入模式
        self.default_input_mode = InputMode.AUTO
        if 'action' in config and 'default_input_mode' in config['action']:
            mode_str = config['action']['default_input_mode'].upper()
            if mode_str == 'DIRECT':
                self.default_input_mode = InputMode.DIRECT
            elif mode_str == 'GUI':
                self.default_input_mode = InputMode.GUI
        
        # 操作間最小延遲（秒）
        self.min_action_delay = config.get('action', {}).get('min_action_delay', 0.1)
        
        self.logger.info("動作執行器初始化完成")
        if not DIRECT_INPUT_AVAILABLE and self.default_input_mode == InputMode.DIRECT:
            self.logger.warning("PyDirectInput不可用，將使用PyAutoGUI代替")
    
    def click_at(self, x, y, button='left', mode=None):
        """在指定位置點擊
        
        Args:
            x (int): X坐標
            y (int): Y坐標
            button (str, optional): 按鍵 ('left', 'right', 'middle')
            mode (InputMode, optional): 輸入模式
        """
        with self.action_lock:
            self._wait_for_min_delay()
            
            self.current_action = f"click_{button}_at_{x}_{y}"
            self.logger.debug(f"點擊 {button} 於 ({x}, {y})")
            
            input_mode = self._determine_input_mode(mode)
            
            try:
                if input_mode == InputMode.DIRECT and DIRECT_INPUT_AVAILABLE:
                    # 移動到位置
                    directinput.moveTo(x, y)
                    # 點擊
                    if button == 'left':
                        directinput.click(x, y)
                    elif button == 'right':
                        directinput.rightClick(x, y)
                    elif button == 'middle':
                        directinput.middleClick(x, y)
                else:
                    # 移動到位置
                    pyautogui.moveTo(x, y)
                    # 點擊
                    pyautogui.click(x=x, y=y, button=button)
                
                self.last_action_time = time.time()
                self.current_action = None
                
            except Exception as e:
                self.logger.error(f"點擊操作失敗: {str(e)}")
                self.current_action = None
                raise
    
    def double_click_at(self, x, y, button='left', mode=None):
        """在指定位置雙擊
        
        Args:
            x (int): X坐標
            y (int): Y坐標
            button (str, optional): 按鍵 ('left', 'right', 'middle')
            mode (InputMode, optional): 輸入模式
        """
        with self.action_lock:
            self._wait_for_min_delay()
            
            self.current_action = f"double_click_{button}_at_{x}_{y}"
            self.logger.debug(f"雙擊 {button} 於 ({x}, {y})")
            
            input_mode = self._determine_input_mode(mode)
            
            try:
                if input_mode == InputMode.DIRECT and DIRECT_INPUT_AVAILABLE:
                    # DirectInput沒有內置雙擊，所以我們執行兩次點擊
                    directinput.moveTo(x, y)
                    if button == 'left':
                        directinput.click(x, y)
                        time.sleep(0.1)
                        directinput.click(x, y)
                    elif button == 'right':
                        directinput.rightClick(x, y)
                        time.sleep(0.1)
                        directinput.rightClick(x, y)
                    elif button == 'middle':
                        directinput.middleClick(x, y)
                        time.sleep(0.1)
                        directinput.middleClick(x, y)
                else:
                    pyautogui.moveTo(x, y)
                    pyautogui.doubleClick(x=x, y=y, button=button)
                
                self.last_action_time = time.time()
                self.current_action = None
                
            except Exception as e:
                self.logger.error(f"雙擊操作失敗: {str(e)}")
                self.current_action = None
                raise
    
    def right_click_at(self, x, y, mode=None):
        """在指定位置右鍵點擊
        
        Args:
            x (int): X坐標
            y (int): Y坐標
            mode (InputMode, optional): 輸入模式
        """
        self.click_at(x, y, button='right', mode=mode)
    
    def move_to(self, x, y, mode=None):
        """移動到指定位置
        
        Args:
            x (int): X坐標
            y (int): Y坐標
            mode (InputMode, optional): 輸入模式
        """
        with self.action_lock:
            self._wait_for_min_delay()
            
            self.current_action = f"move_to_{x}_{y}"
            self.logger.debug(f"移動到 ({x}, {y})")
            
            input_mode = self._determine_input_mode(mode)
            
            try:
                if input_mode == InputMode.DIRECT and DIRECT_INPUT_AVAILABLE:
                    directinput.moveTo(x, y)
                else:
                    pyautogui.moveTo(x, y)
                
                self.last_action_time = time.time()
                self.current_action = None
                
            except Exception as e:
                self.logger.error(f"移動操作失敗: {str(e)}")
                self.current_action = None
                raise
    
    def key_press(self, key, mode=None):
        """按下按鍵
        
        Args:
            key (str): 按鍵名稱
            mode (InputMode, optional): 輸入模式
        """
        with self.action_lock:
            self._wait_for_min_delay()
            
            self.current_action = f"key_press_{key}"
            self.logger.debug(f"按下按鍵 {key}")
            
            input_mode = self._determine_input_mode(mode)
            
            try:
                if input_mode == InputMode.DIRECT and DIRECT_INPUT_AVAILABLE:
                    directinput.press(key)
                else:
                    pyautogui.press(key)
                
                self.last_action_time = time.time()
                self.current_action = None
                
            except Exception as e:
                self.logger.error(f"按鍵操作失敗: {str(e)}")
                self.current_action = None
                raise
    
    def key_down(self, key, mode=None):
        """按住按鍵
        
        Args:
            key (str): 按鍵名稱
            mode (InputMode, optional): 輸入模式
        """
        with self.action_lock:
            self._wait_for_min_delay()
            
            self.current_action = f"key_down_{key}"
            self.logger.debug(f"按住按鍵 {key}")
            
            input_mode = self._determine_input_mode(mode)
            
            try:
                if input_mode == InputMode.DIRECT and DIRECT_INPUT_AVAILABLE:
                    directinput.keyDown(key)
                else:
                    pyautogui.keyDown(key)
                
                self.last_action_time = time.time()
                self.current_action = None
                
            except Exception as e:
                self.logger.error(f"按住按鍵操作失敗: {str(e)}")
                self.current_action = None
                raise
    
    def key_up(self, key, mode=None):
        """釋放按鍵
        
        Args:
            key (str): 按鍵名稱
            mode (InputMode, optional): 輸入模式
        """
        with self.action_lock:
            self._wait_for_min_delay()
            
            self.current_action = f"key_up_{key}"
            self.logger.debug(f"釋放按鍵 {key}")
            
            input_mode = self._determine_input_mode(mode)
            
            try:
                if input_mode == InputMode.DIRECT and DIRECT_INPUT_AVAILABLE:
                    directinput.keyUp(key)
                else:
                    pyautogui.keyUp(key)
                
                self.last_action_time = time.time()
                self.current_action = None
                
            except Exception as e:
                self.logger.error(f"釋放按鍵操作失敗: {str(e)}")
                self.current_action = None
                raise
    
    def type_string(self, text, interval=0.05, mode=None):
        """輸入文字
        
        Args:
            text (str): 要輸入的文字
            interval (float, optional): 按鍵間隔(秒)
            mode (InputMode, optional): 輸入模式
        """
        with self.action_lock:
            self._wait_for_min_delay()
            
            self.current_action = f"type_string"
            self.logger.debug(f"輸入文字: {text}")
            
            input_mode = self._determine_input_mode(mode)
            
            try:
                if input_mode == InputMode.DIRECT and DIRECT_INPUT_AVAILABLE:
                    # DirectInput沒有內置的type功能，所以我們逐字輸入
                    for char in text:
                        directinput.press(char)
                        time.sleep(interval)
                else:
                    pyautogui.write(text, interval=interval)
                
                self.last_action_time = time.time()
                self.current_action = None
                
            except Exception as e:
                self.logger.error(f"輸入文字操作失敗: {str(e)}")
                self.current_action = None
                raise
    
    def execute_action_sequence(self, actions):
        """執行動作序列
        
        Args:
            actions (list): 動作列表，每個動作是(function, args, kwargs)的元組
        
        Returns:
            bool: 是否成功執行所有動作
        """
        self.logger.debug(f"開始執行動作序列，共 {len(actions)} 個動作")
        
        for i, (func, args, kwargs) in enumerate(actions):
            try:
                self.logger.debug(f"執行序列動作 {i+1}/{len(actions)}")
                func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"執行動作序列時失敗於步驟 {i+1}/{len(actions)}: {str(e)}")
                return False
        
        self.logger.debug("動作序列執行完成")
        return True
    
    def stop_all_actions(self):
        """停止所有動作"""
        with self.action_lock:
            self.logger.info("停止所有動作")
            
            # 釋放所有可能被按住的鍵
            common_keys = ['shift', 'ctrl', 'alt', 'win', 'up', 'down', 'left', 'right']
            for key in common_keys:
                try:
                    if DIRECT_INPUT_AVAILABLE:
                        directinput.keyUp(key)
                    pyautogui.keyUp(key)
                except:
                    pass
    
    def _wait_for_min_delay(self):
        """等待最小操作間隔"""
        if self.min_action_delay > 0:
            elapsed = time.time() - self.last_action_time
            if elapsed < self.min_action_delay:
                time.sleep(self.min_action_delay - elapsed)
    
    def _determine_input_mode(self, mode):
        """決定使用哪種輸入模式
        
        Args:
            mode (InputMode, optional): 指定的輸入模式
        
        Returns:
            InputMode: 實際使用的輸入模式
        """
        # 如果指定了模式，則使用指定的模式
        if mode is not None:
            return mode
        
        # 否則使用默認模式
        return self.default_input_mode
    
    def shutdown(self):
        """關閉執行器"""
        self.logger.info("關閉動作執行器")
        self.is_running = False
        self.stop_all_actions()