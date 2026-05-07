#!/usr/bin/env python3
"""
飞书机器人推送模块
"""

import requests
from typing import Dict, List
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class FeishuPusher:
    """飞书机器人推送器"""
    
    def __init__(self, config: Dict):
        """
        初始化飞书推送器
        
        Args:
            config: 飞书推送配置
        """
        self.enabled = config.get('enabled', False)
        self.webhook_url = config.get('webhook_url', '')
        self.use_rich_text = config.get('use_rich_text', True)
        self.title_template = config.get('title_template', '每日邮件列表汇总 ({date})')
    
    def send_message(self, content: Dict) -> bool:
        """
        发送飞书消息
        
        Args:
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.info("飞书推送未启用")
            return False
        
        if not self.webhook_url:
            logger.warning("未配置飞书Webhook地址")
            return False
        
        try:
            payload = {
                "msg_type": "interactive",
                "card": content
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('StatusCode') == 0 or result.get('code') == 0:
                logger.info("飞书消息发送成功")
                return True
            else:
                logger.error(f"飞书消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False
    
    def build_card(self, report: Dict) -> Dict:
        """
        构建飞书消息卡片
        
        Args:
            report: 报告数据
            
        Returns:
            消息卡片内容
        """
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        title = self.title_template.format(date=date)
        
        # 构建卡片内容
        card = {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": []
        }
        
        # 添加统计信息
        stats_element = {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**总邮件数:** {report['total_emails']} 封\n**生成时间:** {report['generated_at']}"
            }
        }
        card['elements'].append(stats_element)
        
        # 添加分隔线
        card['elements'].append({"tag": "hr"})
        
        # 添加各社区详情
        for community, stats in report['communities'].items():
            community_element = {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{community}** ({stats['total_emails']} 封邮件)"
                }
            }
            card['elements'].append(community_element)
            
            # 添加邮件列表详情
            for list_name, list_info in stats['lists'].items():
                list_element = {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"  • {list_name}: {list_info['count']} 封"
                    }
                }
                card['elements'].append(list_element)
            
            # 添加分隔线
            card['elements'].append({"tag": "hr"})
        
        # 添加查看详情按钮（如果有HTML报告链接）
        # 这里可以添加一个链接到详细报告的按钮
        card['elements'].append({
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "查看详细报告"
                    },
                    "type": "primary",
                    "url": ""  # 可以配置一个报告查看链接
                }
            ]
        })
        
        return card
    
    def build_rich_text(self, report: Dict) -> Dict:
        """
        构建富文本消息
        
        Args:
            report: 报告数据
            
        Returns:
            富文本消息内容
        """
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        title = self.title_template.format(date=date)
        
        # 构建富文本内容
        content_lines = [
            f"**{title}**",
            "",
            f"总邮件数: **{report['total_emails']}** 封",
            f"生成时间: {report['generated_at']}",
            ""
        ]
        
        for community, stats in report['communities'].items():
            content_lines.append(f"---")
            content_lines.append(f"**{community}** ({stats['total_emails']} 封)")
            
            for list_name, list_info in stats['lists'].items():
                content_lines.append(f"  • {list_name}: {list_info['count']} 封")
                
                # 显示前3封邮件的标题
                for i, email in enumerate(list_info['emails'][:3]):
                    subject = email.get('subject', '无标题')
                    url = email.get('url', '')
                    if url:
                        content_lines.append(f"    - [{subject}]({url})")
                    else:
                        content_lines.append(f"    - {subject}")
                
                if len(list_info['emails']) > 3:
                    content_lines.append(f"    - ... 还有 {len(list_info['emails']) - 3} 封邮件")
        
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("详细报告请查看邮件或附件")
        
        return {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": '\n'.join(content_lines)
                    }
                }
            ]
        }
    
    def push_report(self, report: Dict) -> bool:
        """
        推送汇总报告
        
        Args:
            report: 报告数据
            
        Returns:
            是否推送成功
        """
        if self.use_rich_text:
            card = self.build_rich_text(report)
        else:
            card = self.build_card(report)
        
        return self.send_message(card)


def push_feishu(report: Dict, config: Dict) -> bool:
    """
    发送飞书推送
    
    Args:
        report: 报告数据
        config: 飞书配置
        
    Returns:
        是否成功
    """
    pusher = FeishuPusher(config)
    return pusher.push_report(report)