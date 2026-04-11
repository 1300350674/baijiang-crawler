"""
数据分析与报告生成模块
"""
import json
import re
import os
from collections import Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    total_videos: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_danmu: int = 0
    total_comments: int = 0
    avg_views: float = 0
    avg_likes: float = 0
    avg_danmu: float = 0
    top5_videos: List[Dict] = field(default_factory=list)
    video_duration_stats: Dict = field(default_factory=dict)
    comment_stats: Dict = field(default_factory=dict)
    sentiment_stats: Dict = field(default_factory=dict)
    word_freq: List[Tuple[str, int]] = field(default_factory=list)
    avg_comment_likes: float = 0
    hot_comments: List[Dict] = field(default_factory=list)


class DataAnalyzer:
    def __init__(self):
        self.stopwords = set([
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '他', '她', '它', '吗', '吧', '啊', '呢', '哦', '嗯', '哈',
            '哈哈', '哈哈哈', '233', 'ww', 'emm', 'bilibili', 'b站', 'BV', 'http', 'www',
            'com', 'video', 'av', 'cid', '的', '了', '我', '你', '他', '她', '它', '们',
            '这', '那', '这个', '那个', '什么', '怎么', '如何', '为什么', '哪', '哪个',
        ])
    
    def load_data(self, data_dir: str) -> Dict:
        videos_data = {}
        comments_data = {}
        danmu_data = {}
        
        videos_path = os.path.join(data_dir, 'videos.json')
        comments_path = os.path.join(data_dir, 'comments.json')
        danmu_path = os.path.join(data_dir, 'danmu.json')
        
        if os.path.exists(videos_path):
            with open(videos_path, 'r', encoding='utf-8') as f:
                videos_data = json.load(f)
        
        if os.path.exists(comments_path):
            with open(comments_path, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
        
        if os.path.exists(danmu_path):
            with open(danmu_path, 'r', encoding='utf-8') as f:
                danmu_data = json.load(f)
        
        return {
            'videos': videos_data.get('videos', []),
            'comments': comments_data.get('by_video', {}),
            'danmu': danmu_data.get('by_video', {})
        }
    
    def analyze_videos(self, videos: List[Dict]) -> Tuple[Dict, List[Dict]]:
        if not videos:
            return {}, []
        
        total_views = sum(v.get('view', 0) for v in videos)
        total_likes = sum(v.get('like', 0) for v in videos)
        total_danmu = sum(v.get('danmu', 0) for v in videos)
        
        stats = {
            'total_videos': len(videos),
            'total_views': total_views,
            'total_likes': total_likes,
            'total_danmu': total_danmu,
            'avg_views': total_views / len(videos) if videos else 0,
            'avg_likes': total_likes / len(videos) if videos else 0,
            'avg_danmu': total_danmu / len(videos) if videos else 0,
        }
        
        sorted_videos = sorted(videos, key=lambda x: x.get('view', 0), reverse=True)
        top5 = sorted_videos[:5]
        top5_info = []
        for v in top5:
            top5_info.append({
                'title': v.get('title', ''),
                'bvid': v.get('bvid', ''),
                'url': v.get('url', ''),
                'views': v.get('view', 0),
                'likes': v.get('like', 0),
                'danmu': v.get('danmu', 0),
                'pubdate': v.get('pubdate', ''),
            })
        
        return stats, top5_info
    
    def analyze_comments(self, comments: Dict[str, List]) -> Tuple[Dict, List[Dict]]:
        all_comments = []
        for bv_comments in comments.values():
            all_comments.extend(bv_comments)
        
        if not all_comments:
            return {'total_comments': 0, 'avg_likes': 0}, []
        
        total_likes = sum(c.get('like', 0) for c in all_comments)
        comment_stats = {
            'total_comments': len(all_comments),
            'avg_likes': total_likes / len(all_comments) if all_comments else 0,
        }
        
        sorted_comments = sorted(all_comments, key=lambda x: x.get('like', 0), reverse=True)
        hot_comments = []
        for c in sorted_comments[:20]:
            hot_comments.append({
                'uname': c.get('uname', ''),
                'content': c.get('content', ''),
                'like': c.get('like', 0),
                'ctime': c.get('ctime', ''),
            })
        
        return comment_stats, hot_comments
    
    def simple_sentiment(self, text: str) -> str:
        positive_words = [
            '牛', '厉害', '喜欢', '支持', '可爱', '漂亮', '好', '棒', '赞', '优秀',
            '太强', '爱了', '绝了', '顶', '冲', '加油', '太棒', '牛逼', '神', '顶',
            '哈哈哈', '笑死', '绝了', '哇', '优秀', '帅', '美', '甜', '暖', '感动',
            '治愈', '神仙', '顶流', '封神', '炸裂', '完美', '满分', '吹爆', '磕',
        ]
        negative_words = [
            '烂', '差', '垃圾', '难看', '失望', '无聊', '尴尬', '抄袭', '恶心',
            '无语', '退钱', '翻车', '崩', '糊', '凉', '尬', '假', '装', '恶臭',
        ]
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def analyze_sentiment(self, comments: Dict[str, List]) -> Dict:
        all_comments = []
        for bv_comments in comments.values():
            all_comments.extend(bv_comments)
        
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for c in all_comments:
            content = c.get('content', '')
            sentiment = self.simple_sentiment(content)
            sentiment_counts[sentiment] += 1
        
        total = len(all_comments) if all_comments else 1
        sentiment_percent = {
            k: round(v / total * 100, 2) for k, v in sentiment_counts.items()
        }
        
        return {
            'counts': sentiment_counts,
            'percentages': sentiment_percent
        }
    
    def extract_words(self, text: str) -> List[str]:
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
        words = [w for w in text.split() if len(w) >= 2 and w.lower() not in self.stopwords]
        return words
    
    def analyze_word_freq(self, comments: Dict[str, List], danmu: Dict[str, List]) -> List[Tuple[str, int]]:
        all_text = []
        
        for bv_comments in comments.values():
            for c in bv_comments:
                content = c.get('content', '')
                if content:
                    all_text.append(content)
        
        for bv_danmu in danmu.values():
            all_text.extend(bv_danmu)
        
        all_words = []
        for text in all_text:
            all_words.extend(self.extract_words(text))
        
        word_freq = Counter(all_words)
        return word_freq.most_common(100)
    
    def generate_report(self, up_name: str, up_info: Dict, analysis: AnalysisResult, 
                       output_path: str, data_timestamp: str = ''):
        report = f"""# {up_name} 视频数据分析报告

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 数据采集时间: {data_timestamp or 'N/A'}

---

## 一、数据概览

| 指标 | 数值 |
|:---:|:---:|
| 视频总数 | {analysis.total_videos} |
| 总播放量 | {self._format_num(analysis.total_views)} |
| 总点赞数 | {self._format_num(analysis.total_likes)} |
| 总弹幕数 | {self._format_num(analysis.total_danmu)} |
| 总评论数 | {self._format_num(analysis.total_comments)} |
| 平均播放量 | {self._format_num(int(analysis.avg_views))} |
| 平均点赞数 | {self._format_num(int(analysis.avg_likes))} |
| 平均弹幕数 | {self._format_num(int(analysis.avg_danmu))} |

---

## 二、Up主信息

| 属性 | 内容 |
|:---:|:---:|
| Up主名称 | {up_info.get('card', {}).get('uname', up_name)} |
| Mid | {up_info.get('card', {}).get('mid', 'N/A')} |
| 粉丝数 | {self._format_num(up_info.get('card', {}).get('fans', 0))} |
| 关注数 | {self._format_num(up_info.get('card', {}).get('friend', 0))} |
| 获赞数 | {self._format_num(up_info.get('card', {}).get('likes', 0))} |
| 等级 | Lv.{up_info.get('card', {}).get('level_info', {}).get('current_level', 'N/A')} |

---

## 三、最热门视频 TOP 5（按播放量）

"""
        
        for i, v in enumerate(analysis.top5_videos, 1):
            report += f"""### {i}. {v['title']}

- **BV号**: `{v['bvid']}`
- **播放量**: {self._format_num(v['views'])}
- **点赞数**: {self._format_num(v['likes'])}
- **弹幕数**: {self._format_num(v['danmu'])}
- **发布时间**: {v['pubdate']}
- **链接**: {v['url']}

"""
        
        report += f"""---

## 四、评论分析

### 4.1 评论概况

| 指标 | 数值 |
|:---:|:---:|
| 总评论数 | {analysis.total_comments} |
| 平均点赞 | {self._format_num(int(analysis.avg_comment_likes))} |

### 4.2 情感分析

| 情感类型 | 数量 | 占比 |
|:---:|:---:|:---:|
| 正面 | {analysis.sentiment_stats.get('counts', {}).get('positive', 0)} | {analysis.sentiment_stats.get('percentages', {}).get('positive', 0)}% |
| 中性 | {analysis.sentiment_stats.get('counts', {}).get('neutral', 0)} | {analysis.sentiment_stats.get('percentages', {}).get('neutral', 0)}% |
| 负面 | {analysis.sentiment_stats.get('counts', {}).get('negative', 0)} | {analysis.sentiment_stats.get('percentages', {}).get('negative', 0)}% |

### 4.3 热门评论 TOP 10

"""
        
        for i, c in enumerate(analysis.hot_comments[:10], 1):
            content = c['content'][:100] + ('...' if len(c['content']) > 100 else '')
            report += f"""**{i}. @{c['uname']}** ({c['like']}赞 · {c['ctime']})
> {content}

"""
        
        report += f"""---

## 五、弹幕/评论高频词 TOP 50

> 以下数据来自视频弹幕和评论区

| 排名 | 词语 | 频次 |
|:---:|:---:|:---:|
"""
        
        for i, (word, freq) in enumerate(analysis.word_freq[:50], 1):
            report += f"| {i} | {word} | {freq} |\n"
        
        report += """

---

## 六、数据说明

1. **数据来源**: B站公开API和页面数据
2. **数据完整性**: 受限于API访问频率，部分数据可能不完整
3. **情感分析**: 基于关键词匹配的情感分类，准确度有限
4. **统计周期**: 包含Up主所有历史视频数据

---

## 七、附录：完整视频数据

| 序号 | 标题 | 播放 | 点赞 | 弹幕 | 发布时间 |
|:---:|:---|:---:|:---:|:---:|:---:|
"""
        
        for i, v in enumerate(analysis.all_videos[:30], 1):
            title = v.get('title', '')[:20] + ('...' if len(v.get('title', '')) > 20 else '')
            report += f"| {i} | {title} | {self._format_num(v.get('view', 0))} | {self._format_num(v.get('like', 0))} | {self._format_num(v.get('danmu', 0))} | {v.get('pubdate', '')} |\n"
        
        if len(analysis.all_videos) > 30:
            report += f"\n*（共{len(analysis.all_videos)}个视频，仅展示前30个）*\n"
        
        report += f"""

---

*本报告由自动爬虫生成 | 仅供参考学习*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report
    
    @staticmethod
    def _format_num(num: int) -> str:
        if num >= 100000000:
            return f"{num / 100000000:.1f}亿"
        elif num >= 10000:
            return f"{num / 10000:.1f}万"
        return str(num)


class ReportGenerator:
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.analyzer = DataAnalyzer()
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(self, up_name: str, up_info: Dict = None) -> str:
        data = self.analyzer.load_data(self.data_dir)
        
        videos = data.get('videos', [])
        comments = data.get('comments', {})
        danmu = data.get('danmu', {})
        
        video_stats, top5 = self.analyzer.analyze_videos(videos)
        comment_stats, hot_comments = self.analyzer.analyze_comments(comments)
        sentiment = self.analyzer.analyze_sentiment(comments)
        word_freq = self.analyzer.analyze_word_freq(comments, danmu)
        
        timestamp = ''
        if videos:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        result = AnalysisResult(
            total_videos=video_stats.get('total_videos', 0),
            total_views=video_stats.get('total_views', 0),
            total_likes=video_stats.get('total_likes', 0),
            total_danmu=video_stats.get('total_danmu', 0),
            total_comments=comment_stats.get('total_comments', 0),
            avg_views=video_stats.get('avg_views', 0),
            avg_likes=video_stats.get('avg_likes', 0),
            avg_danmu=video_stats.get('avg_danmu', 0),
            top5_videos=top5,
            comment_stats=comment_stats,
            sentiment_stats=sentiment,
            word_freq=word_freq,
            hot_comments=hot_comments,
            avg_comment_likes=comment_stats.get('avg_likes', 0),
            all_videos=videos,
        )
        
        output_path = os.path.join(self.output_dir, f'{up_name}_analysis_report.md')
        
        report = self.analyzer.generate_report(
            up_name=up_name,
            up_info=up_info or {},
            analysis=result,
            output_path=output_path,
            data_timestamp=timestamp
        )
        
        json_output = os.path.join(self.output_dir, f'{up_name}_analysis_data.json')
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump({
                'video_stats': video_stats,
                'comment_stats': comment_stats,
                'sentiment': sentiment,
                'word_freq': word_freq[:50],
                'top5_videos': top5,
                'hot_comments': hot_comments[:20],
            }, f, ensure_ascii=False, indent=2)
        
        return output_path
