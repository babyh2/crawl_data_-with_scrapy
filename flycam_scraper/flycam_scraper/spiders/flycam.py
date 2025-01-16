import scrapy
from flycam_scraper.items import flycamItem 

class FlycamSpider(scrapy.Spider):
    name = "flycam"
    allowed_domains = ["flycamvn.com"]
    start_urls = ["https://flycamvn.com/dji-mavic-pro/"]

    def parse(self, response):
        drones = response.css('div.list-sp')
        for drone in drones :
            link = drone.css('h3 > a::attr(href)').get()
            yield response.follow(link, callback = self.parse_drone)

        next_page = response.css('a.nextpostslink::attr(href)').get()
        if next_page is not None :
            yield response.follow(next_page, callback = self.parse)

    def parse_drone(self, response):
        drone_item = flycamItem()
        drone_item['url'] = response.url,
        drone_item['name'] = response.css('h1.entry-title span::text').get(),
        drone_item['new_price'] = response.css('div.pdc-price span.current::attr(data-price)').get(),
        drone_item['old_price'] = response.css('div.pdc-price span.old::attr(data-price)').get(),
        yield drone_item