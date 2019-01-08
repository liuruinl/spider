import scrapy
from scrapy import Spider, Request
from selenium import webdriver
from scrapy.linkextractors import LinkExtractor
from IronEgg.items import Amazon
import time
# from concurrent.futures import ThreadPoolExecutor
import pymongo


class AmzSpider(Spider):
    name = 'amz'
    DB_URI = 'mongodb://liurui:rootroot@172.17.0.2:27017/admin'
    DB_NAME = 'scrapydata'

    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.browser = webdriver.Chrome(chrome_options=chrome_options)
        self.browser.set_page_load_timeout(120)

        self.client = pymongo.MongoClient(self.DB_URI)
        self.db = self.client[self.DB_NAME]
        self.base_url = "https://www.amazon.com/s/ref=nb_sb_noss_2?url=search-alias%3Daps&field-keywords="
        self.items = []
    def close(self, reason):
        self.browser.close()

    def start_requests(self):
        # todo reading key words from db here.

        collection = self.db["words"]

        start_urls = [
            # 'https://www.amazon.com/s/ref=nb_sb_noss_2?url=search-alias%3Daps&field-keywords=net%20core%20in%20action'
        ]

        for doc in collection.find({"owner": 1}):
            start_urls.append(self.base_url + doc["keys"])

        for url in start_urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        if response.status != 200:
            return
        ul = response.css("div #atfResults").css("#s-results-list-atf").css("li")
        if ul.__len__() > 0:
            for li in ul.css('li'):
                if li.attrib.__len__() > 0 and 'data-asin' in li.attrib:
                    amz = Amazon()
                    amz["RequestUrl"] = str(response.url)  # 请求URL
                    amz["SearchWords"] = str(response.url).replace(self.base_url, "")  # 搜索关键词
                    amz["PageIndex"] = response.xpath('//*[@id="pagn"]/span[2]/text()').extract()[0]  # 当前页索引
                    amz["ASIN"] = li.attrib['data-asin']  # ASIN
                    amz["TotalIndex"] = li.attrib['id']  # 总排名
                    yield amz
            #todo paging seems not correct.
            le = LinkExtractor(restrict_css="#pagnNextLink")
            links = le.extract_links(response)
            if links:
                next_url = links[0].url
                #time.sleep(1)
                return scrapy.Request(next_url, callback=self.parse)

    def parse_1(self, response):
        page = 1
        varies = [
            "/div/div/div/div[2]/div[2]/div[1]/a",
            "/div/div[2]/div/div[2]/div[1]/div[1]/a",
            "/div/div/div/div[2]/div[1]/div[1]/a"
        ]
        for i in range(0, 22):
            amz = Amazon()
            amz['PageIndex'] = 1
            for r in varies:
                regex = '//*[@id="result_' + str(i) + '"]'
                regex += r
                attr = response.xpath(regex).attrib
                if attr.__len__() != 0:
                    break
            if attr.__len__() == 0:
                continue
            if 'title' in attr:
                amz["Title"] = attr["title"]
            if 'href' in attr:
                amz["Href"] = attr["href"]

            if amz["Href"] != "":
                amz['KeyWords'] = "a"
                amz["Href"].split('/dp/')
                amz['TargetKey'] = ""
                amz['MatchWords'] = ""
                amz['CurrentPageRank'] = i
                amz['TotalPageRank'] = i * page
                self.items.append(amz)
        le = LinkExtractor(restrict_css="#pagnNextLink")
        links = le.extract_links(response)
        if links:
            next_url = links[0].url
            # todo delay a period of time.
            time.sleep(1)
            return scrapy.Request(next_url, callback=self.parse)
        return self.items
