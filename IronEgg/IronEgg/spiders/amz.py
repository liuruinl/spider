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
    allowed_domains = ['www.amazon.com']
    DB_URI = 'mongodb://liurui:rootroot@172.17.0.3:27017/admin'
    DB_NAME = 'scrapydata'
    
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')

        # p_r_o_x_y = "23.23.23.23:3128"  # IP:PORT or HOST:PORT
        # chrome_options.add_argument('--proxy-server=http://%s' % p_r_o_x_y)
        
        self.browser = webdriver.Chrome(chrome_options=chrome_options)
        self.browser.set_page_load_timeout(120)
        
        
        self.client = pymongo.MongoClient(self.DB_URI)
        self.db = self.client[self.DB_NAME]
        self.base_url = "https://www.amazon.com/s/ref=nb_sb_noss_1?url=search-alias%3Daps&field-keywords="
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
            # page = response.xpath('//*[@id="pagn"]/span[2]/text()').extract()
            page = response.css("div #pagn span.pagnCur").xpath('text()').extract()
            for li in ul.css('li'):
                if li.attrib.__len__() > 0 and 'data-asin' in li.attrib:
                    amz = Amazon()
                    amz["RequestUrl"] = str(response.url)  # 请求URL
                    amz["SearchWords"] = str(response.url).replace(self.base_url, "")  # 搜索关键词
                    amz["ASIN"] = li.attrib['data-asin']  # ASIN
                    amz["TotalIndex"] = li.attrib['id']  # 总排名
                    amz["IsAd"] = False
                    if li.attrib['class'] is not None and li.attrib['class'] != "" and str(li.attrib['class']).find(
                            "AdHolder") >= 0:
                        amz["IsAd"] = True
                    if page.__len__() > 0:
                        amz["PageIndex"] = page[0]  # 当前页索引
                        yield amz
            if page.__len__() > 0 and int(page[0]) < 1:  # 只取20页
                le = LinkExtractor(restrict_css="#pagnNextLink")
                links = le.extract_links(response)
                if links:
                    next_url = links[0].url
                    # time.sleep(1)
                    yield scrapy.Request(next_url, callback=self.parse, dont_filter=True)
    
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
