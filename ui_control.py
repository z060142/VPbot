#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
簡易UI控制與狀態追蹤系統
提供GUI介面用於控制腳本與監控狀態
"""

import os
import sys
import time
import threading
import logging
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import psutil

class StatusUI:
    """狀態UI類，提供GUI介面控制與監控"""
    
    def __init__(self, engine):
        """初始化UI
        
        Args:
            engine: 核心引擎實例
        """
        self.engine = engine
        self.logger = logging.getLogger("StatusUI")
        self.is_running = False
        self.logs_queue = []  # 使用普通列表而不是Queue
        self.log_handler = None
        self.root = None
        self.position_rows = []
        
        # 初始化完成
        self.logger.info("狀態UI已初始化")
    
    def _setup_log_handler(self):
        """設置日誌處理器以捕獲日誌"""
        class UILogHandler(logging.Handler):
            def __init__(self, ui):
                super().__init__()
                self.ui = ui
                self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            
            def emit(self, record):
                log_entry = self.format(record)
                self.ui.logs_queue.append(log_entry)
                # 限制日誌隊列大小
                if len(self.ui.logs_queue) > 1000:
                    self.ui.logs_queue = self.ui.logs_queue[-1000:]
        
        # 創建並添加處理器
        self.log_handler = UILogHandler(self)
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
    
    def _create_ui(self):
        """創建UI介面"""
        # 創建根窗口
        self.root = tk.Tk()
        self.root.title("遊戲職位管理自動化系統")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 設置樣式
        style = ttk.Style()
        style.configure("TButton", padding=5, font=('標楷體', 10))
        style.configure("TLabel", font=('標楷體', 10))
        style.configure("Header.TLabel", font=('標楷體', 12, 'bold'))
        style.configure("Status.TLabel", font=('標楷體', 10, 'bold'))
        
        # 創建主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 創建上方控制區
        control_frame = ttk.LabelFrame(main_frame, text="系統控制", padding=10)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 添加控制按鈕
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X)
        
        self.pause_button = ttk.Button(buttons_frame, text="暫停系統", command=self._toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="重啟系統", command=self._restart_system).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="重啟遊戲", command=self._restart_game).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="重置排程", command=self._reset_scheduler).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="刷新檢測", command=self._force_refresh).pack(side=tk.LEFT, padx=5)
        
        # 創建狀態顯示區
        status_frame = ttk.LabelFrame(main_frame, text="系統狀態", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        # 創建狀態標籤
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        ttk.Label(status_grid, text="遊戲狀態:", style="Header.TLabel").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.game_status_label = ttk.Label(status_grid, text="未知", style="Status.TLabel")
        self.game_status_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="目前任務:", style="Header.TLabel").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.current_task_label = ttk.Label(status_grid, text="無", style="Status.TLabel")
        self.current_task_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="系統狀態:", style="Header.TLabel").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.system_status_label = ttk.Label(status_grid, text="運行中", style="Status.TLabel")
        self.system_status_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="運行時間:", style="Header.TLabel").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.runtime_label = ttk.Label(status_grid, text="00:00:00", style="Status.TLabel")
        self.runtime_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # 添加系統資源使用區
        ttk.Label(status_grid, text="CPU使用率:", style="Header.TLabel").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.cpu_usage_label = ttk.Label(status_grid, text="0%", style="Status.TLabel")
        self.cpu_usage_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(status_grid, text="記憶體使用:", style="Header.TLabel").grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
        self.memory_usage_label = ttk.Label(status_grid, text="0 MB", style="Status.TLabel")
        self.memory_usage_label.grid(row=2, column=3, sticky=tk.W, padx=5, pady=2)
        
        # 創建職位狀態區
        positions_frame = ttk.LabelFrame(main_frame, text="職位狀態", padding=10)
        positions_frame.pack(fill=tk.X, pady=5)
        
        # 創建職位表格
        positions_table = ttk.Frame(positions_frame)
        positions_table.pack(fill=tk.X)
        
        # 表格標題
        ttk.Label(positions_table, text="職位", width=10, style="Header.TLabel").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(positions_table, text="狀態", width=10, style="Header.TLabel").grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(positions_table, text="申請數", width=10, style="Header.TLabel").grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(positions_table, text="超時數", width=10, style="Header.TLabel").grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(positions_table, text="操作", width=15, style="Header.TLabel").grid(row=0, column=4, padx=5, pady=2)
        
        # 職位狀態行
        self.position_rows = []
        for i in range(6):
            position_row = {}
            
            position_row['name'] = ttk.Label(positions_table, text=f"職位{i+1}", width=10)
            position_row['name'].grid(row=i+1, column=0, padx=5, pady=2)
            
            position_row['status'] = ttk.Label(positions_table, text="啟用", width=10)
            position_row['status'].grid(row=i+1, column=1, padx=5, pady=2)
            
            position_row['applications'] = ttk.Label(positions_table, text="0", width=10)
            position_row['applications'].grid(row=i+1, column=2, padx=5, pady=2)
            
            position_row['overtimes'] = ttk.Label(positions_table, text="0", width=10)
            position_row['overtimes'].grid(row=i+1, column=3, padx=5, pady=2)
            
            position_row['action_frame'] = ttk.Frame(positions_table)
            position_row['action_frame'].grid(row=i+1, column=4, padx=5, pady=2)
            
            position_row['toggle_button'] = ttk.Button(
                position_row['action_frame'], 
                text="禁用", 
                width=8,
                command=lambda idx=i: self._toggle_position(idx)
            )
            position_row['toggle_button'].pack(side=tk.LEFT, padx=2)
            
            self.position_rows.append(position_row)
        
        # 創建日誌顯示區
        log_frame = ttk.LabelFrame(main_frame, text="系統日誌", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 創建日誌文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Courier New", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)  # 設為只讀
        
        # 創建底部狀態欄
        status_bar = ttk.Frame(main_frame)
        status_bar.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_bar, text="© 2025 遊戲職位管理自動化系統").pack(side=tk.LEFT)
        
        self.status_message = ttk.Label(status_bar, text="就緒")
        self.status_message.pack(side=tk.RIGHT)
    
    def show(self):
        """顯示UI並啟動更新線程"""
        # 創建UI（必須在主線程中）
        self._create_ui()
        
        # 設置日誌處理器
        self._setup_log_handler()
        
        # 啟動標記
        self.is_running = True
        
        # 啟動更新線程
        update_thread = threading.Thread(target=self._update_loop, daemon=True)
        update_thread.start()
        
        # 開始定期更新UI (在主線程中)
        self._schedule_ui_update()
        
        # 顯示窗口
        self.root.mainloop()
    
    def _schedule_ui_update(self):
        """排程UI更新（在主線程中執行）"""
        if self.is_running and self.root:
            self._perform_ui_update()
            # 每秒更新一次
            self.root.after(1000, self._schedule_ui_update)
    
    def _update_loop(self):
        """更新線程循環：收集數據但不直接更新UI"""
        while self.is_running:
            try:
                # 此線程只收集數據，不直接更新UI
                # 數據更新是通過共享變量(self對象的屬性)進行的
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"更新循環出錯: {str(e)}")
    
    def _perform_ui_update(self):
        """執行UI更新（在主線程中）"""
        try:
            if not self.engine or not self.root:
                return
                
            # 更新遊戲狀態
            game_manager = self.engine.modules.get('game_manager')
            if game_manager:
                self.game_status_label.config(text=game_manager.current_status.name)
            
            # 更新當前任務
            task_scheduler = self.engine.modules.get('task_scheduler')
            if task_scheduler:
                current_task = task_scheduler.get_current_task()
                task_name = current_task.name if current_task else "無"
                self.current_task_label.config(text=task_name)
            
            # 更新系統狀態
            status = "暫停中" if self.engine.is_paused else "運行中"
            self.system_status_label.config(text=status)
            
            # 更新運行時間
            if self.engine.start_time:
                runtime = time.time() - self.engine.start_time
                hours = int(runtime // 3600)
                minutes = int((runtime % 3600) // 60)
                seconds = int(runtime % 60)
                runtime_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.runtime_label.config(text=runtime_text)
            
            # 更新系統資源使用
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            self.cpu_usage_label.config(text=f"{cpu_percent:.1f}%")
            self.memory_usage_label.config(text=f"{memory_mb:.1f} MB")
            
            # 更新職位狀態 - 確保直接從position_manager獲取最新狀態
            position_manager = self.engine.modules.get('position_manager')
            if position_manager:
                try:
                    # 強制獲取最新狀態
                    positions_status = position_manager.get_all_positions_status()
                    
                    for i, status in enumerate(positions_status):
                        if i < len(self.position_rows):
                            row = self.position_rows[i]
                            row['name'].config(text=status["name"])
                            
                            # 更新狀態文本和顏色
                            status_text = "啟用" if status["enabled"] else "禁用"
                            row['status'].config(text=status_text)
                            if status["enabled"]:
                                row['status'].config(foreground="green")
                            else:
                                row['status'].config(foreground="red")
                            
                            row['applications'].config(text=str(status["applications"]))
                            row['overtimes'].config(text=str(status["overtimes"]))
                            
                            # 更新按鈕文本和狀態
                            button_text = "禁用" if status["enabled"] else "啟用"
                            row['toggle_button'].config(text=button_text)
                except Exception as e:
                    self.logger.error(f"更新職位狀態時出錯: {str(e)}")
            
            # 更新日誌
            self._update_logs()
            
        except Exception as e:
            self.logger.error(f"更新UI顯示時出錯: {str(e)}")
    
    def force_update(self):
        """強制立即更新UI（供外部调用）"""
        if self.root:
            self.root.after(0, self._perform_ui_update)
    
    def _update_logs(self):
        """更新日誌顯示"""
        if not self.logs_queue:
            return
        
        # 啟用文本框編輯
        self.log_text.config(state=tk.NORMAL)
        
        # 添加新日誌
        for log in self.logs_queue:
            self.log_text.insert(tk.END, log + "\n")
        
        # 清空隊列
        self.logs_queue.clear()
        
        # 滾動到底部
        self.log_text.see(tk.END)
        
        # 禁用文本框編輯
        self.log_text.config(state=tk.DISABLED)
    
    def _toggle_pause(self):
        """切換系統暫停/恢復"""
        if self.engine.is_paused:
            self.engine.resume_all()
            self.pause_button.config(text="暫停系統")
            self.status_message.config(text="系統已恢復運行")
        else:
            self.engine.pause_all()
            self.pause_button.config(text="恢復系統")
            self.status_message.config(text="系統已暫停")
    
    def _restart_system(self):
        """重啟系統"""
        if messagebox.askyesno("確認", "確定要重啟整個系統嗎？"):
            self.status_message.config(text="正在重啟系統...")
            # 在單獨的線程中執行，避免阻塞UI
            threading.Thread(target=self.engine.restart, daemon=True).start()
    
    def _restart_game(self):
        """重啟遊戲"""
        self.status_message.config(text="正在重啟遊戲...")
        game_manager = self.engine.modules.get('game_manager')
        if game_manager:
            threading.Thread(target=game_manager.restart_game, daemon=True).start()
    
    def _reset_scheduler(self):
        """重置排程器"""
        self.status_message.config(text="正在重置排程...")
        task_scheduler = self.engine.modules.get('task_scheduler')
        if task_scheduler:
            task_scheduler.reset()
    
    def _force_refresh(self):
        """強制刷新檢測"""
        self.status_message.config(text="正在強制刷新檢測...")
        
        # 在新線程中運行以避免阻塞UI
        def refresh():
            try:
                image_detector = self.engine.modules.get('image_detector')
                monitor_manager = self.engine.modules.get('monitor_manager')
                
                if image_detector and monitor_manager:
                    screen_image = image_detector.get_screen_image(force_refresh=True)
                    result = monitor_manager.force_check_all(screen_image)
                    
                    # 更新狀態消息
                    if result:
                        if self.root:
                            self.root.after(0, lambda: self.status_message.config(text="已檢測並處理異常情況"))
                    else:
                        if self.root:
                            self.root.after(0, lambda: self.status_message.config(text="刷新完成，未檢測到異常"))
            except Exception as e:
                self.logger.error(f"強制刷新檢測時出錯: {str(e)}")
        
        threading.Thread(target=refresh, daemon=True).start()
    
    def _toggle_position(self, index):
        """切換職位啟用/禁用狀態
        
        Args:
            index (int): 職位索引
        """
        position_manager = self.engine.modules.get('position_manager')
        if not position_manager:
            return
            
        try:
            positions_status = position_manager.get_all_positions_status()
            
            if index < len(positions_status):
                position_id = positions_status[index]["id"]
                position_name = positions_status[index]["name"]
                enabled = positions_status[index]["enabled"]
                
                if enabled:
                    position_manager.disable_position(position_id)
                    self.status_message.config(text=f"職位 '{position_name}' 已禁用")
                else:
                    position_manager.enable_position(position_id)
                    self.status_message.config(text=f"職位 '{position_name}' 已啟用")
        except Exception as e:
            self.logger.error(f"切換職位狀態時出錯: {str(e)}")
    
    def _on_close(self):
        """窗口關閉處理"""
        if messagebox.askyesno("確認", "關閉UI不會停止系統運行。\n確定要關閉UI嗎？"):
            self.shutdown()
    
    def update_status_message(self, message):
        """更新狀態欄消息
        
        Args:
            message (str): 狀態消息
        """
        if self.root:
            self.status_message.config(text=message)
    
    def shutdown(self):
        """關閉UI"""
        self.logger.info("關閉狀態UI")
        self.is_running = False
        
        # 移除日誌處理器
        if self.log_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)
        
        # 關閉窗口
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

# 用於測試UI
def main():
    """主函數，用於獨立測試UI"""
    # 創建一個模擬的引擎對象
    class DummyEngine:
        def __init__(self):
            self.is_paused = False
            self.start_time = time.time()
            self.modules = {
                'game_manager': DummyGameManager(),
                'task_scheduler': DummyTaskScheduler(),
                'position_manager': DummyPositionManager(),
                'monitor_manager': DummyMonitorManager(),
                'image_detector': DummyImageDetector()
            }
        
        def pause_all(self):
            self.is_paused = True
            print("系統已暫停")
        
        def resume_all(self):
            self.is_paused = False
            print("系統已恢復")
        
        def restart(self):
            print("系統重啟中...")
    
    class DummyGameManager:
        def __init__(self):
            from enum import Enum
            class Status(Enum):
                RUNNING_NORMAL = "RUNNING_NORMAL"
            self.current_status = Status.RUNNING_NORMAL
        
        def restart_game(self):
            print("遊戲重啟中...")
    
    class DummyTaskScheduler:
        def __init__(self):
            self.current_task = None
        
        def get_current_task(self):
            return self.current_task
        
        def reset(self):
            print("排程器重置中...")
    
    class DummyPositionManager:
        def get_all_positions_status(self):
            return [
                {"id": f"pos{i}", "name": f"職位{i+1}", "enabled": i % 2 == 0, "applications": i*2, "overtimes": i}
                for i in range(6)
            ]
        
        def enable_position(self, position_id):
            print(f"啟用職位 {position_id}")
        
        def disable_position(self, position_id):
            print(f"禁用職位 {position_id}")
    
    class DummyMonitorManager:
        def force_check_all(self, screen_image):
            print("強制檢查所有監控項...")
            return False
    
    class DummyImageDetector:
        def get_screen_image(self, force_refresh=False):
            print(f"獲取屏幕圖像 (強制刷新: {force_refresh})")
            return None
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 創建引擎實例
    dummy_engine = DummyEngine()
    
    # 創建並顯示UI
    ui = StatusUI(dummy_engine)
    
    # 生成一些示例日誌
    logger = logging.getLogger("Test")
    logger.info("這是一條測試日誌信息")
    logger.warning("這是一條測試警告信息")
    logger.error("這是一條測試錯誤信息")
    
    # 顯示UI
    ui.show()

if __name__ == "__main__":
    main()