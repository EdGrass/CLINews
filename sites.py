#!/usr/bin/env python

"""
This is a convenience dict of feed urls and their short names (keys)
which can be used at the interactive prompt.

The feed dict values are themselves dicts, with a single required 'url'
attribute.

There are also optional, information settings that can be added or edited
as necessary:

'strip_url_parameters': by default, the parser will remove any parameters
from the urls found in the indvidual item links. If that is not desirable,
include this parameter and set it to False

'referrer': some sites won't allow access unless they see a referral
from a specific site (this is one way around the NY Times paywall,
for example), so define the referring url string here

'desc': this is a basic description string for the user menu (if it does
not exist, the url will be used instead)

Any valid rss feed will work here, and thanks to the folks at
http://rssitfor.me so too will any twitter account.

For example, to get the most recent tweets from @macaronicks as rss,
use this for the feed_url:	

http://rssitfor.me/getrss?name=macaronicks

Check out http://www.wired.com/magazine/2013/08/101signals/ for more
suggestions of what to put here.

"""

interests = {

    # k=short name
    # v=feed dict: { url,
    #                strip_url_parameters (default: True),
    #                referrer (default: None),
    #                desc (default: None) }

    # define all the feeds you normally read in
    # local_sites.py which is localized/private
    # configuration not part of this repo
    
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
