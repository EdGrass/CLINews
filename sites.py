interests = {
    "hkn": {
        "url": "https://news.ycombinator.com/rss",
        "desc": "Hacker News"
    },
    "bbc": {
        "url": "http://feeds.bbci.co.uk/news/rss.xml", 
        "desc": "BBC News"
    },
    "zhd": {
        "url": "http://feeds.feedburner.com/zhihu-daily",
        "desc": "Zhihu Daily",
    },
    "zhc": {
        "url": "http://www.zhihu.com/rss",
        "desc": "Zhihu Choosen",
        "headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        },
        "strip_url_parameters": False,
        "use_mobile": True
    },
    "yys": {
        "url": "http://www.yystv.cn/rss/feed",
        "desc": "Youyan She"
    },
    "shb": {
        "url": "https://feedx.net/rss/shanghaishuping.xml",
        "desc": "Shanghai Book"
    },
    "sc": {
        "url": "https://www.scmp.com/rss/91/feed",
        "desc": "South China Morning Post"
    },
}

try:
    from local_sites import *
except ImportError:
    pass
