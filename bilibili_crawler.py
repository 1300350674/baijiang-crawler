"""
Bilibili Video Crawler
爬取B站up主视频数据、评论、弹幕统计
"""
import requests
import re
import json
import time
import random
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    bvid: str
    title: str
    aid: int
    pubdate: str
    duration: str
    view: int = 0
    like: int = 0
    coin: int = 0
    favorite: int = 0
    share: int = 0
    danmu: int = 0
    desc: str = ""
    author: str = ""
    url: str = ""


@dataclass
class Comment:
    oid: int
    rpid: int
    uname: str
    content: str
    like: int
    ctime: str
    reply: int = 0


class BilibiliCrawler:
    def __init__(self, headers: Optional[Dict] = None):
        self.session = requests.Session()
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://www.bilibili.com',
        }
        if headers:
            default_headers.update(headers)
        self.session.headers.update(default_headers)
        
        self.base_url = "https://api.bilibili.com"
        self.web_url = "https://www.bilibili.com"
        
        self.request_delay = (1, 3)
        self.max_retries = 3
        
    def _request_with_retry(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        for attempt in range(self.max_retries):
            try:
                self._random_delay()
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(random.uniform(5, 15))
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {url}")
                    return None
        return None
    
    def _random_delay(self):
        delay = random.uniform(*self.request_delay)
        time.sleep(delay)
    
    def get_up_info(self, unique_id: str) -> Optional[Dict]:
        url = f"{self.base_url}/x/web-interface/card"
        params = {'card': unique_id, 'photo': 'true'}
        response = self._request_with_retry(url, params=params)
        if response and response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and data.get('data'):
                return data['data']
        return None
    
    def get_up_videos(self, mid: str, ps: int = 30) -> List[VideoInfo]:
        videos = []
        pn = 1
        total = float('inf')
        
        while len(videos) < total:
            url = f"{self.base_url}/x/space/wbi/arc/search"
            params = {'mid': mid, 'pn': pn, 'ps': ps, 'order': 'pubdate'}
            
            response = self._request_with_retry(url, params=params)
            if not response or response.status_code != 200:
                break
                
            data = response.json()
            if data.get('code') != 0:
                logger.error(f"API error: {data.get('message')}")
                break
            
            result = data.get('data', {})
            vlist = result.get('list', {}).get('vlist', [])
            
            if not vlist:
                break
                
            total = result.get('page', {}).get('count', 0)
            
            for v in vlist:
                video = VideoInfo(
                    bvid=v.get('bvid', ''),
                    title=v.get('title', ''),
                    aid=v.get('aid', 0),
                    pubdate=datetime.fromtimestamp(v.get('pubdate', 0)).strftime('%Y-%m-%d') if v.get('pubdate') else '',
                    duration=self._format_duration(v.get('length', '')),
                    view=v.get('play', 0),
                    like=v.get('like', 0),
                    coin=v.get('coin', 0),
                    favorite=v.get('favorite', 0),
                    share=v.get('share', 0),
                    danmu=v.get('video_reply', 0),
                    desc=v.get('description', ''),
                    author=v.get('author', ''),
                    url=f"https://www.bilibili.com/video/{v.get('bvid', '')}"
                )
                videos.append(video)
            
            logger.info(f"Fetched page {pn}, total videos: {len(videos)}/{total}")
            pn += 1
            
            if len(videos) >= total:
                break
        
        return videos
    
    def get_video_stats(self, bvid: str) -> Optional[Dict]:
        url = f"{self.base_url}/x/web-interface/view"
        params = {'bvid': bvid}
        response = self._request_with_retry(url, params=params)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                stat = data.get('data', {}).get('stat', {})
                return {
                    'view': stat.get('view', 0),
                    'like': stat.get('like', 0),
                    'coin': stat.get('coin', 0),
                    'favorite': stat.get('favorite', 0),
                    'share': stat.get('share', 0),
                    'danmu': stat.get('danmaku', 0),
                }
        return None
    
    def get_comments(self, oid: int, pn: int = 1, sort: int = 2, hot: bool = True) -> List[Comment]:
        comments = []
        url = f"{self.base_url}/x/v2/reply"
        params = {
            'type': 1,
            'oid': oid,
            'pn': pn,
            'sort': sort,
            'ps': 20
        }
        
        response = self._request_with_retry(url, params=params)
        if not response or response.status_code != 200:
            return comments
        
        try:
            data = response.json()
            if data.get('code') == 0:
                replies = data.get('data', {}).get('replies', []) or []
                
                for r in replies:
                    if not r:
                        continue
                    comment = Comment(
                        oid=oid,
                        rpid=r.get('rpid', 0),
                        uname=r.get('member', {}).get('uname', ''),
                        content=r.get('content', {}).get('message', ''),
                        like=r.get('like', 0),
                        ctime=datetime.fromtimestamp(r.get('ctime', 0)).strftime('%Y-%m-%d %H:%M') if r.get('ctime') else '',
                        reply=r.get('rcount', 0)
                    )
                    comments.append(comment)
                    
                    if hot:
                        hot_replies = r.get('replies', []) or []
                        for hr in hot_replies:
                            if not hr:
                                continue
                            hrc = Comment(
                                oid=oid,
                                rpid=hr.get('rpid', 0),
                                uname=hr.get('member', {}).get('uname', ''),
                                content=hr.get('content', {}).get('message', ''),
                                like=hr.get('like', 0),
                                ctime=datetime.fromtimestamp(hr.get('ctime', 0)).strftime('%Y-%m-%d %H:%M') if hr.get('ctime') else '',
                                reply=0
                            )
                            comments.append(hrc)
                            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Parse comments error: {e}")
            
        return comments
    
    def get_all_comments(self, oid: int, max_pages: int = 5) -> List[Comment]:
        all_comments = []
        for pn in range(1, max_pages + 1):
            comments = self.get_comments(oid, pn=pn)
            if not comments:
                break
            all_comments.extend(comments)
            logger.info(f"Fetched {len(all_comments)} comments for video {oid}")
        return all_comments
    
    def get_danmu(self, bvid: str) -> List[str]:
        cid_url = f"{self.base_url}/x/web-interface/view"
        params = {'bvid': bvid}
        response = self._request_with_retry(cid_url, params=params)
        
        if not response or response.status_code != 200:
            return []
        
        try:
            data = response.json()
            if data.get('code') == 0:
                cid = data.get('data', {}).get('cid')
                if cid:
                    danmu_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"
                    dm_response = self._request_with_retry(danmu_url)
                    if dm_response and dm_response.apparent_encoding:
                        dm_response.encoding = dm_response.apparent_encoding
                        danmu_list = re.findall(r'<d[^>]*>([^<]+)</d>', dm_response.text)
                        return danmu_list
        except Exception as e:
            logger.error(f"Get danmu error: {e}")
        return []
    
    @staticmethod
    def _format_duration(duration: str) -> str:
        if ':' in str(duration):
            return str(duration)
        try:
            seconds = int(duration)
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins:02d}:{secs:02d}"
        except:
            return str(duration)
    
    def save_data(self, videos: List[VideoInfo], comments: Dict[str, List[Comment]], danmu_data: Dict[str, List[str]], output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        videos_data = {
            'crawl_time': datetime.now().isoformat(),
            'total_videos': len(videos),
            'videos': [asdict(v) for v in videos]
        }
        
        comments_data = {
            'crawl_time': datetime.now().isoformat(),
            'by_video': {bv: [asdict(c) for c in cl] for bv, cl in comments.items()}
        }
        
        danmu_output = {
            'crawl_time': datetime.now().isoformat(),
            'by_video': danmu_data
        }
        
        with open(os.path.join(output_dir, 'videos.json'), 'w', encoding='utf-8') as f:
            json.dump(videos_data, f, ensure_ascii=False, indent=2)
            
        with open(os.path.join(output_dir, 'comments.json'), 'w', encoding='utf-8') as f:
            json.dump(comments_data, f, ensure_ascii=False, indent=2)
            
        with open(os.path.join(output_dir, 'danmu.json'), 'w', encoding='utf-8') as f:
            json.dump(danmu_output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Data saved to {output_dir}")
    
    def crawl_up(self, unique_id: str, max_workers: int = 3) -> Dict:
        logger.info(f"Starting crawl for up: {unique_id}")
        
        up_info = self.get_up_info(unique_id)
        if not up_info:
            logger.error(f"Cannot get up info for {unique_id}")
            return {}
        
        mid = up_info.get('card', {}).get('mid') or up_info.get('mid', '')
        logger.info(f"Up mid: {mid}, name: {up_info.get('card', {}).get('uname', '')}")
        
        videos = self.get_up_videos(mid)
        logger.info(f"Total videos fetched: {len(videos)}")
        
        comments = {}
        danmu_data = {}
        
        video_bvids = [v.bvid for v in videos[:20]]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_bvid = {executor.submit(self.get_all_comments, v.aid): v for v in videos if v.aid}
            
            for future in as_completed(future_to_bvid):
                v = future_to_bvid[future]
                try:
                    comments[v.bvid] = future.result()
                except Exception as e:
                    logger.error(f"Comments error for {v.bvid}: {e}")
                    comments[v.bvid] = []
        
        for v in videos[:10]:
            danmu_data[v.bvid] = self.get_danmu(v.bvid)
            logger.info(f"Fetched {len(danmu_data[v.bvid])} danmu for {v.bvid}")
        
        return {
            'up_info': up_info,
            'videos': videos,
            'comments': comments,
            'danmu': danmu_data
        }
