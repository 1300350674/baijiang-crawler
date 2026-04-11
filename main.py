#!/usr/bin/env python3
"""
B站UP主视频数据爬虫 - 主入口
爬取指定UP主视频数据并生成分析报告
"""
import os
import sys
import json
import argparse
from datetime import datetime

from bilibili_crawler import BilibiliCrawler
from analyzer import ReportGenerator
import config


def parse_args():
    parser = argparse.ArgumentParser(description='B站UP主视频数据爬虫')
    parser.add_argument('--up-id', '-u', default=config.UP_UNIQUE_ID, help='UP主ID或主页URL')
    parser.add_argument('--up-name', '-n', default=config.UP_NAME, help='UP主名称')
    parser.add_argument('--output-dir', '-o', default=config.OUTPUT_DIR, help='输出目录')
    parser.add_argument('--skip-crawl', '-s', action='store_true', help='跳过爬取，直接生成报告')
    parser.add_argument('--workers', '-w', type=int, default=config.MAX_WORKERS, help='并发线程数')
    return parser.parse_args()


def main():
    args = parse_args()
    
    output_dir = args.output_dir
    data_dir = os.path.join(output_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"{'='*60}")
    print(f"B站UP主视频数据爬虫")
    print(f"UP主: {args.up_name} ({args.up_id})")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}\n")
    
    if not args.skip_crawl:
        print("[1/3] 初始化爬虫...")
        crawler = BilibiliCrawler(headers=config.HEADERS)
        crawler.request_delay = config.REQUEST_DELAY
        crawler.max_retries = config.MAX_RETRIES
        
        print("[2/3] 开始爬取数据...")
        start_time = datetime.now()
        
        result = crawler.crawl_up(args.up_id, max_workers=args.workers)
        
        if not result or not result.get('videos'):
            print("[ERROR] 爬取失败，请检查网络或UP主ID是否正确")
            sys.exit(1)
        
        print(f"爬取完成! 耗时: {datetime.now() - start_time}")
        print(f"获取视频: {len(result['videos'])} 个")
        
        print("[3/3] 保存数据...")
        crawler.save_data(
            videos=result['videos'],
            comments=result.get('comments', {}),
            danmu_data=result.get('danmu', {}),
            output_dir=data_dir
        )
        print(f"数据已保存到: {data_dir}")
        
        up_info = result.get('up_info', {})
    else:
        print("[INFO] 跳过爬取步骤")
        up_info = {}
    
    print("\n" + "="*60)
    print("[4/4] 生成分析报告...")
    generator = ReportGenerator(data_dir=data_dir, output_dir=output_dir)
    report_path = generator.generate(up_name=args.up_name, up_info=up_info)
    
    print(f"\n报告生成完成!")
    print(f"报告路径: {report_path}")
    print(f"数据目录: {data_dir}")
    print("="*60)


if __name__ == '__main__':
    main()
