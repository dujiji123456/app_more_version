import hashlib, re
import os
import urllib
from urllib.parse import quote
import cfscrape
import requests
from lxml import etree
import time
import logging
import pymysql
from concurrent import futures
from bs4 import BeautifulSoup
from tqdm import tqdm
import threading
from .models import MoreVersionApk

logger = logging.getLogger("global_logger")
logger.setLevel(logging.ERROR)
handler = logging.FileHandler('log/error.log', 'a')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class APKPureScraper:
    def __init__(self):
        self.sign_key = '34c79de5474eb652'  # 密钥
        self.scraper = cfscrape.create_scraper(delay=10)  # 创建一个带有延迟的请求器
        self.conn = pymysql.connect(host='localhost', user='jack', password='010711', database='apkdiango')  # 连接数据库
        self.cursor = self.conn.cursor()  # 创建一个数据库游标
        self.data = []  # 初始化数据列表
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "dnt": "1",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Microsoft Edge\";v=\"126\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }
        self.cookies = {
            "_apk_uid": "8HAGCmd5i5cJHjJCRKkywJ942Zcs5Xs2",
            "_user_tag": "j%3A%7B%22language%22%3A%22en%22%2C%22source_language%22%3A%22zh-CN%22%2C%22country%22%3A%22US%22%7D",
            "m1": "19930",
            "m2": "90334508abed6e0cc92ef542ff993689",
            "apkpure__lang": "en",
            "apkpure__country": "US",
            "apkpure__sample": "0.3798964788557957",
            "_dt_sample": "0.26147796756781827",
            "_dt_referrer_fix": "0.7723206727122089",
            "_tag_sample": "0.053983276054029306",
            "_home_article_entry_sample": "0.22636317535509298",
            "_related_recommend": "0.5322453660812099",
            "_download_detail_sample": "0.7708545275476448",
            "_f_sp": "1593508291",
            "AMP_TOKEN": "%24NOT_FOUND",
            "_gid": "GA1.2.544494795.1721897761",
            "_qimei": "t8z3w8deAFG7ncdNwGpbmA1BMAN0y3Nr",
            "apkpure__policy_review_new": "all",
            "apkpure__policy_review": "20180525",
            "_apk_sid": "1.1.1721897758159.1.3.1721898389570.-480",
            "download_id": "otr_1959903744876722",
            "_ga": "GA1.1.1116378776.1721897760",
            "_ga_NT1VQC8HKJ": "GS1.1.1721897760.1.1.1721898394.56.0.0"
        }
        self.p = {
            "http": "http://127.0.0.1:7897"
        }

    def spider(self, q):
        try:
            url = f"https://apkpure.net/search?q={q}"  # 搜索页链接
            resp = self.scraper.get(url)  # 发送请求
            res = resp.content.decode(encoding='utf-8', errors='ignore')  # 解码响应内容
            root = etree.HTML(res)  # 解析HTML
            if root.xpath(f'//div[@data-dt-app="{q}"]//a[contains(@class,"first-info")]'):  # 判断是否存在目标游戏链接
                game_download_first_url = \
                    root.xpath(f'//div[@data-dt-app="{q}"]//a[contains(@class,"first-info")]/@href')[0]  # 获取游戏链接
            else:
                raise ValueError('获取不到此游戏 请更换包名')  # 抛出异常
            resp = self.scraper.get(game_download_first_url)  # 发送游戏下载链接请求
            res = resp.content.decode()  # 解码响应内容
            root = etree.HTML(res)  # 解析HTML
            version_list = root.xpath("//div[@class='version-item']/a")   # 获取版本列表链接
            if len(version_list) == 0:  # 判断是否有历史版本
                print("已是最新版本 无历史版本")
            else:
                if root.xpath('//a[@class="more-version"]'):  # 判断是否需要获取更多版本链接
                    more_version_url = 'https://apkpure.net' + root.xpath('//a[@class="more-version"]/@href')[0] # 获取更多版本链接
                    resp = self.scraper.get(more_version_url)  # 发送更多版本链接请求
                    res = resp.content.decode()  # 解码响应内容
                    root = etree.HTML(res)  # 解析HTML
                    li_list = root.xpath("//ul[@class='version-list']/li") or root.xpath("//ul[@class='ver-wrap']/li")  # 获取版本列表
                    for li in li_list[:-1]:  # 遍历版本列表
                        apk_url = li.xpath('./a/@href')[0]  # 获取apk下载链接
                        if 'https://apkpure.net' not in apk_url:
                            apk_url = 'https://apkpure.net' + apk_url# 获取apk下载链接
                        resp = self.scraper.get(apk_url)  # 发送apk下载链接请求a
                        res = resp.content.decode()  # 解码响应内容
                        root = etree.HTML(res)  # 解析HTML
                        apk_version = ''.join(root.xpath("//div[@class='module-card-container whats-new']/h2[@class='card-top']/text()")[0]).replace("What's New in the Latest Version", '')  # 获取apk版本号
                        apk_download_urls = ''.join(root.xpath(
                            "//div[@class='download-box download-button-box d-normal download-box-sample']/a[@class='btn d-normal-a jump-downloading-btn' and contains(@href, 'apk') and not(contains(@href, 'xapk')) and not(contains(@href, 'xpak'))]/@href"))  # 获取apk下载链接
                        if not apk_download_urls:
                            apk_download_urls = 'https://apkpure.net' + ''.join(
                                root.xpath("//a[@class='btn d-normal-a jump-downloading-btn']/@href"))
                            change_log = ''.join(root.xpath('//div[@class="show-more-content"]/p//text()'))  # 获取更新日志
                            if not change_log:
                                change_log = ''
                            data_item = {'apk_name': q, 'apk_version': apk_version,
                                         'apk_download_url': apk_download_urls, 'change_log': change_log}  # 创建数据字典
                        else:
                            data_item = {'apk_name': q, 'apk_version': apk_version,
                                         'apk_download_url': apk_download_urls, 'change_log': ''}  # 创建数据字典
                        self.data.append(data_item)  # 将数据字典添加到数据列表中
                else:
                    for i in version_list:  # 遍历版本列表
                        apk_url = i.xpath('@href')[0]  # 获取apk下载链接
                        # print(apk_url)

                        resp = self.scraper.get(apk_url)  # 发送apk下载链接请求
                        res = resp.content.decode()  # 解码响应内容
                        root = etree.HTML(res)  # 解析HTML
                        apk_version = \
                            root.xpath("//div[@class='info-content one-line']/span[@class='info-sdk']/span/text()")[
                                0]  # 获取apk版本号
                        apk_download_urls = ''.join(root.xpath(
                            "//div[@class='main-body']/main/div[contains(@class,'download-box')]/a[@class='btn download-start-btn']/@href"))  # 获取apk下载链接
                        if not apk_download_urls:
                            apk_download_urls = ''.join(
                                root.xpath("//div[@class='apk']/a[@class='download-btn']/@href"))

                        change_log = ''.join(root.xpath('//div[@class="show-more-content"]/p//text()'))  # 获取更新日志
                        if not change_log:
                            change_log = ''  # 获取更新日志
                            data_item = {'apk_name': q, 'apk_version': apk_version,
                                         'apk_download_url': apk_download_urls, 'change_log': change_log}  # 创建数据字典
                        else:
                            data_item = {'apk_name': q, 'apk_version': apk_version,
                                         'apk_download_url': apk_download_urls, 'change_log': ''}  # 创建数据字典
                        self.data.append(data_item)  # 将数据字典添加到数据列表中
                        print(data_item)
                        print('---------------------------------------------')
            print(len(self.data))
            self.multi_thread(self.data)
            return self.data  # 返回数据列表
        except Exception as e:
            print(e)
            return '获取失败'  # 返回异常信息

    def multi_thread(self, app_more_version_list):
        n = 1
        splitList = [app_more_version_list[i:i + n] for i in range(0, len(app_more_version_list), n)]
        threads = []
        for i in range(len(splitList)):
            t = threading.Thread(target=self.down_app, args=(splitList[i]))
            threads.append(t)
            t.start()

    def down_app(self, torront):
        apk_download_urls = torront['apk_download_url']
        apk_name = torront['apk_name']
        apk_version = torront['apk_version']
        update_content = torront['change_log']
        if 'XAPK' not in apk_download_urls:
            response1 = requests.get(apk_download_urls, headers=self.headers, cookies=self.cookies, proxies=self.p)

            r = re.findall("(https://d.apkpure.net/b/.*?)\"", response1.content.decode())[0]
            if 'XAPK' not in r:
                response2 = requests.head(r, headers=self.headers, cookies=self.cookies, proxies=self.p)
                apk_download_url = response2.headers['Location']
                response = self.retry(apk_download_url)
                total_size = int(response2.headers.get('content-length', 0))
                download_dir = r'E:\apkdjango\apkmoreversion\apkapps\downloads'
                # download_dir = 项目路径 + 'apkmoreversion/apkapps/downloads'
                if not os.path.lexists(os.path.join(download_dir, apk_name)):
                    os.mkdir(os.path.join(download_dir, apk_name))
                if response:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=f'{apk_name}_{apk_version}',
                              ncols=100) as pbar:
                        with open(os.path.join(download_dir, apk_name, f'{apk_name}_{apk_version}.apk'), 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                    down_path = os.path.join(download_dir, apk_name, f'{apk_name}_{apk_version}.apk')
                    MoreVersionApk.objects.create(apk_version=apk_version, apk_name=apk_name,
                                                  apk_download_url=apk_download_url, update_content=update_content,
                                                  down_path=down_path)

                else:
                    return

            else:
                print(3333, r)
        else:
            return

    def retry(self, apk_download_url):
        max_retries = 5
        retry_delay = 5
        time_out = 10
        retry_count = 0
        for _ in range(max_retries):
            response = self.make_request(apk_download_url, time_out, retry_count, max_retries)
            if response:
                if response.status_code == 200:
                    return response
            else:
                retry_count += 1
                time.sleep(retry_delay)

    def make_request(self, apk_download_url, time_out, retry_count, max_retries):
        try:
            response = requests.get(apk_download_url, headers=self.headers, timeout=time_out, stream=True,
                                    cookies=self.cookies, proxies=self.p)
            return response
        except (requests.exceptions.RequestException, ValueError) as e:
            if retry_count == max_retries:
                logging.error(f'{apk_download_url}下载出错,{e}')
            return None

    def save_to_database(self, data_list):
        for item in data_list:
            try:
                sql = "INSERT INTO apkapps_moreversionapk(apk_version, apk_name, apk_download_url, update_content) VALUES (%s, %s, %s, %s) \
                       ON DUPLICATE KEY UPDATE apk_version = VALUES(apk_version), update_content = VALUES(update_content)"  # 插入或更新语句
                self.cursor.execute(sql, (
                    item['apk_version'], item['apk_name'], item['apk_download_url'], item['change_log']
                ))  # 执行插入或更新语句
                self.conn.commit()  # 提交事务

            except Exception as e:
                pass

        self.conn.close()  # 关闭数据库连接
        print('数据已写入')

    def upload(self, item):
        change_log = item.get('change_log', '')  # 获取change_log字段，如果不存在默认为空字符串

        # 使用 BeautifulSoup 解析 HTML内容提取纯文本
        soup = BeautifulSoup(change_log, 'html.parser')
        change_log_text_only = soup.get_text()
        print(change_log_text_only.encode('utf-8'))

        change_log_one = urllib.parse.quote(change_log_text_only)  # 对change_log进行URL编码

        payload = {
            "url": item['apk_download_url'],  # 请求URL
            "packageName": item['apk_name'],  # 应用包名
            "extraData": change_log_one,  # 额外数据
            "time": str(int(time.time())),  # 时间戳
        }

        payload["sign"] = self.make_signature(payload, '34c79de5474eb652')  # 生成签名
        res = requests.post("http://8.217.220.140:8088/task/loadUrl", headers={'Content-Type': 'application/json'},
                            json=payload)  # 发送POST请求

        print(payload)  # 打印请求参数
        print(res.status_code)  # 打印响应状态码
        print(res.text)  # 打印响应内容

    def make_signature(self, data, sign_key):  # 生成签名方法
        sorted_data = dict(sorted(data.items()))  # 对请求参数进行排序
        s = ''  # 签名字符串初始化
        for k, v in sorted_data.items():
            v = quote(v, safe='')  # 对参数值进行URL编码
            s += "&{}={}".format(k, v)  # 拼接排序后的参数字符串
        s = s[1:]  # 去除签名字符串的第一个字符

        return hashlib.md5((s + sign_key).encode('utf-8')).hexdigest()  # 使用MD5算法生成签名的哈希值

    def main(self, q):
        data_list = self.spider(q)  # 调用spider函数获取数据列表
        if data_list == '获取失败':
            return '获取失败'  # 返回获取失败信息
        elif not data_list:
            return ''
        else:
            with futures.ThreadPoolExecutor(max_workers=2) as executor:  # 创建线程池
                tasks = []
                for item in data_list:  # 遍历数据列表
                    tasks.append(executor.submit(self.upload, item))  # 将获取apk的任务添加到任务列表中
                iter_list = futures.as_completed(tasks)
                for future in iter_list:  # 遍历任务列表
                    future.result()

            return data_list  # 返回数据列表


if __name__ == '__main__':
    apk_scraper = APKPureScraper()  # 创建APKPureScraper实例
    state = apk_scraper.main('com.olzhas.carparking.multyplayer')  # 调用main函数爬取数据
    print(state)  # 打印结果
