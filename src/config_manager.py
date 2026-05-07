#!/usr/bin/env python3
"""
配置文件管理模块
"""

import yaml
import json
import os
from typing import Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在: {self.config_path}")
                return {}
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    self.config = yaml.safe_load(f)
                elif self.config_path.endswith('.json'):
                    self.config = json.load(f)
                else:
                    logger.error(f"不支持的配置文件格式: {self.config_path}")
                    return {}
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return self.config
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return {}
    
    def get_config(self) -> Dict:
        """
        获取完整配置
        
        Returns:
            配置字典
        """
        return self.config
    
    def get_section(self, section: str) -> Dict:
        """
        获取配置的某个部分
        
        Args:
            section: 配置部分名称
            
        Returns:
            配置部分字典
        """
        return self.config.get(section, {})
    
    def save_config(self) -> bool:
        """
        保存配置文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                elif self.config_path.endswith('.json'):
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置文件保存成功: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"配置文件保存失败: {e}")
            return False
    
    def update_config(self, updates: Dict) -> bool:
        """
        更新配置
        
        Args:
            updates: 更新的配置字典
            
        Returns:
            是否更新成功
        """
        self.config.update(updates)
        return self.save_config()


class ProcessedEmailsManager:
    """已处理邮件记录管理器"""
    
    def __init__(self, processed_file: str):
        """
        初始化已处理邮件管理器
        
        Args:
            processed_file: 已处理邮件记录文件路径
        """
        self.processed_file = processed_file
        self.processed_emails = {}
        self.load_processed_emails()
    
    def load_processed_emails(self) -> Dict:
        """
        加载已处理邮件记录
        
        Returns:
            已处理邮件字典
        """
        try:
            if os.path.exists(self.processed_file):
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    self.processed_emails = json.load(f)
                logger.info(f"已处理邮件记录加载成功: {self.processed_file}")
            else:
                self.processed_emails = {}
                logger.info("已处理邮件记录文件不存在，将创建新文件")
            
            return self.processed_emails
            
        except Exception as e:
            logger.error(f"已处理邮件记录加载失败: {e}")
            return {}
    
    def is_processed(self, email_url: str) -> bool:
        """
        检查邮件是否已处理
        
        Args:
            email_url: 邮件URL
            
        Returns:
            是否已处理
        """
        return email_url in self.processed_emails
    
    def mark_processed(self, email_url: str, email_info: Dict) -> None:
        """
        标记邮件为已处理
        
        Args:
            email_url: 邮件URL
            email_info: 邮件信息
        """
        self.processed_emails[email_url] = {
            'processed_at': email_info.get('processed_at', ''),
            'subject': email_info.get('subject', ''),
            'community': email_info.get('community', ''),
            'list': email_info.get('list', '')
        }
    
    def save_processed_emails(self) -> bool:
        """
        保存已处理邮件记录
        
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.processed_file), exist_ok=True)
            
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_emails, f, indent=2, ensure_ascii=False)
            
            logger.info(f"已处理邮件记录保存成功: {self.processed_file}")
            return True
            
        except Exception as e:
            logger.error(f"已处理邮件记录保存失败: {e}")
            return False
    
    def filter_new_emails(self, emails: list) -> list:
        """
        过滤出新邮件（未处理的）
        
        Args:
            emails: 邮件列表
            
        Returns:
            新邮件列表
        """
        new_emails = []
        for email in emails:
            email_url = email.get('url', '')
            if email_url and not self.is_processed(email_url):
                new_emails.append(email)
        
        return new_emails
    
    def cleanup_old_records(self, days: int = 30) -> None:
        """
        清理旧的记录
        
        Args:
            days: 保留天数
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for url, info in self.processed_emails.items():
            processed_at = info.get('processed_at', '')
            if processed_at:
                try:
                    processed_date = datetime.strptime(processed_at, '%Y-%m-%d %H:%M:%S')
                    if processed_date < cutoff_date:
                        to_remove.append(url)
                except:
                    pass
        
        for url in to_remove:
            del self.processed_emails[url]
        
        if to_remove:
            logger.info(f"清理了 {len(to_remove)} 条旧记录")
            self.save_processed_emails()


def load_config(config_path: str) -> Dict:
    """
    加载配置文件的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    manager = ConfigManager(config_path)
    return manager.get_config()