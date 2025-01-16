# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FlycamScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class flycamItem(scrapy.Item):
    url = scrapy.Field()
    name = scrapy.Field()
    new_price = scrapy.Field()
    old_price = scrapy.Field()