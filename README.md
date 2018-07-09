###  主要功能

#### 1, 详情页链接自动抽取   

自动发现详情页

#### 2, 索引页链接自动抽取    


自动翻页。  


#### 3. 正文抽取: 
    

    本文采用的是： 行块式分布函数（哈工大） 优点：无需加载为dom树，性能搞     
    常见的还有文字链接比。       
    或者混合自然语言的一些抽取算法。（例如，广告链接的判断）      


#### 4. 示例

```
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

```

