import hashlib
import urllib
from urllib.parse import quote
import cfscrape
import requests
from lxml import etree
import time
import pymysql
from concurrent import futures
from bs4 import BeautifulSoup
from loguru import logger
import os


class APKPureScraper:
    def __init__(self):
        self.sign_key = '34c79de5474eb652' #密钥
        self.scraper = cfscrape.create_scraper(delay=10)  # 创建一个带有延迟的请求器
        self.conn = pymysql.connect(host='localhost', user='root', password='123456', database='apkdiango')  # 连接数据库
        self.cursor = self.conn.cursor()  # 创建一个数据库游标
        self.data = []  # 初始化数据列表
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"  # 设置请求头user-agent
        }

    def spider(self, q):
        try:
            url = f"https://apkpure.net/search?q={q}"  # 搜索页链接
            resp = self.scraper.get(url)  # 发送请求
            res = resp.content.decode(encoding='utf-8', errors='ignore')  # 解码响应内容
            root = etree.HTML(res)  # 解析HTML
            if root.xpath(f'//div[@data-dt-app="{q}"]//a[contains(@class,"first-info")]'):  # 判断是否存在目标游戏链接
                game_download_first_url = root.xpath(f'//div[@data-dt-app="{q}"]//a[contains(@class,"first-info")]/@href')[0]  # 获取游戏链接
            else:
                raise ValueError('获取不到此游戏 请更换包名')  # 抛出异常
            resp = self.scraper.get(game_download_first_url)  # 发送游戏下载链接请求
            res = resp.content.decode()  # 解码响应内容
            root = etree.HTML(res)  # 解析HTML
            version_list = root.xpath('//div[@class="card version-list"]/a') or root.xpath("//div[@class='version-item']/a") # 获取版本列表链接
            if len(version_list) == 0:  # 判断是否有历史版本
                print("已是最新版本 无历史版本")
            else:
                if version_list[-1].xpath('@class')[0] == 'more-version':  # 判断是否需要获取更多版本链接
                    more_version_url = version_list[-1].xpath('@href')[0]  # 获取更多版本链接
                    resp = self.scraper.get(more_version_url)  # 发送更多版本链接请求
                    res = resp.content.decode()  # 解码响应内容
                    root = etree.HTML(res)  # 解析HTML
                    li_list = root.xpath('//div[@class="ver_content_box"]/ul/li')  # 获取版本列表
                    for li in li_list[:-1]:  # 遍历版本列表
                        # apk_size = li.xpath('.//span[@class="ver-item-s"]/text()')[0]  # 获取apk大小
                        apk_url = li.xpath('./a/@href')[0]  # 获取apk下载链接

                        resp = self.scraper.get(apk_url)  # 发送apk下载链接请求
                        res = resp.content.decode()  # 解码响应内容
                        root = etree.HTML(res)  # 解析HTML
                        apk_version = root.xpath("//div[@class='info-content one-line']/span[@class='info-sdk']/span/text()")[0]  # 获取apk版本号
                        apk_download_url = ''.join(root.xpath("//div[@class='main-body']/main/div[contains(@class,'download-box')]/a[@class='btn download-start-btn' and contains(@href, 'apk') and not(contains(@href, 'xapk')) and not(contains(@href, 'xpak'))]/@href"))# 获取apk下载链接
                        if not apk_download_url:
                            apk_download_url = 'https://apkpure.net'+''.join(root.xpath("//a[@class='btn jump-downloading-btn']/@href"))
                        if root.xpath('//div[@class="module change-log"]'):  # 判断是否存在更新日志
                            change_log = ''.join(root.xpath('//div[@class="module change-log"]//p[@class="content"]/text()'))  # 获取更新日志
                            data_item = {'apk_name': q, 'apk_version': apk_version, 'apk_download_url': apk_download_url, 'change_log': change_log}  # 创建数据字典
                        else:
                            data_item = {'apk_name': q, 'apk_version': apk_version, 'apk_download_url': apk_download_url, 'change_log': ''}  # 创建数据字典
                        self.data.append(data_item)  # 将数据字典添加到数据列表中
                else:
                    for i in version_list:  # 遍历版本列表
                        # apk_size = i.xpath('./div[@class="version-info"]//span[@class="size"]/text()')[0]  # 获取apk大小
                        apk_url = i.xpath('@href')[0]  # 获取apk下载链接
                        print(apk_url)

                        resp = self.scraper.get(apk_url)  # 发送apk下载链接请求
                        res = resp.content.decode()  # 解码响应内容
                        root = etree.HTML(res)  # 解析HTML
                        apk_version = root.xpath("//div[@class='info-content one-line']/span[@class='info-sdk']/span/text()")[0]  # 获取apk版本号
                        apk_download_url = ''.join(root.xpath("//div[@class='main-body']/main/div[contains(@class,'download-box')]/a[@class='btn download-start-btn']/@href"))  # 获取apk下载链接
                        if not apk_download_url:
                            apk_download_url = ''.join(root.xpath("//div[@class='apk']/a[@class='download-btn']/@href"))

                        if root.xpath('//div[@class="module change-log"]'):  # 判断是否存在更新日志
                            change_log = root.xpath('//div[@class="module change-log"]//p[@class="content"]/text()')[0]  # 获取更新日志
                            data_item = {'apk_name': q, 'apk_version': apk_version, 'apk_download_url': apk_download_url, 'change_log': change_log}  # 创建数据字典
                        else:
                            data_item = {'apk_name': q, 'apk_version': apk_version, 'apk_download_url': apk_download_url, 'change_log': ''}  # 创建数据字典
                        self.data.append(data_item)  # 将数据字典添加到数据列表中
                        print(data_item)
                        print('---------------------------------------------')
            return self.data  # 返回数据列表
        except Exception as e:
            print(e)
            return '获取失败'  # 返回异常信息


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
        res = requests.post("http://8.217.220.140:8088/task/loadUrl", headers={'Content-Type': 'application/json'}, json =payload)  # 发送POST请求

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



    def download_apk(self, download_links):
        def download_single_apk(download_link):
            try:
                response = requests.get(download_link, stream=True)
                if response.status_code == 200:
                    # 解析文件名
                    apk_name = os.path.basename(urllib.parse.urlparse(download_link).path)
                    # 保存文件
                    with open(apk_name, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            f.write(chunk)
            except Exception as e:
                print(f"Error downloading APK: {e}")

            # 创建线程池
        with futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 提交下载任务
            executor.map(download_single_apk, download_links)



    def main(self, q):
        data_list = self.spider(q)  # 调用spider函数获取数据列表
        if data_list == '获取失败':
            return '获取失败'  # 返回获取失败信息
        elif not data_list:
            return ''
        else:
            self.save_to_database(data_list)  # 调用save_to_database函数将数据保存到数据库中
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
    state = apk_scraper.main('com.mspengejar.hari') # 调用main函数爬取数据
    print(state)  # 打印结果



