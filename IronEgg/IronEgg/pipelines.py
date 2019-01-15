# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import datetime
import logging

class IronEggPipeline(object):
    # DB_URI = 'mongodb://liurui:rootroot@172.17.0.2:27017/admin'
    # DB_NAME = 'scrapydata'

    def __init__(self):
        # self.client = pymongo.MongoClient(self.DB_URI)
        # self.db = self.client[self.DB_NAME]
        pass

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        #self.client.close()
        pass

    def process_item(self, item, spider):
        logging.info("pipelines.process_item")
        collection = spider.db[spider.name]
        try:
            item["AddTime"] = datetime.datetime.utcnow()
            collection.insert_one(item)
        except BaseException as e:
            print(e)

        return item
