#!/usr/bin/env python3
"""
GNU Mailman邮件列表爬取模块
支持Hyperkitty和Pipermail两种归档格式
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re
import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class MailmanCrawler:
    """GNU Mailman邮件列表爬虫"""
    
    def __init__(self, config: Dict):
        """
        初始化爬虫
        
        Args:
            config: 爬取配置字典
        """
        self.timeout = config.get('timeout', 30)
        self.delay = config.get('delay', 1)
        self.max_emails = config.get('max_emails_per_list', 50)
        self.use_proxy = config.get('use_proxy', False)
        self.proxy = config.get('proxy', '')
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if self.use_proxy and self.proxy:
            self.session.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        获取页面内容
        
        Args:
            url: 页面URL
            
        Returns:
            页面HTML内容，失败返回None
        """
        try:
            logger.info(f"正在获取页面: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            time.sleep(self.delay)  # 避免请求过快
            return response.text
        except requests.RequestException as e:
            logger.error(f"获取页面失败: {url}, 错误: {e}")
            return None
    
    def detect_archive_type(self, archive_url: str) -> str:
        """
        检测归档页面类型
        
        Args:
            archive_url: 归档页面URL
            
        Returns:
            归档类型: 'hyperkitty' 或 'pipermail'
        """
        if 'hyperkitty' in archive_url.lower():
            return 'hyperkitty'
        elif 'pipermail' in archive_url.lower():
            return 'pipermail'
        else:
            # 尝试访问页面判断
            html = self.fetch_page(archive_url)
            if html:
                if 'hyperkitty' in html.lower() or 'HyperKitty' in html:
                    return 'hyperkitty'
                elif 'pipermail' in html.lower():
                    return 'pipermail'
        return 'unknown'
    
    def get_emails_by_date_range(self, community: Dict, start_date: str, end_date: str, timezone: str = 'Asia/Shanghai') -> List[Dict]:
        """
        获取指定日期范围内的邮件列表
        
        Args:
            community: 社区配置字典
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            timezone: 时区
            
        Returns:
            邮件列表
        """
        emails = []
        archive_url = community.get('archive_url', '')
        list_names = community.get('lists', [])
        community_name = community.get('name', 'Unknown')
        
        if not archive_url:
            logger.warning(f"社区 {community_name} 未配置归档URL")
            return emails
        
        archive_type = self.detect_archive_type(archive_url)
        logger.info(f"社区 {community_name} 归档类型: {archive_type}")
        
        for list_name in list_names:
            try:
                list_emails = self._crawl_list_by_date_range(
                    archive_url, 
                    list_name, 
                    archive_type,
                    start_date,
                    end_date,
                    community_name
                )
                emails.extend(list_emails)
            except Exception as e:
                logger.error(f"爬取邮件列表 {list_name} 失败: {e}")
        
        return emails
    
    def get_yesterday_emails(self, community: Dict, timezone: str = 'Asia/Shanghai') -> List[Dict]:
        """
        获取前一天的邮件列表
        
        Args:
            community: 社区配置字典
            timezone: 时区
            
        Returns:
            邮件列表
        """
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        return self.get_emails_by_date_range(community, yesterday_str, yesterday_str, timezone)
    
    def _crawl_list_by_date_range(self, archive_url: str, list_name: str,
                                   archive_type: str, start_date: str, end_date: str,
                                   community_name: str) -> List[Dict]:
        """
        爬取单个邮件列表的日期范围
        
        Args:
            archive_url: 归档URL
            list_name: 邮件列表名称
            archive_type: 归档类型
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            community_name: 社区名称
            
        Returns:
            邮件列表
        """
        emails = []
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        current_dt = start_dt
        while current_dt <= end_dt:
            date_str = current_dt.strftime('%Y-%m-%d')
            
            if archive_type == 'hyperkitty':
                day_emails = self._crawl_hyperkitty(archive_url, list_name, date_str, community_name)
            elif archive_type == 'pipermail':
                day_emails = self._crawl_pipermail(archive_url, list_name, date_str, community_name)
            else:
                logger.warning(f"未知的归档类型: {archive_type}")
                break
            
            emails.extend(day_emails)
            current_dt += timedelta(days=1)
        
        return emails[:self.max_emails]
    
    def _crawl_list(self, archive_url: str, list_name: str, 
                    archive_type: str, date_str: str,
                    community_name: str) -> List[Dict]:
        """
        爬取单个邮件列表
        
        Args:
            archive_url: 归档URL
            list_name: 邮件列表名称
            archive_type: 归档类型
            date_str: 日期字符串
            community_name: 社区名称
            
        Returns:
            件列表
        """
        emails = []
        
        if archive_type == 'hyperkitty':
            emails = self._crawl_hyperkitty(archive_url, list_name, date_str, community_name)
        elif archive_type == 'pipermail':
            emails = self._crawl_pipermail(archive_url, list_name, date_str, community_name)
        else:
            logger.warning(f"未知的归档类型: {archive_type}")
        
        return emails[:self.max_emails]
    
    def _crawl_hyperkitty(self, archive_url: str, list_name: str,
                          date_str: str, community_name: str) -> List[Dict]:
        """
        爬取Hyperkitty归档
        
        Args:
            archive_url: 归档URL
            list_name: 件列表名称
            date_str: 日期字符串
            community_name: 社区名称
            
        Returns:
            件列表
        """
        emails = []
        
        # 构建邮件列表归档URL
        # Hyperkitty格式: https://example.com/hyperkitty/list/list_name@domain/
        list_url = urljoin(archive_url, f"list/{list_name}/")
        
        # 获取当天的邮件列表页面
        # Hyperkitty通常按日期组织: https://example.com/hyperkitty/list/list_name@domain/2024/1/
        year, month = date_str.split('-')[0], date_str.split('-')[1]
        date_url = urljoin(list_url, f"{year}/{month}/")
        
        html = self.fetch_page(date_url)
        if not html:
            # 尝试直接访问列表页面
            html = self.fetch_page(list_url)
        
        if not html:
            return emails
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找邮件链接
        # Hyperkitty邮件链接通常在表格或列表中
        email_links = soup.find_all('a', href=re.compile(r'/message/'))
        
        for link in email_links:
            email_url = urljoin(list_url, link.get('href'))
            email_info = self._parse_hyperkitty_email(email_url, list_name, community_name, date_str)
            if email_info:
                emails.append(email_info)
        
        return emails
    
    def _parse_hyperkitty_email(self, email_url: str, list_name: str,
                                 community_name: str, date_str: str) -> Optional[Dict]:
        """
        解析Hyperkitty单封邮件
        
        Args:
            email_url: 件URL
            list_name: 件列表名称
            community_name: 社区名称
            date_str: 日期字符串
            
        Returns:
            件信息字典
        """
        html = self.fetch_page(email_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取邮件信息
        email_info = {
            'community': community_name,
            'list': list_name,
            'url': email_url,
            'date': date_str
        }
        
        # 标题
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            email_info['subject'] = title_elem.get_text(strip=True)
        
        # 发件人
        author_elem = soup.find('span', class_='author') or soup.find('div', class_='from')
        if author_elem:
            email_info['author'] = author_elem.get_text(strip=True)
        
        # 发送时间
        date_elem = soup.find('span', class_='date') or soup.find('time')
        if date_elem:
            email_info['sent_time'] = date_elem.get_text(strip=True)
        
        # 正文内容（用于摘要）
        body_elem = soup.find('div', class_='message-body') or soup.find('div', class_='content')
        if body_elem:
            body_text = body_elem.get_text(strip=True)
            email_info['body'] = body_text
        
        return email_info
    
    def _crawl_pipermail(self, archive_url: str, list_name: str,
                         date_str: str, community_name: str) -> List[Dict]:
        """
        爬取Pipermail归档
        
        Args:
            archive_url: 归档URL
            list_name: 件列表名称
            date_str: 日期字符串
            community_name: 社区名称
            
        Returns:
            件列表
        """
        emails = []
        
        # Pipermail格式: https://example.com/pipermail/list_name/
        list_url = urljoin(archive_url, f"{list_name}/")
        
        # 获取当月归档
        year, month = date_str.split('-')[0], date_str.split('-')[1]
        month_name = datetime(int(year), int(month), 1).strftime('%B')
        archive_file = f"{year}-{month_name}.txt"
        archive_file_url = urljoin(list_url, archive_file)
        
        html = self.fetch_page(archive_file_url)
        if not html:
            # 尝试获取索引页面
            html = self.fetch_page(list_url)
            if html:
                # 从索引页面找到当月归档链接
                soup = BeautifulSoup(html, 'html.parser')
                archive_link = soup.find('a', href=re.compile(f"{year}-{month_name}"))
                if archive_link:
                    archive_file_url = urljoin(list_url, archive_link.get('href'))
                    html = self.fetch_page(archive_file_url)
        
        if not html:
            return emails
        
        # Pipermail mbox格式解析
        emails = self._parse_pipermail_mbox(html, list_name, community_name, date_str)
        
        return emails
    
    def _parse_pipermail_mbox(self, mbox_content: str, list_name: str,
                               community_name: str, date_str: str) -> List[Dict]:
        """
        解析Pipermail mbox格式
        
        Args:
            mbox_content: mbox内容
            list_name: 件列表名称
            community_name: 社区名称
            date_str: 日期字符串
            
        Returns:
            件列表
        """
        emails = []
        
        # mbox格式以 "From " 开头分隔每封邮件
        messages = re.split(r'^From .*?\n', mbox_content)
        
        for msg in messages:
            if not msg.strip():
                continue
            
            email_info = {
                'community': community_name,
                'list': list_name,
                'date': date_str
            }
            
            # 解析邮件头
            headers = {}
            header_lines = []
            body_lines = []
            in_headers = True
            
            for line in msg.split('\n'):
                if in_headers:
                    if line.strip() == '':
                        in_headers = False
                    else:
                        header_lines.append(line)
                else:
                    body_lines.append(line)
            
            # 解析头部字段
            for line in header_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            email_info['subject'] = headers.get('subject', '无标题')
            email_info['author'] = headers.get('from', '未知发件人')
            email_info['sent_time'] = headers.get('date', '')
            
            # 正文
            body_text = '\n'.join(body_lines).strip()
            email_info['body'] = body_text
            
            # 检查日期是否匹配
            if date_str in email_info.get('sent_time', '') or \
               self._check_date_in_body(body_text, date_str):
                emails.append(email_info)
        
        return emails
    
    def _check_date_in_body(self, body: str, date_str: str) -> bool:
        """
        检查日期是否在正文中出现
        
        Args:
            body: 正文内容
            date_str: 日期字符串
            
        Returns:
            是否匹配
        """
        # 简化日期匹配，检查多种格式
        date_formats = [
            date_str,
            date_str.replace('-', '/'),
            datetime.strptime(date_str, '%Y-%m-%d').strftime('%d %b %Y'),
        ]
        for fmt in date_formats:
            if fmt.lower() in body.lower():
                return True
        return False


def crawl_all_lists(config: Dict, start_date: str = None, end_date: str = None) -> List[Dict]:
    """
    爬取所有配置的邮件列表
    
    Args:
        config: 完整配置字典
        start_date: 开始日期 (YYYY-MM-DD)，如果不指定则抓取前一天
        end_date: 结束日期 (YYYY-MM-DD)，如果不指定则抓取前一天
        
    Returns:
        所有邮件列表
    """
    crawler = MailmanCrawler(config.get('crawler', {}))
    mailing_lists = config.get('mailing_lists', [])
    timezone = config.get('digest', {}).get('timezone', 'Asia/Shanghai')
    
    all_emails = []
    
    for community in mailing_lists:
        if start_date and end_date:
            emails = crawler.get_emails_by_date_range(community, start_date, end_date, timezone)
        else:
            emails = crawler.get_yesterday_emails(community, timezone)
        all_emails.extend(emails)
        logger.info(f"社区 {community.get('name')} 获取到 {len(emails)} 封邮件")
    
    return all_emails