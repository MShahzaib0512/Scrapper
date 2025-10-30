from scrapy import Spider
from datetime import datetime

class ShophiveSpider(Spider):
    name = "shophive"
    allowed_domains = ["shophive.com"]
    start_urls = ["https://www.shophive.com/mobile-phones"]

    def parse(self, response):
      brands = response.xpath('//ul[@id="categories-nav"]/li/ul/li')
      for brand in brands:
            brand_name = brand.xpath('.//a//text()').get()
            brand_url = brand.xpath('.//a/@href').get()
            yield response.follow(brand_url, self.parse_brand, meta={'brand': brand_name})

    def parse_brand(self, response):
        brand = response.meta['brand']
        products_url = response.xpath('//li[contains(@class,"item product product-item")]/div/div/a')
        for url in products_url:
            products_url = url.xpath('.//@href').get()
            if 'mobile-accessories' not in products_url:
              yield response.follow(products_url, self.parse_product, meta={'brand': brand})

        next_page = response.xpath('//a[@class="next"]/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse_brand, meta={'brand': brand})

    def parse_product(self, response):
        brand = response.meta['brand']
        raw_title = response.xpath('//span[@class="base"]/text()').get()
        orignal_price = response.xpath('//span[@data-price-type="finalPrice"]/@data-price-amount').get()
        image_url = response.xpath(f'//img[@alt="{raw_title}"]/@src').get()
        is_available = response.xpath('//div[@title="Availability"]').get()
        site_name = "Shophive"
        url = response.url
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not all([brand, raw_title, orignal_price, url]):
            missing_fields = [field for field, value in {
                'brand': brand,
                'product_name': raw_title,
                'orignal_price': orignal_price,
                'url': url
            }.items() if not value]
            self.logger.warning(f"Missing data for product at {url}. Skipping item. Missing fields: {', '.join(missing_fields)}")
            return

        product_name, storage = self._get_product_name_and_storage(raw_title, brand)

        yield {
            'brand': brand,
            'product_name': product_name,
            'price': orignal_price,
            'image_url': image_url,
            'in_stock': bool(is_available),
            'site_name': site_name,
            'url': url,
            'storage': storage,
            'timestamp': timestamp
        }

    def _get_product_name_and_storage(self, raw_title, brand):
        title_parts = raw_title.split()
        storage = None
        product_name_parts = []

        for part in title_parts:
            if any(unit in part for unit in ['GB', 'TB', 'MB']):
                storage = part
            else:
                product_name_parts.append(part)

        product_name = ' '.join(product_name_parts).replace(brand, '').strip()
        return product_name, storage