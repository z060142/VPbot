#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任務排程器模組
負責任務優先級管理與執行排程
"""

import time
import logging
import threading
from collections import deque

class Task:
    """任務類定義"""
    def __init__(self, id, name, priority, interval_minutes=None, interval_seconds=None, action=None):
        """初始化任務
        
        Args:
            id (str): 任務唯一ID
            name (str): 任務名稱
            priority (int): 任務優先級(0-100)
            interval_minutes (float, optional): 執行間隔(分鐘)
            interval_seconds (float, optional): 執行間隔(秒)
            action (function, optional): 執行函數
        """
        self.id = id
        self.name = name
        self.priority = priority
        
        # 轉換所有間隔為秒
        if interval_seconds is not None:
            self.interval_seconds = interval_seconds
        elif interval_minutes is not None:
            self.interval_seconds = interval_minutes * 60
        else:
            self.interval_seconds = 300  # 默認5分鐘
            
        self.action = action
        self.last_execution_time = 0
        self.is_running = False
        self.execution_count = 0
        self.consecutive_failures = 0
        self.max_retries = 3
        self.current_step = 0
        self.total_steps = 1
        self.paused = False
    
    def should_run(self):
        """檢查任務是否應該執行
        
        Returns:
            bool: 是否應該執行
        """
        # 如果任務正在運行或已暫停，則不執行
        if self.is_running or self.paused:
            return False
        
        # 檢查間隔時間（使用秒）
        elapsed_seconds = time.time() - self.last_execution_time
        return elapsed_seconds >= self.interval_seconds
    
    def reset_execution(self):
        """重置執行狀態"""
        self.is_running = False
        self.current_step = 0
    
    def get_progress(self):
        """獲取任務進度
        
        Returns:
            float: 進度百分比 (0-100)
        """
        if self.total_steps <= 1:
            return 0 if not self.is_running else 100
        
        return (self.current_step / self.total_steps) * 100

class TaskScheduler:
    """任務排程器類"""
    def __init__(self):
        """初始化任務排程器"""
        self.logger = logging.getLogger("TaskScheduler")
        self.tasks = []  # 任務列表
        self.is_paused = False  # 排程器暫停狀態
        self.current_task_index = None  # 當前執行的任務索引
        self.lock = threading.Lock()  # 線程鎖
        
        self.logger.info("任務排程器初始化完成")
    
    def add_task(self, id, name, priority, interval_minutes=None, interval_seconds=None, action=None):
        """添加任務
        
        Args:
            id (str): 任務唯一ID
            name (str): 任務名稱
            priority (int): 任務優先級(0-100)
            interval_minutes (float, optional): 執行間隔(分鐘)
            interval_seconds (float, optional): 執行間隔(秒)
            action (function, optional): 執行函數
        
        Returns:
            Task: 添加的任務
        """
        with self.lock:
            # 檢查是否已存在同ID的任務
            for task in self.tasks:
                if task.id == id:
                    self.logger.warning(f"已存在ID為 '{id}' 的任務，無法添加")
                    return None
            
            # 創建新任務
            task = Task(id, name, priority, interval_minutes, interval_seconds, action)
            self.tasks.append(task)
            
            # 按優先級排序任務列表
            self.tasks.sort(key=lambda t: t.priority, reverse=True)
            
            self.logger.info(f"添加任務 '{name}' (ID: {id})")
            return task
    
    def remove_task(self, task_id):
        """移除任務
        
        Args:
            task_id (str): 任務唯一ID
        
        Returns:
            bool: 是否成功移除
        """
        with self.lock:
            # 查找任務
            for i, task in enumerate(self.tasks):
                if task.id == task_id:
                    # 檢查是否是當前執行的任務
                    if self.current_task_index is not None and i == self.current_task_index:
                        task.is_running = False
                        self.current_task_index = None
                    
                    # 移除任務
                    self.tasks.pop(i)
                    self.logger.info(f"移除任務 '{task.name}' (ID: {task_id})")
                    return True
            
            self.logger.warning(f"找不到ID為 '{task_id}' 的任務，無法移除")
            return False
    
    def get_task(self, task_id):
        """獲取任務
        
        Args:
            task_id (str): 任務唯一ID
        
        Returns:
            Task: 任務對象，如果不存在則返回None
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_current_task(self):
        """獲取當前正在執行的任務
        
        Returns:
            Task: 當前任務，如果沒有則返回None
        """
        if self.current_task_index is not None and 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None
    
    def execute_current_task_step(self):
        """執行當前任務步驟"""
        # 如果排程器已暫停，則不執行任何操作
        if self.is_paused:
            return
        
        with self.lock:
            # 如果沒有進行中的任務，則檢查是否有新任務需要執行
            if self.current_task_index is None:
                self._select_next_task()
            
            # 獲取當前任務並執行
            current_task = self.get_current_task()
            if current_task and current_task.is_running:
                self._execute_task(current_task)
    
    def _select_next_task(self):
        """選擇下一個要執行的任務"""
        # 選擇優先級最高的應該運行的任務
        for i, task in enumerate(self.tasks):
            if task.should_run():
                task.is_running = True
                task.last_execution_time = time.time()
                task.execution_count += 1
                task.current_step = 0
                self.current_task_index = i
                self.logger.info(f"開始執行任務 '{task.name}' (ID: {task.id})")
                return
    
    def _execute_task(self, task):
        """執行任務
        
        Args:
            task (Task): 要執行的任務
        """
        try:
            # 執行任務動作
            result = task.action()
            
            # 任務執行完成
            task.is_running = False
            self.current_task_index = None
            
            if result:
                task.consecutive_failures = 0
                self.logger.info(f"任務 '{task.name}' 執行成功")
            else:
                task.consecutive_failures += 1
                self.logger.warning(f"任務 '{task.name}' 返回失敗，連續失敗次數: {task.consecutive_failures}")
                
                # 如果連續失敗次數超過閾值，增加間隔時間
                if task.consecutive_failures >= task.max_retries:
                    self.logger.warning(f"任務 '{task.name}' 連續失敗次數過多，將增加間隔時間")
                    # 這裏可以實現任務間隔時間的動態調整
        
        except Exception as e:
            self.logger.error(f"執行任務 '{task.name}' 時出錯: {str(e)}")
            task.is_running = False
            self.current_task_index = None
            task.consecutive_failures += 1
    
    def pause_scheduler(self):
        """暫停排程器"""
        with self.lock:
            self.is_paused = True
            self.logger.info("任務排程器已暫停")
    
    def resume_scheduler(self):
        """恢復排程器"""
        with self.lock:
            self.is_paused = False
            self.logger.info("任務排程器已恢復")
    
    def pause_task(self, task_id):
        """暫停指定任務
        
        Args:
            task_id (str): 任務ID
        
        Returns:
            bool: 是否成功暫停
        """
        task = self.get_task(task_id)
        if task:
            with self.lock:
                task.paused = True
                self.logger.info(f"任務 '{task.name}' 已暫停")
            return True
        return False
    
    def resume_task(self, task_id):
        """恢復指定任務
        
        Args:
            task_id (str): 任務ID
        
        Returns:
            bool: 是否成功恢復
        """
        task = self.get_task(task_id)
        if task:
            with self.lock:
                task.paused = False
                self.logger.info(f"任務 '{task.name}' 已恢復")
            return True
        return False
    
    def restart_task(self, task_id):
        """重新啟動指定任務
        
        Args:
            task_id (str): 任務ID
        
        Returns:
            bool: 是否成功重啟
        """
        task = self.get_task(task_id)
        if task:
            with self.lock:
                task.is_running = False
                task.last_execution_time = 0  # 設為0使其立即可執行
                task.current_step = 0
                task.consecutive_failures = 0
                task.paused = False
                self.logger.info(f"任務 '{task.name}' 已重啟")
            return True
        return False
    
    def reset(self):
        """重置排程器狀態"""
        with self.lock:
            # 停止當前任務
            if self.current_task_index is not None:
                current_task = self.tasks[self.current_task_index]
                current_task.is_running = False
                self.logger.info(f"停止當前任務 '{current_task.name}'")
            
            # 重置所有任務的執行時間，使其下次可執行
            for task in self.tasks:
                task.last_execution_time = 0
                task.current_step = 0
                task.consecutive_failures = 0
            
            self.current_task_index = None
            self.is_paused = False
            
            self.logger.info("任務排程器已重置")
    
    def skip_current_task(self):
        """跳過當前任務"""
        with self.lock:
            if self.current_task_index is not None:
                current_task = self.tasks[self.current_task_index]
                current_task.is_running = False
                self.logger.info(f"跳過當前任務 '{current_task.name}'")
                self.current_task_index = None
                return True
        
        self.logger.warning("沒有正在執行的任務可跳過")
        return False
    
    def get_all_tasks_status(self):
        """獲取所有任務的狀態
        
        Returns:
            list: 任務狀態列表
        """
        status_list = []
        
        for task in self.tasks:
            status = {
                "id": task.id,
                "name": task.name,
                "priority": task.priority,
                "interval_minutes": task.interval_minutes,
                "last_execution_time": task.last_execution_time,
                "is_running": task.is_running,
                "execution_count": task.execution_count,
                "consecutive_failures": task.consecutive_failures,
                "paused": task.paused,
                "progress": task.get_progress()
            }
            status_list.append(status)
        
        return status_list