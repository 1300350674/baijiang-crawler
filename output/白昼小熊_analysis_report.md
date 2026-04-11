# B站UP主"白昼小熊"数据分析报告

> 生成时间: 2026-04-11

## 📊 数据概览

| 指标 | 数值 |
|:---|---:|
| 总视频数 | 待获取 |
| 总播放量 | 待获取 |
| 总获赞数 | 待获取 |
| 总弹幕数 | 待获取 |
| 总评论数 | 待获取 |

> ⚠️ **注意**: 当前从服务器环境无法直接访问B站API（B站有严格的风控机制），需要在你本地运行代码才能获取真实数据。

---

## 🚀 本地运行指南

### 环境要求
- Python 3.8+
- 需要稳定的网络环境（建议使用代理）

### 安装依赖
```bash
cd baijiang-crawler
pip install -r requirements.txt
```

### 运行爬虫
```bash
# 方式1: 使用UP主名称搜索
python main.py --up-name "白昼小熊"

# 方式2: 直接指定UP主ID（推荐，更稳定）
python main.py --up-id 19523724
```

### 输出文件
- `output/data/videos.json` - 视频数据
- `output/data/comments.json` - 评论数据
- `output/白昼小熊_analysis_report.md` - 分析报告

---

## 📁 项目结构

```
baijiang-crawler/
├── bilibili_crawler.py  # 爬虫核心
├── analyzer.py          # 数据分析模块
├── main.py             # 主入口
├── config.py           # 配置
├── requirements.txt    # 依赖
└── output/             # 输出目录
    └── data/
```

---

## 🔧 代码功能说明

1. **视频数据爬取**: 获取UP主所有视频的播放量、点赞、投币、收藏、弹幕数
2. **评论爬取**: 爬取热门评论，支持多页
3. **弹幕分析**: 获取视频弹幕数据
4. **报告生成**: 
   - 热门视频TOP5
   - 评论情感分析
   - 弹幕/评论词频统计
   - 数据可视化图表

---

*本报告由 OpenClaw AI 生成*
