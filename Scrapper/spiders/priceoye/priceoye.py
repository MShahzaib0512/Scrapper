from datetime import datetime
from scrapy import Spider
import re
from Scrapper.items import ScraperItem

class PriceOyeSpider(Spider):
    name = "priceoye"
    allowed_domains = ["priceoye.pk"]
    start_urls = ["https://priceoye.pk/mobiles"]
    next_page_url = "https://priceoye.pk/mobiles?page={}"
    page_number = 2

    def parse(self, response):

        products = response.xpath('//div[@class="product-list"]/div[@class="productBox b-productBox"]')
        for product in products:
           detail_page_url = product.xpath('.//a/@href').get()

           yield response.follow(detail_page_url, self.parse_product)

        # Follow pagination links
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(self.next_page_url.format(self.page_number), self.parse)

    def parse_product(self, response):

        rating = response.xpath('//div[contains(@class,"rating-points")]/text()').get()
        raw_title = response.xpath('//div[@id="product-summary"]//h3/text()').get()
        discount_price = response.xpath('//span[contains(@class,"price-size-lg")]/span/text()').get()
        original_price = response.xpath('//div[contains(@class,"market-price")]//span/span/text()').get()
        stock_status = response.xpath('//span[contains(@class,"stock-status")]/text()').get()
        storage = response.xpath('//div[@class="product-variant"]/ul[@class="sizes colors"]//span[@class]/text()').get()
        image_url = response.xpath('//div[@class="product-color-image"]//img/@src').get()
        product_url = response.url

        # Cleaning
        rating = clean_text(rating)
        raw_title = clean_text(raw_title)
        stock_status = clean_text(stock_status)
        storage = clean_text(storage)

        discount_price = parse_price(discount_price)
        original_price = parse_price(original_price)
        brand, product_name = _get_brand_and_product(raw_title)

        # Normalize stock
        in_stock = stock_status and "in stock" in stock_status.lower()

        # Handle missing discount
        final_price = discount_price or original_price

        item = {
            "product_name": product_name,
            "brand": brand,
            "price": final_price,
            "original_price": original_price,
            "discount_price": discount_price,
            "discount_percentage": round(((original_price - discount_price) / original_price) * 100, 2)
                if (original_price and discount_price) else None,
            "storage": storage,
            "rating": rating,
            "in_stock": in_stock,
            "site_name": "PriceOye",
            "url": product_url,
            "image_url": image_url,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        yield ScraperItem(**item)


def parse_price(value):
    if not value:
        return None
    cleaned = re.sub(r"[^\d]", "", value)
    return int(cleaned) if cleaned else None

def clean_text(value):
    return value.strip() if value else None

def _get_brand_and_product(title):
    parts = title.strip().split()
    if not parts:
        return None, None
    brand = parts[0]
    product = " ".join(parts[1:]) if len(parts) > 1 else ""
    return brand, product
