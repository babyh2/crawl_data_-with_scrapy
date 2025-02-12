import scrapy
from scrapy_selenium import SeleniumRequest
    
class ScrapingClubSpider(scrapy.Spider):
    name = "scraping_club"
    
    def start_requests(self):
        url = "https://scrapingclub.com/exercise/list_infinite_scroll/"
        yield SeleniumRequest(url=url, callback=self.parse)
    
    def parse(self, response):
        # select all product elements and iterate over them
        for product in response.css(".post"):
            # scrape the desired data from each product
            url = product.css("a").attrib["href"]
            image = product.css(".card-img-top").attrib["src"]
            name = product.css("h4 a::text").get()
            price = product.css("h5::text").get()
    
            # add the data to the list of scraped items
            yield {
                "url": url,
                "image": image,
                "name": name,
                "price": price
            }
