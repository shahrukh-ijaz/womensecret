import scrapy
import re
import json


class WomenSecretSpider(scrapy.Spider):
    name = 'task'
    refer = ''
    allowed_domains = ['womensecret.com']
    start_urls = ['https://womensecret.com/']
    headers = {
        'accept': 'text/html, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/74.0.3729.131 Safari/537.36',
        'X-Twitter-Active-User': 'yes',
        'x-requested-with': 'XMLHttpRequest',
        'Accept-Language': 'en-US',
        'method': 'get',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'scheme': 'https',
        'referer': refer
    }

    def parse(self, response):
        for category in response.css("nav ul.menu-category li.c03__item--level-1"):
            next_page = category.css("a::attr(href)").extract_first()
            if next_page != 'https://womensecret.com/es/es/editorial' and next_page == \
                    'https://womensecret.com/es/es/accesorios':
                yield response.follow(next_page, callback=self.category_parse, meta={'start': 0})

    def category_parse(self, response):
        size = response.meta.get('start')
        # total_products = response.css("span.pagination__total-results strong::text").extract_first()
        products = response.css("ul#search-result-items li.grid__unit.s-1-2.l-1-3.grid-tile.new-row")
        for product in products:
            product_url = product.css("div.product-image > a::attr(href)").extract_first()
            skus = list()
            if product_url is not None:
                yield response.follow(product_url, callback=self.product_parse, meta={'skus': skus})
        self.refer = response.url
        if (int(size)+30) <= 60:
            yield response.follow('https://womensecret.com/es/es/accesorios?sz=30&start={}&format=ajax'. format(size),
                                  callback=self.category_parse,
                                  headers=self.headers, meta={'start': size+30})

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

        data['skus'] = skus
        yield data
