import scrapy
from scrapy import Spider, Request
from scrapy.linkextractors import LinkExtractor
from IronEgg.items import Amazon
import pymongo

import IronEgg.settings as sets

class AmzSpider(Spider):
    name = 'amz'
    allowed_domains = ['www.amazon.com']
    DB_URI = sets.DB_URI
    DB_NAME = sets.DB_NAME
    
    def __init__(self):
        self.logger.info("amz.init.start")
        self.browser = {}
        self.client = pymongo.MongoClient(self.DB_URI)
        self.db = self.client[self.DB_NAME]
        # todo read base-url from db
        self.items = []
        self.logger.info("amz.init.end")
    
    def start_requests(self):
        self.logger.info("amz.start_requests.start")
        collection = self.db["words"]
        fake_url = "https://www.a.com/"
        start_urls = [
            'https://www.a.com/python '
        ]
        # for doc in collection.find({"owner": 1}):
        # yield Request(url=fake_url + doc["keys"], callback=self.parse, meta={'first_page': True, 'words': doc["keys"]})
        for url in start_urls:
            yield Request(url=url, callback=self.parse, meta={'first_page': True, 'words': 'python'})
    
    def parse(self, response):
        self.logger.info("amz.parse.start")
        if response is None:
            return
        if response.status != 200:
            return
        if sets.PARSE_V == 1:
            ul = response.css("div #atfResults").css("#s-results-list-atf")
            self.logger.info("ul.len %s" % ul.__len__())
            if ul.__len__() > 0:
                page = response.css("div #pagn span.pagnCur").xpath('text()').extract()
                current_page_rank = 1
                for li in ul.css('li'):
                    if li.attrib.__len__() > 0 and 'data-asin' in li.attrib:
                        amz = Amazon()
                        amz["RequestUrl"] = str(response.url)  # 请求URL
                        amz["SearchWords"] = response.meta['words']  # urllib.parse.unquote(str(response.url).replace(self.base_url, ""))  # 搜索关键词
                        amz["ASIN"] = li.attrib['data-asin']  # ASIN
                        amz["TotalIndex"] = li.attrib['id']  # 总排名
                        if amz["TotalIndex"].split('_'):
                            amz["TotalRank"] = int(amz["TotalIndex"].split('_')[1]) + 1
                        amz["CurrentPageRank"] = current_page_rank
                        amz["IsAd"] = False
                        if li.attrib['class'] is not None and li.attrib['class'] != "" and str(li.attrib['class']).find("AdHolder") >= 0:
                            amz["IsAd"] = True
                        if page.__len__() > 0:
                            amz["PageIndex"] = page[0]  # 当前页索引
                            yield amz
                        else:
                            self.logger.critical("cant find any page, nothing returned !!!")
                    else:
                        self.logger.warning("li.attrib.len is 0")
                    current_page_rank += 1
        
                if page.__len__() > 0 and int(page[0]) < sets.TOTAL_PAGE:
                    le = LinkExtractor(restrict_css="#pagnNextLink")
                    links = le.extract_links(response)
                    if links:
                        next_url = links[0].url
                        yield scrapy.Request(next_url, callback=self.parse, dont_filter=True,
                                             meta={'first_page': False,
                                                   'words': response.meta['words'],
                                                   'referer': response.url,
                                                   'proxy': response.meta['proxy'],
                                                   'browser': response.meta['browser']
                                                   })
            else:
                yield scrapy.Request(str(response.url), callback=self.parse, dont_filter=True,
                                     meta={'first_page': False,
                                           'words': response.meta['words'],
                                           # 'referer': response.url,
                                           # 'proxy': response.meta['proxy']
                                           })
        if sets.PARSE_V == 2:
            divs = response.css("div[data-index]")
            length = divs.__len__()
            self.logger.info("divs.len %s" % length)
            if length > 0:
                for div in divs:
                    if div.attrib.__len__() > 0 and 'data-asin' in div.attrib:
                        amz = Amazon()
                        amz["RequestUrl"] = str(response.url)  # 请求URL
                        amz["SearchWords"] = response.meta['words']  #
                        amz["ASIN"] = div.attrib['data-asin']  # ASIN
                        amz["TotalIndex"] = div.attrib['id']  # 总排名