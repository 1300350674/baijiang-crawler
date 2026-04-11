"""
配置文件
"""
import os

UP_NAME = "白昼小熊"
UP_UNIQUE_ID = "19523724"
OUTPUT_DIR = "output"
DATA_DIR = os.path.join(OUTPUT_DIR, "data")

MAX_WORKERS = 3
MAX_RETRIES = 3
REQUEST_DELAY = (1, 3)
MAX_COMMENT_PAGES = 5
MAX_DANMU_VIDEOS = 10

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
}
