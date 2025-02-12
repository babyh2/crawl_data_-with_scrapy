import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time

class CellSpider(scrapy.Spider):
    name = "cell"

    def start_requests(self):
        url = "https://cellphones.com.vn/mobile/samsung.html"
        yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response):
        driver = response.request.meta["driver"]

        button = driver.find_element(By.CSS_SELECTOR, ".cps-block-content_btn-showmore")
        while button.is_displayed():
            button.click()
            time.sleep(2)

        products = driver.find_elements(By.CSS_SELECTOR, ".product-info")

        for product in products:

            url = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            name = product.find_element(By.CSS_SELECTOR, ".product__name h3").text
            new_price = product.find_element(By.CSS_SELECTOR, ".product__price--show").text
            try:
                old_price = product.find_element(By.CSS_SELECTOR, ".old-price-selector").text.strip()
            except NoSuchElementException:
                old_price = "N/A"

            yield {
                "url": url,
                "name": name,
                "old_price": old_price,
                "new_price": new_price.strip()
            }

        driver.quit()
