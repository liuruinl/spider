# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class IronEggItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Amazon(scrapy.Item):
    _id = scrapy.Field()
    RequestUrl = scrapy.Field()  # 请求URL
    SearchWords = scrapy.Field()  # 搜索关键词
    
    PageIndex = scrapy.Field()  # 当前页索引
    CurrentPageRank = scrapy.Field()  # 当前页面排名
    TotalIndex = scrapy.Field()
    TotalRank = scrapy.Field()  # 总排名
    ASIN = scrapy.Field()  # 查找目标
    IsAd = scrapy.Field()  # 是否广告
    
    AddTime = scrapy.Field()  #
