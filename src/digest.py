#!/usr/bin/env python3
"""
邮件摘要生成模块
"""

from typing import List, Dict
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class DigestGenerator:
    """邮件摘要生成器"""
    
    def __init__(self, config: Dict):
        """
        初始化摘要生成器
        
        Args:
            config: 汇总配置字典
        """
        self.summary_length = config.get('summary_length', 200)
        self.group_by_community = config.get('group_by_community', True)
        self.timezone = config.get('timezone', 'Asia/Shanghai')
    
    def generate_summary(self, body: str) -> str:
        """
        生成邮件摘要
        
        Args:
            body: 件正文
            
        Returns:
            摘要文本
        """
        if not body:
            return "（无正文内容）"
        
        # 清理正文
        cleaned_body = self._clean_body(body)
        
        # 截取摘要
        if len(cleaned_body) <= self.summary_length:
            return cleaned_body
        
        # 在截取长度内找到最后一个完整句子
        truncated = cleaned_body[:self.summary_length]
        
        # 尝试在最后一个句号、问号或感叹号处截断
        last_sentence_end = max(
            truncated.rfind('.'),
            truncated.rfind('?'),
            truncated.rfind('!'),
            truncated.rfind('。'),
            truncated.rfind('？'),
            truncated.rfind('！')
        )
        
        if last_sentence_end > self.summary_length * 0.5:
            return truncated[:last_sentence_end + 1] + "..."
        else:
            return truncated + "..."
    
    def _clean_body(self, body: str) -> str:
        """
        清理邮件正文
        
        Args:
            body: 原始正文
            
        Returns:
            清理后的正文
        """
        # 移除HTML标签
        body = re.sub(r'<[^>]+>', '', body)
        
        # 移除多余的空白字符
        body = re.sub(r'\s+', ' ', body)
        
        # 移除邮件签名等常见噪音
        patterns_to_remove = [
            r'--\s*$',  # 签名分隔符
            r'^\s*_{5,}',  # 下划线分隔符
            r'^\s*From:.*$',  # 引用邮件头
            r'^\s*>.*$',  # 引用内容（可选保留）
            r'^\s*Sent from my.*$',  # 移动端签名
        ]
        
        for pattern in patterns_to_remove:
            body = re.sub(pattern, '', body, flags=re.MULTILINE)
        
        return body.strip()
    
    def group_emails(self, emails: List[Dict]) -> Dict:
        """
        按社区分组邮件
        
        Args:
            emails: 件列表
            
        Returns:
            分组后的邮件字典
        """
        grouped = {}
        
        for email in emails:
            community = email.get('community', 'Unknown')
            list_name = email.get('list', 'Unknown')
            
            if community not in grouped:
                grouped[community] = {}
            
            if list_name not in grouped[community]:
                grouped[community][list_name] = []
            
            # 为每封邮件生成摘要
            email['summary'] = self.generate_summary(email.get('body', ''))
            grouped[community][list_name].append(email)
        
        return grouped
    
    def generate_report(self, emails: List[Dict], date: str) -> Dict:
        """
        生成完整的汇总报告
        
        Args:
            emails: 件列表
            date: 日期字符串
            
        Returns:
            报告数据字典
        """
        report = {
            'date': date,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timezone': self.timezone,
            'total_emails': len(emails),
            'communities': {}
        }
        
        # 按社区分组
        grouped = self.group_emails(emails)
        
        for community, lists in grouped.items():
            community_stats = {
                'total_emails': sum(len(emails) for emails in lists.values()),
                'lists': {}
            }
            
            for list_name, list_emails in lists.items():
                community_stats['lists'][list_name] = {
                    'count': len(list_emails),
                    'emails': list_emails
                }
            
            report['communities'][community] = community_stats
        
        return report
    
    def format_report_text(self, report: Dict) -> str:
        """
        格式化报告为纯文本
        
        Args:
            report: 报告数据
            
        Returns:
            格式化的文本
        """
        lines = []
        
        # 标题
        lines.append("=" * 60)
        lines.append(f"邮件列表每日汇总 - {report['date']}")
        lines.append("=" * 60)
        lines.append(f"生成时间: {report['generated_at']} ({report['timezone']})")
        lines.append(f"总邮件数: {report['total_emails']}")
        lines.append("")
        
        # 各社区详情
        for community, stats in report['communities'].items():
            lines.append("-" * 40)
            lines.append(f"【{community}】 - 共 {stats['total_emails']} 封邮件")
            lines.append("-" * 40)
            
            for list_name, list_info in stats['lists'].items():
                lines.append(f"\n邮件列表: {list_name} ({list_info['count']} 封)")
                lines.append("")
                
                for i, email in enumerate(list_info['emails'], 1):
                    lines.append(f"  {i}. {email.get('subject', '无标题')}")
                    lines.append(f"     发件人: {email.get('author', '未知')}")
                    lines.append(f"     时间: {email.get('sent_time', '未知')}")
                    lines.append(f"     摘要: {email.get('summary', '')}")
                    lines.append(f"     链接: {email.get('url', '无链接')}")
                    lines.append("")
        
        lines.append("=" * 60)
        lines.append("报告结束")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def format_report_html(self, report: Dict) -> str:
        """
        格式化报告为HTML
        
        Args:
            report: 报告数据
            
        Returns:
            格式化的HTML
        """
        html_parts = []
        
        # HTML头部
        html_parts.append("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮件列表每日汇总</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        h3 {
            color: #2980b9;
        }
        .meta-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .community-section {
            margin-bottom: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        .email-item {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .email-subject {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .email-meta {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .email-summary {
            margin-top: 10px;
            color: #555;
        }
        .email-link {
            color: #3498db;
            text-decoration: none;
        }
        .email-link:hover {
            text-decoration: underline;
        }
        .stats {
            color: #27ae60;
            font-weight: bold;
        }
    </style>
</head>
<body>
""")
        
        # 标题
        html_parts.append(f"""
    <h1>邮件列表每日汇总</h1>
    <div class="meta-info">
        <p><strong>日期:</strong> {report['date']}</p>
        <p><strong>生成时间:</strong> {report['generated_at']} ({report['timezone']})</p>
        <p><strong>总邮件数:</strong> <span class="stats">{report['total_emails']}</span> 封</p>
    </div>
""")
        
        # 各社区详情
        for community, stats in report['communities'].items():
            html_parts.append(f"""
    <div class="community-section">
        <h2>{community}</h2>
        <p>共 <span class="stats">{stats['total_emails']}</span> 封邮件</p>
""")
            
            for list_name, list_info in stats['lists'].items():
                html_parts.append(f"""
        <h3>{list_name} ({list_info['count']} 封)</h3>
""")
                
                for email in list_info['emails']:
                    html_parts.append(f"""
        <div class="email-item">
            <div class="email-subject">{email.get('subject', '无标题')}</div>
            <div class="email-meta">
                发件人: {email.get('author', '未知')} | 
                时间: {email.get('sent_time', '未知')}
            </div>
            <div class="email-summary">{email.get('summary', '')}</div>
            <div>
                <a class="email-link" href="{email.get('url', '#')}" target="_blank">查看完整邮件</a>
            </div>
        </div>
""")
            
            html_parts.append("    </div>")
        
        # HTML尾部
        html_parts.append("""
</body>
</html>
""")
        
        return '\n'.join(html_parts)
    
    def format_report_markdown(self, report: Dict) -> str:
        """
        格式化报告为Markdown
        
        Args:
            report: 报告数据
            
        Returns:
            格式化的Markdown
        """
        md_parts = []
        
        # 标题
        md_parts.append(f"# 邮件列表每日汇总 - {report['date']}")
        md_parts.append("")
        md_parts.append(f"> 生成时间: {report['generated_at']} ({report['timezone']})")
        md_parts.append(f"> 总邮件数: **{report['total_emails']}** 封")
        md_parts.append("")
        
        # 各社区详情
        for community, stats in report['communities'].items():
            md_parts.append(f"## {community}")
            md_parts.append(f"共 **{stats['total_emails']}** 封邮件")
            md_parts.append("")
            
            for list_name, list_info in stats['lists'].items():
                md_parts.append(f"### {list_name} ({list_info['count']} 封)")
                md_parts.append("")
                
                for email in list_info['emails']:
                    md_parts.append(f"#### {email.get('subject', '无标题')}")
                    md_parts.append(f"- **发件人:** {email.get('author', '未知')}")
                    md_parts.append(f"- **时间:** {email.get('sent_time', '未知')}")
                    md_parts.append(f"- **摘要:** {email.get('summary', '')}")
                    md_parts.append(f"- **链接:** [{email.get('url', '无链接')}]({email.get('url', '#')})")
                    md_parts.append("")
        
        return '\n'.join(md_parts)


def generate_digest(emails: List[Dict], config: Dict, date: str) -> Dict:
    """
    生成邮件摘要报告
    
    Args:
        emails: 件列表
        config: 汇总配置
        date: 日期
        
    Returns:
        报告数据
    """
    generator = DigestGenerator(config)
    return generator.generate_report(emails, date)