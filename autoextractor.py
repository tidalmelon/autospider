# -*- coding: utf-8 -*-

import re
import requests as rq
from urlparse import urljoin
from lxml import etree

import htmlutil

class ListUrlExtractor(object):
    
    def __init__(self):
        self.features = set([u'下一页', u'上一页'])

    def get_list_urls(self, dom, url):
        links = htmlutil.getlinks(dom, "//a", url)
        #print 'a tag num: ', len(links)

        outlinks = {}
        if links:
            for link, anchor in links:
                if anchor in self.features:
                    outlinks[link] = (link, anchor)
                    continue

                sim_val = self.__urlsim(url, link)
                #print url, link, sim_val, anchor
                if sim_val > 0.90:
                    outlinks[link] = (link, anchor)

        return outlinks.values()

    def __urlsim(self, s1, s2):   
        # 可替换为其他算法
        m = [[0 for x in range(len(s2)+1)] for y in range(len(s1)+1)]   
        d = [[None for x in range(len(s2)+1)] for y in range(len(s1)+1)]   
  
        for p1 in range(len(s1)):   
            for p2 in range(len(s2)):   
                if s1[p1] == s2[p2]:
                    m[p1+1][p2+1] = m[p1][p2]+1  
                    d[p1+1][p2+1] = 'ok'            
                elif m[p1+1][p2] > m[p1][p2+1]:
                    m[p1+1][p2+1] = m[p1+1][p2]   
                    d[p1+1][p2+1] = 'left'            
                else:
                    m[p1+1][p2+1] = m[p1][p2+1]     
                    d[p1+1][p2+1] = 'up'           
        (p1, p2) = (len(s1), len(s2))   
        s = []   
        while m[p1][p2]:
            c = d[p1][p2]  
            if c == 'ok':
                s.append(s1[p1-1])  
                p1-=1  
                p2-=1   
            if c =='left':
                p2 -= 1  
            if c == 'up':     
                p1 -= 1  
        val = len(s) / float(len(s1))
        return val


class DetailUrlExtractor(object):

    def __init__(self):
        self.sess = rq.Session()
        self.find_zh = re.compile(u'[\u4e00-\u9fa5]').findall
        self.find_zh_en = re.compile(u'[a-zA-Z\d_\u4e00-\u9fa5]').findall

    def get_detail_urls(self, dom, url, standard_contents):
        self.url = url
        if dom is None:
            dom = self.__create_dom(url)
        content = self.__traverse_dom(dom)[1]
        content_ = []
        for c in content:
            if c[1:3] not in standard_contents:
                content_.append(list(c))
        content_ = self.__filter(content_)

        content_ = [(e[3], e[2]) for e in content_]

        return content_

    def train_model_seed(self, seed, encoding='utf-8'):
        le = ListUrlExtractor()
        http = rq.Session()

        r = http.get(seed)
        dom = htmlutil.create_dom(r.content.decode(encoding))
        outlinks = le.get_list_urls(dom, seed)
        for link, anchor in outlinks:
            print 'train model: ', link, anchor
        standard_urls = [outlink[0] for outlink in outlinks]

        standard_urls = standard_urls[0:2] if len(standard_urls) > 5 else standard_urls

        return self.train_model(standard_urls)
        

    def train_model(self, standard_urls):
        standard_contents = []
        if isinstance(standard_urls, list):
            self.url = standard_urls[0]
            standard_dom = self.__create_dom(standard_urls[0])
            standard_contents = set([c[1:3] for c in self.__traverse_dom(standard_dom)[1]])
            for url in standard_urls[1:]:
                standard_dom = self.__create_dom(url)
                standard_contents = standard_contents & set([c[1:3] for c in self.__traverse_dom(standard_dom)[1]])
        else:
            self.url = standard_urls
            standard_dom = self.__create_dom(standard_urls)
            standard_contents = set([c[1:3] for c in self.__traverse_dom(standard_dom)[1]])
        return set(standard_contents)

    def __filter(self, content_):
        content = []
        # zh rate > 4
        for c in content_:
            # magic num
            if len(self.find_zh_en(c[2])) > 4:
                content.append(c)
        # other extensions
        return content

    def __create_dom(self, url):
        r = self.sess.get(url)
        content = htmlutil.movecomment(r.content)
        return etree.HTML(content)

    def __traverse_dom(self, dom, idx=0, tag=''):
        content = []

        tagname = dom.tag
        tag += (tagname+'_')
        idx += 1

        if tagname == 'a' or tagname == 'A':
            anchor = dom.xpath('.//text()')
            href = dom.xpath('./@href')
            if href:
                href = href[0]
                href = urljoin(self.url, href)
                anchor = ''.join(anchor)
            else:
                href = ''
                anchor = ''

            #txt = htmlutil.gettext(dom, ".//text()")
            #if txt is None:
            #    txt = ''
            content.append((idx, tag, anchor, href))

        for d in dom:
            idx, content_ = self.__traverse_dom(d, idx, tag)
            content.extend(content_)
        return idx, content


