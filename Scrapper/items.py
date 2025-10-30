# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScraperItem(scrapy.Item):
    url = scrapy.Field()
    product_name = scrapy.Field()
    brand = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    discount_price = scrapy.Field()
    discount_percentage = scrapy.Field()
    storage = scrapy.Field()
    rating = scrapy.Field()
    in_stock = scrapy.Field()
    site_name = scrapy.Field()
    image_url = scrapy.Field()
    timestamp = scrapy.Field()
