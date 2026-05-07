# Mailman邮件列表每日汇总工具

一个自动化的邮件列表汇总工具，支持从GNU Mailman邮件列表归档页面爬取邮件，生成每日汇总报告，并通过邮件和飞书推送。

## 功能特性

- ✅ 支持GNU Mailman邮件列表（Hyperkitty和Pipermail归档格式）
- ✅ 自动爬取前一天的邮件内容
- ✅ 生成邮件摘要（标题+摘要）
- ✅ 按社区和邮件列表分组汇总
- ✅ 支持邮件推送（SMTP）
- ✅ 支持飞书机器人推送
- ✅ Docker容器化部署
- ✅ 定时任务调度（每天早上9:00）
- ✅ 已处理邮件记录，避免重复推送
- ✅ 多种报告格式（HTML、Markdown、纯文本）

## 目录结构

```
mailman-digest/
├── config/
│   └── config.yaml          # 配置文件
├── src/
│   ├── __init__.py
│   ├── main.py              # 主程序
│   ├── crawler.py           # 邮件列表爬取模块
│   ├── digest.py            # 摘要生成模块
│   ├── push_email.py        # 邮件推送模块
│   ├── push_feishu.py       # 飞书推送模块
│   ├── config_manager.py    # 配置管理模块
│   └── scheduler.py         # 定时任务调度模块
├── Dockerfile               # Docker镜像构建文件
├── docker-compose.yml       # Docker Compose配置
├── requirements.txt         # Python依赖
└── README.md                # 使用文档
```

## 快速开始

### 1. 配置文件设置

编辑 `config/config.yaml` 文件，配置你的邮件列表和推送渠道：

```yaml
# 邮件列表配置
mailing_lists:
  - name: "openEuler社区"
    archive_url: "https://mail.openeuler.org/hyperkitty/"
    lists:
      - "dev@openeuler.org"
      - "community@openeuler.org"

# 推送配置
push:
  email:
    enabled: true
    smtp_server: "smtp.example.com"
    smtp_port: 465
    smtp_user: "your_email@example.com"
    smtp_password: "your_password"
    recipients:
      - "your_email@example.com"
  
  feishu:
    enabled: true
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx"

# 定时任务配置
schedule:
  cron: "0 9 * * *"  # 每天早上9:00
  timezone: "Asia/Shanghai"
```

### 2. Docker部署

**构建镜像**
```bash
docker build -t mailman-digest:latest .
```

**启动容器**
```bash
docker-compose up -d
```

**查看日志**
```bash
docker logs -f mailman-digest
```

### 3. 手动运行

**立即执行一次汇总**
```bash
docker exec mailman-digest python src/main.py --run-now
```

**或直接运行**
```bash
python src/main.py --run-now -c config/config.yaml
```

## 配置说明

### 邮件列表配置

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 社区名称 | "openEuler社区" |
| `archive_url` | 归档页面URL | "https://mail.openeuler.org/hyperkitty/" |
| `lists` | 邮件列表地址列表 | ["dev@openeuler.org"] |

### 爬取配置

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `max_emails_per_list` | 每个列表最大邮件数 | 50 |
| `timeout` | 请求超时时间（秒） | 30 |
| `delay` | 请求间隔（秒） | 1 |
| `use_proxy` | 是否使用代理 | false |

### 汇总配置

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `summary_length` | 摘要截取长度 | 200 |
| `group_by_community` | 按社区分组 | true |
| `timezone` | 时区 | Asia/Shanghai |

### 邮件推送配置

| 字段 | 说明 |
|------|------|
| `smtp_server` | SMTP服务器地址 |
| `smtp_port` | SMTP端口（SSL通常为465） |
| `smtp_user` | SMTP用户名 |
| `smtp_password` | SMTP密码 |
| `smtp_use_ssl` | 是否使用SSL |
| `from` | 发送者邮箱 |
| `recipients` | 接收者邮箱列表 |

### 飞书推送配置

| 字段 | 说明 |
|------|------|
| `webhook_url` | 飞书机器人Webhook地址 |
| `use_rich_text` | 是否使用富文本消息 |

**获取飞书Webhook地址：**
1. 在飞书群组中添加"自定义机器人"
2. 获取Webhook地址
3. 将地址填入配置文件

### 定时任务配置

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `cron` | Cron表达式 | "0 9 * * *" |
| `timezone` | 时区 | Asia/Shanghai |
| `run_on_start` | 启动时立即执行 | false |

**Cron表达式格式：**
```
分钟 小时 日 月 星期
0    9    *  *  *    # 每天早上9:00
30   8    *  *  1-5  # 工作日早上8:30
```

## 输出文件

工具会在 `output/` 目录生成以下文件：

- `digest_YYYY-MM-DD.html` - HTML格式汇总报告
- `digest_YYYY-MM-DD.md` - Markdown格式汇总报告

## 日志文件

日志文件位于 `logs/` 目录：
- `mailman-digest.log` - 主日志文件

## 数据文件

数据文件位于 `data/` 目录：
- `processed_emails.json` - 已处理邮件记录

## 常见问题

### 1. 邮件列表爬取失败

**检查项：**
- 归档URL是否正确
- 邮件列表名称是否正确
- 网络连接是否正常
- 是否需要代理

### 2. 邮件推送失败

**检查项：**
- SMTP服务器地址和端口是否正确
- SMTP用户名和密码是否正确
- 是否启用了SSL
- 接收者邮箱地址是否正确

### 3. 飞书推送失败

**检查项：**
- Webhook地址是否正确
- 机器人是否被禁用
- 消息格式是否正确

### 4. 容器启动失败

**检查项：**
- 配置文件是否存在
- 配置文件格式是否正确
- 目录权限是否正确

## 进阶配置

### 使用环境变量覆盖配置

可以通过环境变量覆盖配置文件中的部分设置：

```yaml
environment:
  - SMTP_SERVER=smtp.example.com
  - SMTP_PORT=465
  - SMTP_USER=your_email@example.com
  - SMTP_PASSWORD=your_password
  - FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
```

### 自定义报告模板

可以修改 `src/digest.py` 中的模板函数来自定义报告格式。

### 添加更多推送渠道

可以在 `src/` 目录添加新的推送模块，如钉钉、Slack等。

## 维护说明

### 清理旧数据

工具会自动清理30天前的已处理邮件记录。

### 更新邮件列表

编辑配置文件添加或删除邮件列表，重启容器生效。

### 升级工具

```bash
docker-compose down
docker build -t mailman-digest:latest .
docker-compose up -d
```

## 技术栈

- Python 3.11
- requests - HTTP请求
- BeautifulSoup4 - HTML解析
- APScheduler - 定时任务调度
- PyYAML - 配置文件解析

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或Pull Request。