class ArticleExtractor(object):

    def __init__(self):
        self.pat_href = re.compile(r'<a.*?href=.*?>', re.IGNORECASE) #去掉a标签低前半部分
        self.pat_comment = re.compile(r'<!--[\s\S]*?-->', re.IGNORECASE)
        self.pat_script = re.compile(r'<script.*?>[\s\S]*?</script>', re.IGNORECASE)
        self.pat_style = re.compile(r'<style.*?>[\s\S]*?</style>', re.IGNORECASE)
        self.pat_alltag = re.compile(r'<[\s\S]*?>', re.IGNORECASE)
        self.pat_img = re.compile(r'http:.*?(jpg|png|jpeg|JPEG)', re.IGNORECASE)

        self.pat_content = re.compile(r'\W')

        self.pat_title = re.compile(r'<title>(.*?)</title>', re.IGNORECASE)

    def clean_html(self, text):
        text = self.pat_href.sub('*', text)
        text = self.pat_comment.sub('', text)
        text = self.pat_script.sub('', text)
        text = self.pat_style.sub('', text)
        text = self.pat_alltag.sub('', text)
        text = self.pat_img.sub('', text)
        text = text.replace('\t', '').replace('&nbsp;', '').replace(' ', '')
        return text

    def get_article(self, text):
        self.title = ''
        self.content = ''

        def get_title(input):
            match = self.pat_title.search(input)
            if match:
                return match.group(1)
            return ''

        self.title = get_title(text)
        content = ''
        text = self.clean_html(text)

        lines = text.split('\n')
        article = []
        for i, line in enumerate(lines):
            #print i, line
            if len(line) > 120 and len(self.pat_content.findall(line)) / len(line) < 0.2:
                article.append(i)

        begin = end = 0

        if (len(article)) == 0:
            self.text = ''
            return '', ''
        elif len(article) == 1:
            begin = end = article[0]
        else:
            article.sort()
            begin = article[0]
            end = article[1]

        while True:
            if begin <= 2:
                break
            else:
                if lines[begin-1] == '':
                    if lines[begin-2] == '':
                        break
                    else:
                        if not self.is_adv(lines[begin -2]):
                            begin -= 2
                        else:
                            break
                else:
                    if self.is_adv(lines[begin-1]):
                        break
                    else:
                        begin -= 1

        while True:
            if end >= len(lines) - 2:
                break
            else:
                if lines[end+1] == '':
                    if lines[end+2] == '':
                        break
                    else:
                        if not self.is_adv(lines[end+2]):
                            end += 2
                        else:
                            break
                else:
                    if self.is_adv(lines[end+1]):
                        break
                    else:
                        end += 1

        for k in range(begin, end+1):
            # 转义字符参考：https://www.cnblogs.com/knowledgesea/archive/2013/07/24/3210703.html
            # todo: html to text
            txt = lines[k].replace(u'&ldquo;', u'“').replace(u'&rdquo;', u'”').replace(u'&quot;', u'“')
            if txt.count('*') > 5 or len(txt) < 10:
                if len(txt) < 10:
                    pass
                else:
                    issues = txt.split('*')
                    for issue in issues:
                        if len(issue) > 20:
                            self.content += issue + '\n'
            else:
                self.content += txt.replace('*', '') + '\n'

        if self.content != '':
            return self.title, self.content

    def is_adv(self, line):
        if len(line) > 40:
            return False
        else:
            if line == '':
                return False
            else:
                if '*' in line[:6] or len(line) < 4:
                    return True
                else:
                    return False
            


#########test code#########

def article_extractor_test():
    def downHtml(url, encoding='utf-8'):
        http = rq.Session()
        r = http.get(url)
        return r.content.decode(encoding)

    ext = ArticleExtractor()
    url = 'http://www.bjnews.com.cn/news/2018/05/23/488032.html'
    text = downHtml(url)
    title, content = ext.get_article(text)
    print 'title:', title
    print 'content:', content

def auto_list_urls_test():
    le = ListUrlExtractor()
    http = rq.Session()

    seed = 'http://bi.dataguru.cn/index.php?page=1'
    seed = 'http://www.bjnews.com.cn/news/?page=1'

    r = http.get(seed)
    dom = htmlutil.create_dom(r.content)
    outlinks = le.get_list_urls(dom, seed)
    if outlinks:
        for link, anchor in outlinks:
            print link, anchor

def auto_detail_urls_test():
    de = DetailUrlExtractor()

    # 列表页识别
    urls = []
    urls.append('http://www.bjnews.com.cn/news/?page=1')
    urls.append('http://www.bjnews.com.cn/news/?page=2')
    urls.append('http://www.bjnews.com.cn/news/?page=3')
    urls.append('http://www.bjnews.com.cn/news/?page=4')
    urls.append('http://www.bjnews.com.cn/news/?page=5')
    #standard_contents = de.train_model(urls)
    standard_contents = de.train_model_seed(urls[0])

    ll = de.get_detail_urls(None, 'http://www.bjnews.com.cn/news/?page=6', standard_contents)
    for x, y in ll:
        print x, y
    


if __name__ == '__main__':

    #auto_list_urls_test()
    #auto_detail_urls_test()
    article_extractor_test()










