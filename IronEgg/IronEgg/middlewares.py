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
from selenium import webdriver
import random
import IronEgg.settings as sets

class SeleniumMiddleware(object):
    @staticmethod
    def process_request(request, spider):
        driver = 1
        try:
            driver = SeleniumMiddleware.get_chrome(request, spider)
            if driver is None:
                return request
            current_url = request.url
            if request.meta["first_page"]:
                driver.get("https://www.amazon.com")
                if driver.page_source == sets.BLANK_PAGE:
                    driver.quit()
                    SeleniumMiddleware.clear_request_meta(request)
                    return request
                elem = driver.find_element_by_id('twotabsearchtextbox')
                elem.send_keys(request.meta["words"])
                driver.find_element_by_class_name('nav-input').click()
                driver.refresh()
                current_url = driver.current_url
            else:
                driver.get(request.url)
                if driver.page_source == sets.BLANK_PAGE:
                    driver.quit()
                    SeleniumMiddleware.clear_request_meta(request)
                    return request
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            content = driver.page_source.encode('utf-8')
            if not sets.USE_THE_SAME_BROWSER:
                driver.quit()
        except Exception as e:
            spider.logger.critical(e)
            if driver is not None and driver != 1:
                driver.quit()
                SeleniumMiddleware.clear_request_meta(request)
            return request
        return HtmlResponse(current_url, encoding='utf-8', body=content, request=request)
    
    @staticmethod
    def get_chrome(request, spider):
        
        if sets.USE_THE_SAME_BROWSER and 'browser' in request.meta and request.meta['browser'] is not None:
            return request.meta['browser']
        
        opts = webdriver.ChromeOptions()
        if sets.USE_PROXY:
            if 'proxy' in request.meta and request.meta['proxy'] is not None:
                random_proxy = request.meta['proxy']
            else:
                cursor = spider.db["proxies"].find({"active": {"$gt": 0}}).limit(sets.PULL_FROM_DB_COUNT)
                random_proxy = random.choice([c for c in cursor])["addr"]
            opts.add_argument('--proxy-server=http://%s' % random_proxy)
            request.meta['proxy'] = random_proxy
        
        opts.add_argument('--headless')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--incognito')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--ignore-certificate-errors')
        opts.add_argument('blink-settings=imagesEnabled=false')
        # 1 allow all pic；2 disable all pic；3 disable third parts pic
        opts.add_experimental_option('prefs', {'profile.default_content_setting_values': {'images': 2}})
        opts.add_argument('user-agent=%s' % random.choice(sets.AGENTS_ALL))
        driver = webdriver.Chrome(chrome_options=opts)
        driver.set_page_load_timeout(180)
        
        request.meta['browser'] = driver
        return driver
    
    @staticmethod
    def clear_request_meta(request):
        request.meta['proxy'] = None
        request.meta['browser'] = None

from scrapy.dupefilter import RFPDupeFilter

class CloseDupeFilter(RFPDupeFilter):
    def request_seen(self, request):
        return False

# from scrapy.contrib.downloadermiddleware.retry import RetryMiddleware

# class CustomRetryMiddleware(RetryMiddleware):
#    pass
