import os
import traceback
import requests
import csv
import time
import re
import urllib.parse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 全局配置
PICTURE_DOWNLOAD_INTERVAL = 0.5
REQUESTS_TIMEOUT = 30
WEIBO_PIC_PATH = "./微博图片动态/"
CSV_PATH = "微博记录.csv"
requests.DEFAULT_RETRIES = 5
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 10  # 重试间隔（秒）

class WeiboAdvancedCrawler:
    def __init__(self):
        if not os.path.exists(WEIBO_PIC_PATH):
            os.makedirs(WEIBO_PIC_PATH, exist_ok=True)
        self.key = ""
        self.start_date = None
        self.end_date = None
        self.scope = "ori"
        self.has_pic = True
        self.__init_csv()

    def __init_csv(self):
        if not os.path.exists(CSV_PATH):
            with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['类型', '来源', '关键词', '作者', '标题', '简介', '标签', '图注', 
                                '原文链接', '图片链接', '本地链接', '创建时间'])

    def set_search_params(self, keywords: list, start_date: str = None, end_date: str = None, scope: str = "ori", has_pic: bool = True):
        self.key = "+".join(keywords)
        self.start_date = start_date
        self.end_date = end_date
        self.scope = scope
        self.has_pic = has_pic

    def __log(self, message: str):
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()} {message}\n")

    def __download_pic(self, url: str, path: str):
        try:
            r = requests.get(url, timeout=REQUESTS_TIMEOUT)
            r.raise_for_status()
            with open(path, 'wb') as f:
                f.write(r.content)
            print(f"图片下载成功: {path}")
        except:
            self.__log(f"下载图片失败: {url}\n{traceback.format_exc()}")
        time.sleep(PICTURE_DOWNLOAD_INTERVAL)

    def __get_tags(self, text: str):
        tags = []
        soup = BeautifulSoup(text, 'html.parser')
        for a in soup.find_all('a', href=re.compile(r'weibo\.com\/[a-zA-Z]+\/[a-zA-Z0-9]+')):
            tag = a.text.strip()
            if tag.startswith('#') and tag.endswith('#'):
                tags.append(tag[1:-1])
        return tags

    def __get_text(self, text: str):
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text(strip=True)

    def __append_to_csv(self, record: list):
        try:
            with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(record)
            print(f"记录写入 CSV: {record[8]}")
        except:
            self.__log(f"写入 CSV 失败: {traceback.format_exc()}")

    def __request(self, url: str):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://s.weibo.com/',
            'Cookie': 'SCF=Ar7jzpx6TRlbgzUGGij9EQJOi4vq0tboMa3qFDKTjYgcGSEzaQ0WWLBV3v6Kw-qAAoW-M3I_QuG9Dp039UKLqAw.; SUB=_2A25K6-xzDeRhGeFH7VoZ8S7Iwz-IHXVpiWG7rDV8PUNbmtANLULMkW9Neou_JiA4h42xf5741fXW0GGbAvr-ePxd; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFsmxZm62lAyT_90_GupI015NHD95QN1KqR1h27Shn0Ws4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0.c1hnpehBRe7tt; ALF=02_1746348323; _s_tentry=passport.weibo.com; Apache=6283768143030.159.1743756326045; SINAGLOBAL=6283768143030.159.1743756326045; ULV=1743756326098:1:1:1:6283768143030.159.1743756326045:; WBPSESS=P16UVdooRyDTzmbj2KHwQv1nAugUJryGPZxDCAI06XWaP09TOgrSjtFJ9dc7LESv7zyFRLmm5M17ubi-zgEbiKTuMcNumMVmSWW4DHc6kSRY9zWOCwNn_iZDdbHn-jExMbL5BzS6Qbj6xYI0U2xJhg=='
        }
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.get(url, headers=headers, timeout=REQUESTS_TIMEOUT)
                response.raise_for_status()
                with open('response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"请求成功: {url}")
                return response.text
            except Exception as e:
                self.__log(f"请求失败 (尝试 {attempt + 1}/{MAX_RETRIES + 1}): {url}\n{str(e)}\n{traceback.format_exc()}")
                if attempt < MAX_RETRIES:
                    print(f"请求失败，第 {attempt + 1} 次尝试失败，将在 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"请求失败，已达到最大重试次数 ({MAX_RETRIES})，放弃此请求: {url}")
                    return None

    def __parse_weibo(self, html: str, source: str, base_path: str):
        soup = BeautifulSoup(html, 'html.parser')
        seen_urls = set()
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    seen_urls.add(row[8])

        cards = soup.select('div.card-wrap')
        print(f"找到 {len(cards)} 条微博卡片")

        if not cards:
            print("未找到微博卡片，检查选择器或 HTML 内容")
            self.__log("未找到微博卡片，HTML 已保存至 response.html")
            return

        for card in cards:
            try:
                mid = card.get('mid') or card.get('data-mid') or card.get('id')
                if not mid:
                    print("未找到 mid，跳过此卡片")
                    continue
                url_article = f"https://m.weibo.cn/detail/{mid}"
                if url_article in seen_urls:
                    print(f"跳过已记录的微博: {mid}")
                    continue

                author = card.select_one('a.name') or card.select_one('div.info a')
                author_name = author.text.strip() if author else "-"

                content = card.select_one('p.txt') or card.select_one('div.weibo-text')
                text = content.get('data-original-title', content.text) if content else "-"
                tags = self.__get_tags(str(content)) if content else []

                created_at_elem = card.select_one('div.from > a') or card.select_one('span.time')
                created_at = created_at_elem.text.strip() if created_at_elem else "-"
                if created_at != "-":
                    if re.match(r'\d{4}年\d{2}月\d{2}日 \d{2}:\d{2}', created_at):
                        created_at = created_at.replace('年', '-').replace('月', '-').replace('日', '') + ':00'
                    else:
                        print(f"未识别的时间格式: {created_at}")
                        created_at = "-"
                print(f"微博 {mid} 创建时间: {created_at}")

                pics = card.select('img[src*="sinaimg"]')
                print(f"微博 {mid} 找到 {len(pics)} 张图片")
                if not pics and self.has_pic:
                    print(f"微博 {mid} 无图片，跳过（预期应含图片）")
                    continue

                for pic in pics:
                    pic_url = pic.get('src')
                    if not pic_url:
                        print(f"微博 {mid} 的图片缺少 src 属性，跳过")
                        continue
                    if pic_url.startswith('//'):
                        pic_url = 'https:' + pic_url
                    elif not pic_url.startswith('http'):
                        print(f"无效图片 URL: {pic_url}，跳过")
                        continue

                    print(f"尝试下载图片: {pic_url}")
                    local_path = f"{base_path}{self.key}_{mid}_{len(tags)}_{os.urandom(4).hex()}.jpg"
                    record = [
                        '图片', source, self.key, author_name, "-",
                        self.__get_text(text), ",".join(tags), "-",
                        url_article, pic_url, local_path, created_at
                    ]
                    self.__append_to_csv(record)
                    self.__download_pic(pic_url, local_path)
            except:
                self.__log(f"解析单条微博失败: {mid}\n{traceback.format_exc()}")

    def __get_total_pages(self, html: str) -> int:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            page_nav = soup.select_one('ul.s-scroll') or soup.select_one('div.m-page') or soup.select_one('div.s-scroll')
            if not page_nav:
                print("未找到分页导航，假设只有1页")
                return 1
            
            pages = page_nav.select('a[href*="page="]')
            if not pages:
                print("未找到页码链接，假设只有1页")
                return 1
            
            max_page = 1
            for page in pages:
                href = page.get('href', '')
                page_num = re.search(r'page=(\d+)', href)
                if page_num:
                    num = int(page_num.group(1))
                    max_page = max(max_page, num)
            print(f"检测到的最大页数: {max_page}")
            return max_page
        except Exception as e:
            self.__log(f"获取总页数失败: {str(e)}\n{traceback.format_exc()}")
            print("页数检测异常，默认返回1页")
            return 1

    def search(self, pages: int):
        source = "微博原创动态" if self.scope == "ori" else f"微博{self.scope}动态"
        base_path = WEIBO_PIC_PATH

        # 存储需要处理的时间段列表，格式为 [(start_date, end_date)]
        time_segments = [(self.start_date, self.end_date)]

        while time_segments:
            # 从列表中取出一个时间段处理
            current_start, current_end = time_segments.pop(0)
            print(f"处理时间段: {current_start} 至 {current_end}")

            # 构造当前时间段的URL
            base_url = f"https://s.weibo.com/weibo?q={urllib.parse.quote(self.key)}"
            if self.scope and self.scope != "all":
                base_url += f"&scope={self.scope}"
            if current_start and current_end:
                base_url += f"×cope=custom:{current_start}:{current_end}"
            if self.has_pic:
                base_url += "&haspic=1"

            # 获取当前时间段的总页数
            print(f"检查时间段 {current_start} 至 {current_end} 的总页数: {base_url}")
            html = self.__request(base_url)
            if not html:
                print("无法获取第一页内容，跳过此时间段")
                continue

            total_pages = self.__get_total_pages(html)
            print(f"当前时间段 {current_start} 至 {current_end} 检测到总页数: {total_pages}")

            # 如果总页数大于49，进行时间段二分并存储
            if total_pages > 49:
                print(f"总页数 {total_pages} 超过49，正在进行时间段二分...")
                start = datetime.strptime(current_start, '%Y-%m-%d')
                end = datetime.strptime(current_end, '%Y-%m-%d')
                mid = start + (end - start) / 2
                mid_date = mid.strftime('%Y-%m-%d')
                mid_next_day = (mid + timedelta(days=1)).strftime('%Y-%m-%d')

                # 添加前半段和后半段到时间段列表
                time_segments.insert(0, (current_start, mid_date))  # 前半段优先处理
                time_segments.insert(1, (mid_next_day, current_end))  # 后半段次之
                print(f"分段后待处理时间段: {time_segments}")
                continue

            # 如果总页数为1，不加page参数
            if total_pages == 1:
                print(f"总页数为1，正在爬取: {base_url}")
                html = self.__request(base_url)
                if html:
                    print(f"正在爬取唯一一页 {source}，图片将保存至 {base_path}")
                    self.__parse_weibo(html, source, base_path)
                continue

            # 如果总页数在1到49之间，爬取对应页数
            pages_to_crawl = min(total_pages, pages)
            print(f"总页数 {total_pages} 在1到49之间，将爬取 {pages_to_crawl} 页")
            for page in range(1, pages_to_crawl + 1):
                try:
                    url = f"{base_url}&page={page}"
                    print(f"搜索 URL: {url}")
                    html = self.__request(url)
                    if not html:
                        print(f"第 {page} 页请求失败")
                        continue
                    print(f"正在爬取第 {page} 页 {source}，图片将保存至 {base_path}")
                    self.__parse_weibo(html, source, base_path)
                except:
                    self.__log(f"爬取第 {page} 页失败: {traceback.format_exc()}")
                    break

if __name__ == "__main__":
    weibo = WeiboAdvancedCrawler()
    weibo.set_search_params(keywords=["缅甸地震"], start_date="2025-03-28", end_date="2025-04-05", scope="ori", has_pic=True)
    weibo.search(pages=49)
