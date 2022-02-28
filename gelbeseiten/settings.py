# -*- coding: utf-8 -*-

# Scrapy settings for gelbeseiten project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'gelbeseiten'

SPIDER_MODULES = ['gelbeseiten.spiders']
NEWSPIDER_MODULE = 'gelbeseiten.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30'

ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY =5

CONCURRENT_REQUESTS = 1
ITEM_PIPELINES = {
    'gelbeseiten.pipelines.gelbeseitenPipeline': 300,
}






FEED_EXPORT_ENCODING = 'utf-8'

