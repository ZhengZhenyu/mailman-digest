#!/usr/bin/env python3
"""
邮件列表每日汇总工具主程序
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict
import argparse

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler import crawl_all_lists
from digest import generate_digest, DigestGenerator
from push_email import push_email
from push_feishu import push_feishu
from config_manager import ConfigManager, ProcessedEmailsManager


def setup_logging(config: Dict) -> logging.Logger:
    """
    设置日志
    
    Args:
        config: 日志配置
        
    Returns:
        Logger实例
    """
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', '/app/logs/mailman-digest.log')
    
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def run_digest_task(config: Dict) -> Dict:
    """
    执行汇总任务
    
    Args:
        config: 完整配置
        
    Returns:
        报告数据
    """
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("开始执行邮件列表汇总任务")
    logger.info("=" * 50)
    
    # 获取前一天的日期
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    logger.info(f"汇总日期: {yesterday_str}")
    
    # 爬取邮件列表
    logger.info("开始爬取邮件列表...")
    emails = crawl_all_lists(config)
    logger.info(f"爬取完成，共获取 {len(emails)} 封邮件")
    
    # 过滤已处理的邮件
    storage_config = config.get('storage', {})
    processed_file = storage_config.get('processed_file', '/app/data/processed_emails.json')
    processed_manager = ProcessedEmailsManager(processed_file)
    
    new_emails = processed_manager.filter_new_emails(emails)
    logger.info(f"过滤后新邮件: {len(new_emails)} 封")
    
    if not new_emails:
        logger.info("没有新邮件需要处理")
        return None
    
    # 生成摘要报告
    logger.info("开始生成摘要报告...")
    digest_config = config.get('digest', {})
    report = generate_digest(new_emails, digest_config, yesterday_str)
    
    # 格式化报告
    generator = DigestGenerator(digest_config)
    html_content = generator.format_report_html(report)
    text_content = generator.format_report_text(report)
    markdown_content = generator.format_report_markdown(report)
    
    # 保存报告到文件
    output_dir = storage_config.get('output_dir', '/app/output')
    os.makedirs(output_dir, exist_ok=True)
    
    report_file_html = os.path.join(output_dir, f"digest_{yesterday_str}.html")
    report_file_md = os.path.join(output_dir, f"digest_{yesterday_str}.md")
    
    with open(report_file_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"HTML报告已保存: {report_file_html}")
    
    with open(report_file_md, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info(f"Markdown报告已保存: {report_file_md}")
    
    # 推送报告
    push_config = config.get('push', {})
    
    # 邮件推送
    email_config = push_config.get('email', {})
    if email_config.get('enabled', False):
        logger.info("开始邮件推送...")
        success = push_email(report, html_content, text_content, email_config)
        if success:
            logger.info("邮件推送成功")
        else:
            logger.warning("邮件推送失败")
    
    # 飞书推送
    feishu_config = push_config.get('feishu', {})
    if feishu_config.get('enabled', False):
        logger.info("开始飞书推送...")
        success = push_feishu(report, feishu_config)
        if success:
            logger.info("飞书推送成功")
        else:
            logger.warning("飞书推送失败")
    
    # 标记邮件为已处理
    for email in new_emails:
        email_url = email.get('url', '')
        if email_url:
            processed_manager.mark_processed(email_url, {
                'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'subject': email.get('subject', ''),
                'community': email.get('community', ''),
                'list': email.get('list', '')
            })
    
    processed_manager.save_processed_emails()
    logger.info("已处理邮件记录已保存")
    
    # 清理旧记录
    processed_manager.cleanup_old_records(days=30)
    
    logger.info("=" * 50)
    logger.info("邮件列表汇总任务完成")
    logger.info("=" * 50)
    
    return report


def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='邮件列表每日汇总工具')
    parser.add_argument('-c', '--config', 
                        default='/app/config/config.yaml',
                        help='配置文件路径')
    parser.add_argument('--run-now', 
                        action='store_true',
                        help='立即执行一次汇总任务')
    args = parser.parse_args()
    
    # 加载配置
    config_manager = ConfigManager(args.config)
    config = config_manager.get_config()
    
    if not config:
        print(f"配置文件加载失败: {args.config}")
        sys.exit(1)
    
    # 设置日志
    logger = setup_logging(config)
    
    # 检查是否立即执行
    schedule_config = config.get('schedule', {})
    run_on_start = schedule_config.get('run_on_start', False)
    
    if args.run_now or run_on_start:
        run_digest_task(config)
        return
    
    # 启动定时任务调度器
    from scheduler import start_scheduler
    start_scheduler(config, run_digest_task)


if __name__ == '__main__':
    main()