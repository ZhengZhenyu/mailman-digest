#!/usr/bin/env python3
"""
定时任务调度模块
"""

import logging
from typing import Dict, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, config: Dict):
        """
        初始化调度器
        
        Args:
            config: 调度配置
        """
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.timezone = config.get('timezone', 'Asia/Shanghai')
    
    def add_daily_task(self, task_func: Callable, cron_expr: str) -> None:
        """
        添加每日定时任务
        
        Args:
            task_func: 任务函数
            cron_expr: cron表达式
        """
        # 解析cron表达式
        parts = cron_expr.split()
        if len(parts) != 5:
            logger.error(f"无效的cron表达式: {cron_expr}")
            return
        
        minute, hour, day, month, day_of_week = parts
        
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=self.timezone
        )
        
        self.scheduler.add_job(
            task_func,
            trigger=trigger,
            id='daily_digest',
            name='每日邮件列表汇总',
            replace_existing=True
        )
        
        logger.info(f"定时任务已添加: {cron_expr} ({self.timezone})")
    
    def start(self) -> None:
        """
        启动调度器
        """
        self.scheduler.start()
        logger.info("调度器已启动")
    
    def stop(self) -> None:
        """
        停止调度器
        """
        self.scheduler.shutdown()
        logger.info("调度器已停止")
    
    def get_next_run_time(self) -> datetime:
        """
        获取下次运行时间
        
        Returns:
            下次运行时间
        """
        job = self.scheduler.get_job('daily_digest')
        if job:
            return job.next_run_time
        return None


def start_scheduler(config: Dict, task_func: Callable) -> None:
    """
    启动定时任务调度器
    
    Args:
        config: 完整配置
        task_func: 任务函数
    """
    schedule_config = config.get('schedule', {})
    cron_expr = schedule_config.get('cron', '0 9 * * *')
    
    scheduler = TaskScheduler(schedule_config)
    scheduler.add_daily_task(task_func, cron_expr)
    scheduler.start()
    
    next_run = scheduler.get_next_run_time()
    if next_run:
        logger.info(f"下次运行时间: {next_run}")
    
    # 保持程序运行
    try:
        import signal
        import time
        
        def signal_handler(sig, frame):
            logger.info("收到停止信号，正在关闭调度器...")
            scheduler.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("调度器运行中，按 Ctrl+C 停止")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        scheduler.stop()