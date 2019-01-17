# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

class IroneggSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.
    
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s
    
    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.
        
        # Should return None or raise an exception.
        return None
    
    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.
        
        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i
    
    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.
        
        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass
    
    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.
        
        # Must return only requests (not items).
        for r in start_requests:
            yield r
    
    def spider_opened(self, spider):
        pass

class IroneggDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s
    
    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None
    
    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response
    
    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.
        
        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass
    
    def spider_opened(self, spider):
        pass

from scrapy.http import HtmlResponse
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import random
import requests as r
import IronEgg.settings as SETS

class SeleniumMiddleware(object):
    @staticmethod
    def process_request(request, spider):
        
        try:
            opts = webdriver.ChromeOptions()
            opts.add_argument('--headless')
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--disable-dev-shm-usage')
            opts.add_argument('--ignore-certificate-errors')
            # 1 allow all pic；2 disable all pic；3 disable third parts pic
            opts.add_experimental_option('prefs', {'profile.default_content_setting_values': {'images': 2}})
            agent = random.choice(SETS.AGENTS_ALL)
            opts.add_argument('user-agent=%s' % agent)
            # todo get proxy from db
            cursor = spider.db["proxies"].find({}).limit(SETS.PULL_FROM_DB_COUNT)
            proxies = []
            if cursor is not None:
                proxies = [c for c in cursor]
            proxy = random.choice(proxies)
            if proxies.__len__() <  SETS.FETCH_FROM_REMOTE_LIMIT_COUNT:
                spider.db["proxies"].insert_many([{'addr': i} for i in r.get(SETS.FETCH_PROXY_URL).json()])
            opts.add_argument('--proxy-server=http://%s' % proxy['addr'])
            driver = webdriver.Chrome(chrome_options=opts)
            driver.set_page_load_timeout(5)
            # driver.get("http://httpbin.org/ip")
            # print(driver.page_source)
            driver.get(request.url)
            status = 200
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            content = driver.page_source.encode('utf-8')
            driver.quit()
        except TimeoutException as e:
            spider.logger.error(e.msg + request.url)
            status = 504
            content = ""
            # spider.db["proxies"].remove_one()({"_id": proxy._id})
            spider.db["proxies_bak"].insert_one(proxy)
        except Exception as e:
            status = 500
            content = ""
            print(e)
        
        return HtmlResponse(request.url, encoding='utf-8', body=content, request=request, status=status)

from scrapy.dupefilter import RFPDupeFilter

class CloseDupeFilter(RFPDupeFilter):
    def request_seen(self, request):
        return False

# from scrapy.contrib.downloadermiddleware.retry import RetryMiddleware

# class CustomRetryMiddleware(RetryMiddleware):
#    pass


