import scrapy

class TechSpecSpider(scrapy.Spider):
    name = 'tech_specs'
    allowed_domains = ['cellphones.com.vn']
    start_urls = ['https://cellphones.com.vn/mobile/apple.html']  # URL ban đầu, thay đổi theo nhu cầu

    def parse(self, response):
        # Lấy danh sách các sản phẩm từ trang danh mục
        phones = response.css('div.product-info')
        for phone in phones:
            link = phone.css('a::attr(href)').get()
            if link:
                yield response.follow(link, callback=self.parse_phone)

    def parse_phone(self, response):
        #Thông tin sản phẩm 
        information = []
        i_title = response.css('.box-title p::text').get()
        i_des = response.css('.description::text').get()
        if i_title and i_des:
            information = i_des
        
        #Đặc điểm nổi bật 
        note = response.css('.ksp-content div')
        highlights = []
        h_title = response.css('.ksp-content h2::text').get()
        h_content = note.css('ul li::text').getall()
        if h_title and h_content:
            highlights = h_content

        #Màu và giá 
        colors = []
        all_colors = response.css('.list-variants li')
        for color in all_colors:
            c_title = color.css('.item-variant-name::text').get()
            c_price = color.css('.item-variant-price::text').get()
            if c_title and c_price:
                colors.append({
                    'color': c_title.strip(),
                    'price': c_price.strip()
                })

        yield {
            'information': information,
            'highlights': highlights,
            'colors': colors
        }