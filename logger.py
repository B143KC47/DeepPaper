import time
import threading
from datetime import datetime

class AnalysisLogger:
    """分析过程日志记录器
    
    用于记录PDF分析过程中的各个步骤和状态，支持实时查看日志。
    """
    
    def __init__(self):
        """初始化日志记录器"""
        self.logs = []
        self.lock = threading.Lock()  # 用于线程安全的日志记录
        self.last_update_time = time.time()
    
    def info(self, message):
        """记录信息级别的日志
        
        Args:
            message: 日志消息
        """
        self._add_log('INFO', message)
    
    def warning(self, message):
        """记录警告级别的日志
        
        Args:
            message: 日志消息
        """
        self._add_log('WARNING', message)
    
    def error(self, message):
        """记录错误级别的日志
        
        Args:
            message: 日志消息
        """
        self._add_log('ERROR', message)
    
    def _add_log(self, level, message):
        """添加日志记录
        
        Args:
            level: 日志级别
            message: 日志消息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        
        # 使用锁确保线程安全
        with self.lock:
            self.logs.append(log_entry)
            # 同时在控制台输出
            print(f"[{timestamp}] [{level}] {message}")
            self.last_update_time = time.time()
    
    def get_logs(self, since_timestamp=None):
        """获取日志记录
        
        Args:
            since_timestamp: 可选，只返回此时间戳之后的日志
            
        Returns:
            日志记录列表
        """
        with self.lock:
            if since_timestamp is None:
                return self.logs.copy()
            else:
                # 返回指定时间戳之后的日志
                return [log for log in self.logs if log['timestamp'] > since_timestamp]
    
    def get_logs_since_last_update(self):
        """获取自上次更新以来的日志
        
        Returns:
            最新的日志记录列表
        """
        with self.lock:
            # 计算距离上次更新的时间
            current_time = time.time()
            logs_since_last = self.logs[-10:] if len(self.logs) > 10 else self.logs
            self.last_update_time = current_time
            return logs_since_last
    
    def clear_analysis_logs(self):
        """清除所有分析日志"""
        with self.lock:
            self.logs = []
            self.last_update_time = time.time()

# 创建全局日志记录器实例
logger = AnalysisLogger()