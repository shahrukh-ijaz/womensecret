# -*- coding: utf-8 -*-
import scrapy
import re
import json
from scrapy.http import HtmlResponse


class WomenSecretSpider(scrapy.Spider):
    name = 'task'
    allowed_domains = ['womensecret.com']
    start_urls = ['https://womensecret.com']

    def parse(self, response):
        for category in response.css("nav ul.menu-category li.c03__item--level-1"):
            next_page = category.css("a::attr(href)").extract_first()
            if next_page != 'https://womensecret.com/es/es/editorial':
                yield response.follow(next_page, callback=self.category_parse)

    def category_parse(self, response):
        products = response.css("ul#search-result-items li.grid__unit.s-1-2.l-1-3.grid-tile.new-row")
        for product in products:
            product_url = product.css("div.product-image > a::attr(href)").extract_first()
            skus = list()
            yield response.follow(product_url, callback=self.product_parse, meta={'skus': skus})

    def product_parse(self, response):
        item_data = json.loads(re.findall('window.universal_variable.product = (.+);', response.text)[0])
        data = dict(
            retailer_sku=item_data.get('sku_code'),
            gender=item_data.get('gender'),
            name=item_data.get('name'),
            url=item_data.get('url'),
            category=item_data.get('category'),
            subcategory=item_data.get('subcategory'),
            description=response.css('.c02__product-description::text').extract_first(),
            images=response.css('.c02__colors > dataimages > dataimage::attr(data-image-small)').extract()
            )
        skus = list()
        for size in response.css('input.attrSelectedSizeValue::attr(value)').extract():
            for color in response.css('ul.swatches.c02__swatch-list > li > a::attr(title)').extract():
                skus.append(
                    dict(
                        size=size,
                        color=color,
                        price=item_data.get('unit_price'),
                        sale_price=item_data.get('unit_sale_price'),
                        currency=item_data.get('currency')
                    )
                )
        html_data = HtmlResponse(url="Twitter Response", body=data['items_html'], encoding='utf-8')

        data['skus'] = skus
        yield data
