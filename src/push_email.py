#!/usr/bin/env python3
"""
邮件推送模块
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailPusher:
    """邮件推送器"""
    
    def __init__(self, config: Dict):
        """
        初始化邮件推送器
        
        Args:
            config: 邮件推送配置
        """
        self.enabled = config.get('enabled', False)
        self.smtp_server = config.get('smtp_server', '')
        self.smtp_port = config.get('smtp_port', 465)
        self.smtp_user = config.get('smtp_user', '')
        self.smtp_password = config.get('smtp_password', '')
        self.smtp_use_ssl = config.get('smtp_use_ssl', True)
        self.from_addr = config.get('from', '')
        self.from_name = config.get('from_name', '邮件列表汇总机器人')
        self.recipients = config.get('recipients', [])
        self.subject_template = config.get('subject_template', '【每日邮件列表汇总】{date}')
    
    def send_email(self, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选）
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.info("邮件推送未启用")
            return False
        
        if not self.recipients:
            logger.warning("未配置邮件接收者")
            return False
        
        try:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_addr}>"
            msg['To'] = ', '.join(self.recipients)
            
            # 添加纯文本内容
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 连接SMTP服务器并发送
            if self.smtp_use_ssl:
                smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
                smtp.starttls()
            
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.sendmail(self.from_addr, self.recipients, msg.as_string())
            smtp.quit()
            
            logger.info(f"邮件发送成功，接收者: {self.recipients}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def push_report(self, report: Dict, html_content: str, text_content: str) -> bool:
        """
        推送汇总报告
        
        Args:
            report: 报告数据
            html_content: HTML格式内容
            text_content: 纯文本格式内容
            
        Returns:
            是否推送成功
        """
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        subject = self.subject_template.format(date=date)
        
        return self.send_email(subject, html_content, text_content)


def push_email(report: Dict, html_content: str, text_content: str, config: Dict) -> bool:
    """
    发送邮件推送
    
    Args:
        report: 报告数据
        html_content: HTML内容
        text_content: 纯文本内容
        config: 邮件配置
        
    Returns:
        是否成功
    """
    pusher = EmailPusher(config)
    return pusher.push_report(report, html_content, text_content)