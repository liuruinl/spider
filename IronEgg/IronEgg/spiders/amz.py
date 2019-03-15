import scrapy
from scrapy import Spider, Request
from scrapy.linkextractors import LinkExtractor
from IronEgg.items import Amazon
import pymongo
import re
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
        fake_url = "https://www.a.com/"
        if sets.DEBUG:
            start_urls = [
                fake_url + 'python '
            ]
            for url in start_urls:
                yield Request(url=url, callback=self.parse, meta={'first_page': True, 'words': 'python'})
        else:
            collection = self.db["words"]
            for doc in collection.find({"owner": 1}):
                yield Request(url=fake_url + doc["keys"], callback=self.parse,
                              meta={'first_page': True, 'words': doc["keys"]})

    def parse(self, response):
        self.logger.info("amz.parse.start")
        if response is None:
            return
        if response.status != 200:
            return
        try:
            if sets.PARSE_V == 1:
                lis = response.css("div #atfResults").css("#s-results-list-atf").css('li')
                self.logger.info("li.len %s" % lis.__len__())
                if lis.__len__() > 0:
                    page = response.css("div #pagn span.pagnCur").xpath('text()').extract()
                    current_page_rank = 1
                    for li in lis:
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
                            self.logger.critical("cant not get PageIndex.")
                        current_page_rank += 1
                    if page.__len__() > 0 and int(page[0]) < sets.TOTAL_PAGE:
                        le = LinkExtractor(restrict_css="#pagnNextLink")
                        links = le.extract_links(response)
                        if links:
                            yield scrapy.Request(links[0].url, callback=self.parse, dont_filter=True,
                                                 meta={'first_page': False, 'words': response.meta['words'], 'referer': response.url, 'proxy': response.meta['proxy'], 'browser': response.meta['browser']})
                else:
                    yield scrapy.Request(str(response.url), callback=self.parse, dont_filter=True, meta={'first_page': False, 'words': response.meta['words']})
            if sets.PARSE_V == 2:
                divs = response.css("div[data-index]")
                self.logger.info("divs.len %s" % divs.__len__())
                if divs.__len__() > 0:
                    for div in divs:
                        amz = Amazon()
                        amz["RequestUrl"] = str(response.url)  # 请求URL
                        amz["SearchWords"] = response.meta['words']  #
                        amz["ASIN"] = div.attrib['data-asin']  # ASIN
                        amz["TotalRank"] = int(div.attrib['data-index']) + 1  # 总排名
                        amz["CurrentPageRank"] = div.attrib['data-index']
                        amz["IsAd"] = False
                        if div.attrib['class'] is not None and div.attrib['class'] != "" and str(div.attrib['class']).find("AdHolder") >= 0:
                            amz["IsAd"] = True
                        amz["PageIndex"] = re.findall(r"&page=(.+?)&", response.url)[0]
                    if response.css("li.a-last a") and amz["PageIndex"] < sets.TOTAL_PAGE:  # having next page
                        yield scrapy.Request(response.css("li.a-last a").attrib['href'], callback=self.parse, dont_filter=True,
                                             meta={'first_page': False, 'words': response.meta['words'], 'referer': response.url, 'proxy': response.meta['proxy'], 'browser': response.meta['browser']})
                    else:
                        yield scrapy.Request(str(response.url), callback=self.parse, dont_filter=True, meta={'first_page': False, 'words': response.meta['words']})
                else:
                    yield scrapy.Request(str(response.url), callback=self.parse, dont_filter=True, meta={'first_page': False, 'words': response.meta['words']})

        except Exception as e:
            self.logger.critical(e)
