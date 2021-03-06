# -*- coding: utf-8 -*-

import scrapy 
from scrapy.http import FormRequest
from lxml import etree
import house.common.htmlutil as htmlutil
import random

from house.common.autoextractor import ListUrlExtractor, DetailUrlExtractor, ArticleExtractor

class NewsSpider(scrapy.Spider):

    name = 'news'

    start_urls = ['http://www.bjnews.com.cn/news/?page=1']

    def __init__(self):
        # 自动翻页 
        self.listurlextractor = ListUrlExtractor()
        # 自动发现详情页
        self.detailextractor = DetailUrlExtractor()
        # 正文抽取
        self.articleextractor = ArticleExtractor()

        #  , then mapping
        seed = 'http://www.bjnews.com.cn/news/?page=1'
        # 训练模型
        self.model = self.detailextractor.train_model_seed(seed, "utf-8")
        print 'train model success'

    def parse(self, response):
        dom = htmlutil.create_dom(response.body.decode('utf-8'))
        outlinks = self.listurlextractor.get_list_urls(dom, response.url)
        for link, anchor in outlinks:
            print 'index url:', link, anchor
            yield FormRequest(url=link, callback=self.parse)

        outlinks = self.detailextractor.get_detail_urls(dom, response.url, self.model)
        for link, anchor in outlinks:
            print 'extract detail url:', link, anchor
            yield FormRequest(url=link, callback=self.parse_detail, meta={'anchor': anchor})

    def parse_detail(self, response):
        anchor = response.meta.get('anchor', '')

        txt = response.body.decode("utf-8")
        title, content = self.articleextractor.get_article(txt)
        
        item = {}
        item['title'] = title
        item['anchor'] = anchor
        item['article'] = content
        yield item


