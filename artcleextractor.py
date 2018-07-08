# -*- coding: utf-8 -*-
import re

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

    def get_article(self, text, url):
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
            

if __name__ == '__main__':

    import requests

    def downHtml(url, encoding='utf-8'):
        http = requests.Session()
        r = http.get(url)
        return r.content.decode(encoding)

    ext = ArticleExtractor()
    url = 'http://www.bjnews.com.cn/news/2018/05/23/488032.html'
    text = downHtml(url)
    title, content = ext.get_article(text, url)
    print 'title:', title
    print 'content:', content


















