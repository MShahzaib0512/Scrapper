import scrapy
import re
import json
from datetime import datetime


class MegaMobilesSpider(scrapy.Spider):
    name = "mega_mobiles"
    allowed_domains = ["mega.pk"]
    start_urls = ["https://www.mega.pk/mobiles/"]

    def parse(self, response):
        """Parse the main mobiles page and go to each brand page."""
        brand_links = response.xpath('//div[@class="brand-logos shadow-mega-sm"]/a/@href').getall()
        for link in brand_links:
            yield response.follow(link, callback=self.parse_brand)

    def parse_brand(self, response):
        """Parse brand page and visit each product page."""
        product_links = response.xpath('//div[@class="mega-product-image"]/a/@href').getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_product)

        # Handle pagination if available
        next_page = response.xpath('//a[contains(text(), "Next")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_brand)

    def parse_product(self, response):
        """Extract all product info: model, brand, price, RAM, storage, and rating."""
        model = response.xpath('//h2[@class="product-title"]/text()').get()
        if not model:
            return

        brand = response.xpath('//ul[@class="breadcrumb product-navBar"]/li/a/text()').getall()[-1]
        price = response.xpath('//span[@id="price"]/text()').get()

        # --- Extract from model name first ---
        ram_pattern = r'(\d+\s?GB)\s*RAM'
        storage_pattern = r'(\d+\s?(?:GB|TB))\s*(?:Storage|STORAGE)'

        ram_match = re.search(ram_pattern, model, re.IGNORECASE)
        storage_match = re.search(storage_pattern, model, re.IGNORECASE)

        ram = ram_match.group(1) if ram_match else None
        storage = storage_match.group(1) if storage_match else None

        # --- Fallback: extract from <p> specs if missing ---
        if not ram or not storage:
            desc_html = response.xpath('//p[@class="item_desc text-justify margint-20"]').get()
            if desc_html:
                desc_text = re.sub(r'<[^>]+>', '', desc_html)
                desc_text = re.sub(r'\s+', ' ', desc_text).strip()

                if not ram:
                    ram_match = re.search(r'RAM[:\s]*([0-9]+ ?GB)', desc_text, re.IGNORECASE)
                    ram = ram_match.group(1) if ram_match else None

                if not storage:
                    storage_match = re.search(r'Storage[:\s]*([0-9]+ ?(?:GB|TB))', desc_text, re.IGNORECASE)
                    storage = storage_match.group(1) if storage_match else None

        # --- Extract Rating from JSON-LD ---
        rating_value = None
        json_ld_list = response.xpath('//script[@type="application/ld+json"]/text()').getall()

        for json_text in json_ld_list:
            try:
                data = json.loads(json_text.strip())
                if isinstance(data, dict) and data.get("@type") == "Product":
                    rating = data.get("aggregateRating", {})
                    rating_value = rating.get("ratingValue")
                    break  # found what we need
            except Exception:
                continue  # skip invalid JSON

        # --- Clean and yield ---
        model_clean = re.sub(r'\s+', ' ', model.strip())
        imgage_url = response.xpath('//img[@class="img-responsive stats padding-10 center-block"]/@src').get()
        in_stock = response.xpath(
            '//div[@class="stock-detail"]/span[contains(text(),"Stock Info")]/following-sibling::text()[1]').get()
        if in_stock:
            in_stock = in_stock.strip()


        yield {
            "brand": brand.strip() if brand else None,
            "product_name": model_clean,
            "ram": ram,
            "storage": storage,
            "price": price.strip() if price else None,
            "rating": rating_value,
            "in_Stock" : in_stock,
            "url": response.url,
            "image_url": imgage_url,
            "site_name" : self.name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
