#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
遠程控制客戶端 - 整合版
專為工作排程器主腳本設計的輕量級遠程控制客戶端
"""

import socketio
import time
import os
import subprocess
import sys
import logging
import threading
import json
import ssl
import signal
from logging.handlers import RotatingFileHandler

# 配置信息
SERVER_URL = "https://aa.bdmc.live:9753"  # 更改為您的伺服器地址
CLIENT_KEY = "96829ba427be5af9391e4c2c3f8b36696ed170c32e0ccc746e70f8e136c084277346eb361a40453b6483ffa73fe92e4d9766752d0b978bba9b7f89e1fcb55a76"       # 更改為您的客戶端密鑰
TARGET_PROGRAM = "LastWar.exe"              # 目標程序名稱
MAIN_SCRIPT_PATH = "bot start.py"      # 主排程腳本路徑
REMOVE_SCRIPT_PATH = "remove_job.py"        # 移除任務腳本路徑
BOT_CHAT_PATH = "bot_chat.py"               # 聊天腳本路徑

# 設置日誌
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ControlClient")
logger.setLevel(logging.INFO)

# 添加控制台處理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# 添加文件處理器
file_handler = RotatingFileHandler(
    "control_client.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=3
)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

class ControlClient:
    """控制客戶端類"""
    
    def __init__(self, server_url, client_key):
        """初始化控制客戶端"""
        self.server_url = server_url
        self.client_key = client_key
        
        # 註冊支持的命令
        self.registered_commands = [
            # 系統控制命令
            "pause system",        # 暫停系統
            "resume system",       # 恢復系統
            "restart system",      # 重啟系統
            "restart game",        # 重啟遊戲
            "reset scheduler",     # 重置排程
            "refresh detection",   # 刷新檢測
            
            # 職位管理命令
            "enable position1",    # 啟用職位1
            "enable position2",    # 啟用職位2
            "enable position3",    # 啟用職位3
            "enable position4",    # 啟用職位4
            "enable position5",    # 啟用職位5
            "enable position6",    # 啟用職位6
            "disable position1",   # 禁用職位1
            "disable position2",   # 禁用職位2
            "disable position3",   # 禁用職位3
            "disable position4",   # 禁用職位4
            "disable position5",   # 禁用職位5
            "disable position6",   # 禁用職位6
            
            # 特殊命令
            "remove",              # 罷黜特定ID的職位
            "say:",                # 發送聊天訊息
            
            # 兼容舊版命令
            "restart wolf",        # 舊版重啟遊戲命令
            "restart",             # 舊版重啟遊戲命令
            "restart bot",         # 舊版重啟系統命令
            "reset"                # 舊版重置排程命令
        ]
        
        # 創建事件，用於通知主腳本各種控制信號
        self.system_pause_event = threading.Event()
        self.system_resume_event = threading.Event()
        self.restart_system_event = threading.Event()  # 重啟整個系統
        self.restart_game_event = threading.Event()    # 僅重啟遊戲
        self.reset_scheduler_event = threading.Event() # 重置排程
        self.refresh_detection_event = threading.Event() # 刷新檢測
        
        # 職位控制信息
        self.position_control = {"active": False, "position_id": None, "enable": False}
        
        # 移除任務信息
        self.remove_job_info = {"active": False, "job_id": None}
        
        # 聊天信息
        self.chat_info = {"active": False, "content": None}
        
        # 創建Socket.IO客戶端
        self.sio = socketio.Client(ssl_verify=False)
        
        # 註冊事件處理
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('authenticated', self._on_authenticated)
        self.sio.on('command', self._on_command)
        
        # 連接狀態
        self.connected = False
        self.authenticated = False
        self.should_exit = False
    
    def start(self):
        """開始連接伺服器"""
        try:
            logger.info(f"正在連接到伺服器: {self.server_url}")
            self.sio.connect(self.server_url)
            return True
        except Exception as e:
            logger.error(f"連接伺服器失敗: {str(e)}")
            return False
    
    def stop(self):
        """停止連接"""
        self.should_exit = True
        if self.connected:
            self.sio.disconnect()
        logger.info("客戶端已停止")
    
    def run_in_thread(self):
        """在線程中運行客戶端"""
        # 創建和啟動客戶端線程
        self.client_thread = threading.Thread(target=self._run_forever)
        self.client_thread.daemon = True  # 設置為守護線程
        self.client_thread.start()
        logger.info("控制客戶端線程已啟動")
        return self.client_thread
    
    def _run_forever(self):
        """在線程中持續運行"""
        while not self.should_exit:
            if not self.connected:
                success = self.start()
                if not success:
                    logger.info("5秒後重試連接...")
                    time.sleep(5)
                    continue
            
            # 防止線程結束
            try:
                time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                logger.info("收到退出信號")
                self.stop()
                break
    
    def _on_connect(self):
        """連接成功的回調"""
        self.connected = True
        logger.info("已連接到伺服器")
        
        # 發送認證
        self.sio.emit('authenticate', {
            'type': 'client',
            'clientKey': self.client_key,
            'commands': self.registered_commands
        })
    
    def _on_disconnect(self):
        """斷開連接的回調"""
        self.connected = False
        self.authenticated = False
        logger.info("已與伺服器斷開連接")
    
    def _on_authenticated(self, data):
        """認證結果的回調"""
        if data.get('success'):
            if not self.authenticated:  # 避免重複日誌
                self.authenticated = True
                logger.info("認證成功")
        else:
            self.authenticated = False
            logger.error(f"認證失敗: {data.get('error', '未知錯誤')}")
            # 斷開並稍後重連
            self.sio.disconnect()
    
    def _on_command(self, data):
        """接收到命令的回調"""
        command = data.get('command', '')
        params = data.get('params', {})
        from_user = data.get('from', 'unknown')
        
        logger.info(f"收到來自 {from_user} 的命令: {command}")
        
        # 處理命令
        try:
            # 暫停系統
            if command == "pause system":
                result = self._pause_system()
                self._send_command_result(command, True, result)
            
            # 恢復系統
            elif command == "resume system":
                result = self._resume_system()
                self._send_command_result(command, True, result)
            
            # 重啟系統
            elif command == "restart system" or command == "restart bot":
                result = self._restart_system()
                self._send_command_result(command, True, result)
            
            # 重啟遊戲
            elif command == "restart game" or command.startswith("restart wolf") or command == "restart":
                result = self._restart_game()
                self._send_command_result(command, True, result)
            
            # 重置排程
            elif command == "reset scheduler" or command == "reset":
                result = self._reset_scheduler()
                self._send_command_result(command, True, result)
            
            # 刷新檢測
            elif command == "refresh detection":
                result = self._refresh_detection()
                self._send_command_result(command, True, result)
            
            # 啟用職位
            elif command.startswith("enable position"):
                try:
                    position_num = int(command.replace("enable position", "").strip())
                    if 1 <= position_num <= 6:
                        result = self._toggle_position(f"position_{position_num}", True)
                        self._send_command_result(command, True, result)
                    else:
                        self._send_command_result(command, False, "無效的職位編號")
                except ValueError:
                    self._send_command_result(command, False, "無效的職位編號格式")
            
            # 禁用職位
            elif command.startswith("disable position"):
                try:
                    position_num = int(command.replace("disable position", "").strip())
                    if 1 <= position_num <= 6:
                        result = self._toggle_position(f"position_{position_num}", False)
                        self._send_command_result(command, True, result)
                    else:
                        self._send_command_result(command, False, "無效的職位編號")
                except ValueError:
                    self._send_command_result(command, False, "無效的職位編號格式")
            
            # 罷黜職位
            elif command.startswith("remove "):
                # 提取ID
                try:
                    job_id = command.split("remove ")[1].strip()
                    result = self._remove_job(job_id)
                    self._send_command_result(command, True, result)
                except IndexError:
                    self._send_command_result(command, False, "缺少任務ID")
            
            # 發送聊天
            elif command.startswith("say:"):
                # 提取聊天內容
                try:
                    content = command[4:].strip()  # 去除"say:"前綴和空白
                    if content:
                        result = self._send_chat(content)
                        self._send_command_result(command, True, result)
                    else:
                        self._send_command_result(command, False, "聊天內容不能為空")
                except Exception as e:
                    self._send_command_result(command, False, f"處理聊天命令時出錯: {str(e)}")
            
            else:
                self._send_command_result(command, False, "未知命令")
        
        except Exception as e:
            logger.exception(f"執行命令 {command} 時出錯")
            self._send_command_result(command, False, f"執行錯誤: {str(e)}")
    
    def _send_command_result(self, command, success, message):
        """發送命令執行結果到伺服器"""
        if self.connected and self.authenticated:
            self.sio.emit('commandResult', {
                'command': command,
                'success': success,
                'message': message,
                'timestamp': time.time()
            })
    
    # 命令處理函數
    
    def _pause_system(self):
        """暫停系統"""
        logger.info("設置系統暫停信號")
        self.system_pause_event.set()
        return "已設置系統暫停信號"
    
    def _resume_system(self):
        """恢復系統"""
        logger.info("設置系統恢復信號")
        self.system_resume_event.set()
        return "已設置系統恢復信號"
    
    def _restart_system(self):
        """重啟整個系統"""
        logger.info("設置系統重啟信號")
        self.restart_system_event.set()
        return "已設置系統重啟信號"
    
    def _restart_game(self):
        """重啟遊戲"""
        try:
            logger.info("重啟遊戲")
            
            # 設置遊戲重啟信號
            self.restart_game_event.set()
            
            return "已設置遊戲重啟信號"
        except Exception as e:
            logger.exception("重啟遊戲時出錯")
            return f"重啟遊戲時出錯: {str(e)}"
    
    def _reset_scheduler(self):
        """重置排程器"""
        logger.info("設置排程重置信號")
        self.reset_scheduler_event.set()
        return "已設置排程重置信號"
    
    def _refresh_detection(self):
        """刷新檢測"""
        logger.info("設置刷新檢測信號")
        self.refresh_detection_event.set()
        return "已設置刷新檢測信號"
    
    def _toggle_position(self, position_id, enable):
        """切換職位啟用/禁用狀態
        
        Args:
            position_id (str): 職位ID
            enable (bool): 是否啟用
        """
        try:
            logger.info(f"切換職位 {position_id} 狀態為 {'啟用' if enable else '禁用'}")
            
            # 設置職位控制信息
            self.position_control["active"] = True
            self.position_control["position_id"] = position_id
            self.position_control["enable"] = enable
            
            return f"已設置職位 {position_id} 為 {'啟用' if enable else '禁用'}"
        except Exception as e:
            logger.exception("切換職位狀態時出錯")
            return f"切換職位狀態時出錯: {str(e)}"
    
    def _remove_job(self, job_id):
        """紀錄任務ID，設置移除信號
        
        Args:
            job_id (str): 任務ID
        """
        try:
            logger.info(f"處理移除任務: {job_id}")
            
            # 設置移除任務信息
            self.remove_job_info["active"] = True
            self.remove_job_info["job_id"] = job_id
            
            return f"已設置移除任務信號，ID: {job_id}"
        except Exception as e:
            logger.exception("設置移除任務時出錯")
            return f"設置移除任務時出錯: {str(e)}"
    
    def _send_chat(self, content):
        """紀錄聊天內容，設置聊天信號
        
        Args:
            content (str): 聊天內容
        """
        try:
            logger.info(f"處理聊天命令: {content}")
            
            # 設置聊天信息
            self.chat_info["active"] = True
            self.chat_info["content"] = content
            
            return f"已設置聊天信號，內容: '{content}'"
        except Exception as e:
            logger.exception("設置聊天命令時出錯")
            return f"設置聊天命令時出錯: {str(e)}"
    
    # 信號檢查方法（供主腳本調用）
    
    def check_system_pause(self):
        """檢查是否有系統暫停信號"""
        if self.system_pause_event.is_set():
            self.system_pause_event.clear()
            return True
        return False
    
    def check_system_resume(self):
        """檢查是否有系統恢復信號"""
        if self.system_resume_event.is_set():
            self.system_resume_event.clear()
            return True
        return False
    
    def check_restart_system(self):
        """檢查是否有系統重啟信號"""
        if self.restart_system_event.is_set():
            self.restart_system_event.clear()
            return True
        return False
    
    def check_restart_game(self):
        """檢查是否有遊戲重啟信號"""
        if self.restart_game_event.is_set():
            self.restart_game_event.clear()
            return True
        return False
    
    def check_reset_scheduler(self):
        """檢查是否有排程重置信號"""
        if self.reset_scheduler_event.is_set():
            self.reset_scheduler_event.clear()
            return True
        return False
    
    def check_refresh_detection(self):
        """檢查是否有刷新檢測信號"""
        if self.refresh_detection_event.is_set():
            self.refresh_detection_event.clear()
            return True
        return False
    
    def check_position_control(self):
        """檢查是否有職位控制請求
        
        Returns:
            tuple: (position_id, enable) 如果有控制請求，否則返回 (None, None)
        """
        if self.position_control["active"]:
            position_id = self.position_control["position_id"]
            enable = self.position_control["enable"]
            
            # 重置控制信息
            self.position_control["active"] = False
            self.position_control["position_id"] = None
            self.position_control["enable"] = False
            
            return (position_id, enable)
        
        return (None, None)
    
    def check_remove_job(self):
        """檢查是否有移除任務請求
        
        Returns:
            str: 任務ID，如果沒有則返回None
        """
        if self.remove_job_info["active"]:
            job_id = self.remove_job_info["job_id"]
            
            # 重置控制信息
            self.remove_job_info["active"] = False
            self.remove_job_info["job_id"] = None
            
            return job_id
        
        return None
    
    def check_chat_request(self):
        """檢查是否有聊天請求
        
        Returns:
            str: 聊天內容，如果沒有則返回None
        """
        if self.chat_info["active"]:
            content = self.chat_info["content"]
            
            # 重置控制信息
            self.chat_info["active"] = False
            self.chat_info["content"] = None
            
            return content
        
        return None

# 主程序
if __name__ == "__main__":
    # 此部分僅用於獨立測試，實際使用時應由主腳本導入
    print("啟動控制客戶端 (測試模式)")
    
    client = ControlClient(SERVER_URL, CLIENT_KEY)
    
    # 註冊信號處理器
    def signal_handler(sig, frame):
        print("接收到退出信號，正在停止客戶端...")
        client.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 啟動客戶端
    try:
        client.start()
        print("按Ctrl+C退出")
        
        # 模擬主腳本循環
        while True:
            if client.check_system_pause():
                print("收到系統暫停信號，應暫停系統")
            
            if client.check_system_resume():
                print("收到系統恢復信號，應恢復系統")
            
            if client.check_restart_system():
                print("收到系統重啟信號，應重啟系統")
            
            if client.check_restart_game():
                print("收到遊戲重啟信號，應重啟遊戲")
            
            if client.check_reset_scheduler():
                print("收到排程重置信號，應重置排程")
            
            if client.check_refresh_detection():
                print("收到刷新檢測信號，應刷新檢測")
            
            position_control = client.check_position_control()
            if position_control[0]:
                print(f"收到職位控制請求: {position_control[0]} -> {'啟用' if position_control[1] else '禁用'}")
            
            job_id = client.check_remove_job()
            if job_id:
                print(f"收到移除任務請求，ID: {job_id}")
            
            chat_content = client.check_chat_request()
            if chat_content:
                print(f"收到聊天請求，內容: '{chat_content}'")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序中斷")
    finally:
        client.stop()
        print("客戶端已停止")