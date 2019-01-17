import scrapy
from scrapy import Spider, Request
from scrapy.linkextractors import LinkExtractor
from IronEgg.items import Amazon
import pymongo
import urllib

class AmzSpider(Spider):
    name = 'amz'
    allowed_domains = ['www.amazon.com']
    DB_URI = 'mongodb://liurui:rootroot@172.17.0.2:27017/scrapydata'
    DB_NAME = 'scrapydata'
    
    def __init__(self):
        self.logger.info("amz.init.start")
        self.browser = {}
        self.client = pymongo.MongoClient(self.DB_URI)
        self.db = self.client[self.DB_NAME]
        # todo read base-url from db
        self.base_url = "https://www.amazon.com/s/ref=nb_sb_noss_1?url=search-alias%3Daps&field-keywords="
        self.items = []
        self.logger.info("amz.init.end")
    
    def start_requests(self):
        self.logger.info("amz.start_requests.start")
        collection = self.db["words"]
        start_urls = [
            # 'https://www.amazon.com/s/ref=nb_sb_noss_2?url=search-alias%3Daps&field-keywords=net%20core%20in%20action'
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            # "http://httpbin.org/user-agent",
            #"https://www.liuruinl.com",
            "https://www.amazon.com/s?k=a&ref=nb_sb_noss"
        ]
        # for doc in collection.find({"owner": 1}):
        #     yield Request(url=self.base_url + doc["keys"], callback=self.parse)  # meta={"id": doc["_id"]}
        for url in start_urls:
            yield Request(url=url, callback=self.parse)
    
    def parse(self, response):
        self.logger.info("amz.parse.start")
        if response is None:
            return
        if response.status != 200:
            return
        #print(response.xpath("/html/body/pre/text()").extract()[0])
        ul = response.css("div #atfResults").css("#s-results-list-atf").css("li")
        self.logger.info("ul.len %s" % ul.__len__())
        if ul.__len__() > 0:
            page = response.css("div #pagn span.pagnCur").xpath('text()').extract()
            for li in ul.css('li'):
                if li.attrib.__len__() > 0 and 'data-asin' in li.attrib:
                    amz = Amazon()
                    amz["RequestUrl"] = str(response.url)  # 请求URL
                    amz["SearchWords"] = urllib.parse.unquote(str(response.url).replace(self.base_url, ""))  # 搜索关键词
                    amz["ASIN"] = li.attrib['data-asin']  # ASIN
                    amz["TotalIndex"] = li.attrib['id']  # 总排名
                    amz["IsAd"] = False
                    if li.attrib['class'] is not None and li.attrib['class'] != "" and str(li.attrib['class']).find(
                            "AdHolder") >= 0:
                        amz["IsAd"] = True
                    if page.__len__() > 0:
                        amz["PageIndex"] = page[0]  # 当前页索引
                        yield amz
                    else:
                        self.logger.critical("cant find any page, nothing returned !!!")
                else:
                    self.logger.warning("li.attrib.len is 0")
            if page.__len__() > 0 and int(page[0]) < 1:  # 只取20页
                le = LinkExtractor(restrict_css="#pagnNextLink")
                links = le.extract_links(response)
                if links:
                    next_url = links[0].url
                    # time.sleep(1)
                    yield scrapy.Request(next_url, callback=self.parse, dont_filter=True)
                else:
                    self.browser.quit()
        else:
            self.logger.critical("ul.len is %s !!!" % ul.css('li').__len__())
