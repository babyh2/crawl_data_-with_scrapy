import scrapy

class LinkProductsSpider(scrapy.Spider):
    name = "link_products"
    allowed_domains = ["www.marksandspencer.com"]
    start_urls = ["https://www.marksandspencer.com/aog/home_1"]
    base_url = "https://www.marksandspencer.com"

    def parse(self, response):
        # Gọi hàm để phân tích các liên kết đến trang danh mục
        yield from self.parse_link_to_page_products(response)

    def parse_link_to_page_products(self, response):
        tags = response.css("div.gnav_tab__GM_Zu")
        all_links = {}  # Từ điển lưu trữ tất cả các link
        
        for tag in tags:
            tag_name = tag.css(".gnav_fullWidth__4JO07 p.eco-box_gapPolyfill__zyYBi::text").get()
            if tag_name is None:
                continue
            tag_name = tag_name.strip()  # Loại bỏ khoảng trắng thừa
            
            # Lấy tất cả các section trong tag
            sections = tag.css(".gnav_section__A_vh7")
            if not sections:  # Kiểm tra nếu không có section nào
                continue
            
            # Khởi tạo từ điển con cho tag_name nếu chưa tồn tại
            if tag_name not in all_links:
                all_links[tag_name] = {}
            
            for section in sections:
                section_name = section.css('div.gnav_sectionHeading__Defct::text').get()
                if section_name is None:
                    section_name = section.css('div.gnav_sectionHeading__Defct a::text').get()
                if section_name is None:
                    continue
                section_name = section_name.strip()  # Loại bỏ khoảng trắng thừa
                
                # Khởi tạo danh sách cho section_name nếu chưa tồn tại
                if section_name not in all_links[tag_name]:
                    all_links[tag_name][section_name] = []
                
                # Lấy tất cả sản phẩm trong section
                all_products = section.css("ul.gnav_sectionItems__LqhOG li")
                for link in all_products:
                    products_name = link.css("a::text").get()
                    if products_name is None:
                        continue
                    products_name = products_name.strip()  # Loại bỏ khoảng trắng thừa
                    link_url = link.css("a::attr(href)").get()
                    if link_url is None:
                        continue
                    
                    link_url = self.complete_url(link_url)
                    # Thêm sản phẩm vào danh sách của section_name
                    all_links[tag_name][section_name].append({
                        products_name: {
                            "link": link_url,
                            "product_links": []  # Danh sách để lưu các liên kết sản phẩm
                        }
                    })

        # Gửi yêu cầu đến từng trang danh mục để crawl liên kết sản phẩm
        for tag_name, sections in all_links.items():
            for section_name, products in sections.items():
                for product in products:
                    link = product[list(product.keys())[0]]["link"]
                    yield scrapy.Request(
                        url=link,
                        callback=self.parse_product_page,
                        meta={
                            "product_info": product,
                            "tag_name": tag_name,
                            "section_name": section_name
                        }
                    )

    def complete_url(self, relative_url):
        # Ghép base_url và relative_url để tạo thành URL đầy đủ
        if relative_url.startswith("http"):
            return relative_url
        return self.base_url + relative_url

    def parse_product_page(self, response):
        product_info = response.meta["product_info"]
        tag_name = response.meta["tag_name"]
        section_name = response.meta["section_name"]
        product_name = list(product_info.keys())[0]
        product_data = product_info[product_name]

        # Thu thập các liên kết sản phẩm từ trang hiện tại
        product_links = response.css('.page-container_pageContainer__OTllb a.product-card_cardWrapper__GVSTY::attr(href)').getall()
        product_links = [self.complete_url(link.strip()) for link in product_links if link.strip()]
        
        # Thêm các liên kết sản phẩm vào product_data
        product_data["product_links"].extend(product_links)

        # Kiểm tra trang tiếp theo
        next_page = response.css('.pagination_wrapper__4CNGi p.media-0_strong__aXigV+ a::attr(href)').get()
        if next_page:
            next_page_url = self.complete_url(next_page.strip())
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_next_page,
                meta={
                    "product_info": product_info,
                    "tag_name": tag_name,
                    "section_name": section_name
                }
            )
        else:
            # Nếu không còn trang tiếp theo, yield kết quả
            yield {
                "tag": tag_name,
                "section": section_name,
                "product": product_name,
                "link": product_data["link"],
                "product_links": product_data["product_links"]
            }

    def parse_next_page(self, response):
        product_info = response.meta["product_info"]
        tag_name = response.meta["tag_name"]
        section_name = response.meta["section_name"]
        product_name = list(product_info.keys())[0]
        product_data = product_info[product_name]

        # Thu thập các liên kết sản phẩm từ trang hiện tại
        product_links = response.css('.page-container_pageContainer__OTllb a.product-card_cardWrapper__GVSTY::attr(href)').getall()
        product_links = [self.complete_url(link.strip()) for link in product_links if link.strip()]
        
        # Thêm các liên kết sản phẩm vào product_data
        product_data["product_links"].extend(product_links)

        # Kiểm tra trang tiếp theo
        next_page = response.css('.pagination_wrapper__4CNGi p.media-0_strong__aXigV+ a::attr(href)').get()
        if next_page:
            next_page_url = self.complete_url(next_page.strip())
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_next_page,
                meta={
                    "product_info": product_info,
                    "tag_name": tag_name,
                    "section_name": section_name
                }
            )
        else:
            # Nếu không còn trang tiếp theo, yield kết quả
            yield {
                "tag": tag_name,
                "section": section_name,
                "product": product_name,
                "link": product_data["link"],
                "product_links": product_data["product_links"]
            }