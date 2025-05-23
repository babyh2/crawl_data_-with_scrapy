import scrapy
import json

class ProductImagesSpider(scrapy.Spider):
    name = "product_images"
    allowed_domains = ["marksandspencer.com", "personalised-discovery.marksandspencer.app"]
    api_url = 'https://personalised-discovery.marksandspencer.app/graphql/'

    def start_requests(self):
        base_url = "https://www.marksandspencer.com/regular-fit-linen-blend-chinos/p/clp60716468"
        yield scrapy.Request(url=base_url, callback=self.parse)

    def parse(self, response):
        # Thu thập thông tin sản phẩm
        for item in self.parse_product_info(response):
            yield item

        # Thu thập màu sắc và hình ảnh
        for item in self.parse_colors(response):
            yield item

        # Thu thập kiểu dáng
        for item in self.get_style(response):
            yield item

        # Thu thập chi tiết sản phẩm
        for item in self.get_detail(response):
            yield item

        # Thu thập outfits
        for request in self.get_outfits(response):
            yield request

    def parse_product_info(self, response):
        product_name = response.css("h1.media-0_headingSm__aysOm::text").get()
        product_brand = response.css(".brand-title_title__u6Xx5::text").get()
        product_price = response.css(".product-intro_priceWrapper__XRTSR p.media-0_headingSm__aysOm::text").get()

        yield {
            "product_url": response.url,
            "product_brand": product_brand,
            "product_name": product_name,
            "product_price": product_price,
        }

    def parse_colors(self, response):
        # Trích xuất danh sách màu từ aria-label
        color_labels = response.css('.selector_withImage__Ib2VU::attr(aria-label)').getall()
        color_codes = []
        for label in color_labels:
            color = label.replace(" colour option", "").strip()
            color_cleaned = color.replace(" ", "").upper()
            color_codes.append(color_cleaned)
        color_codes = list(set(color_codes))

        # Yield danh sách màu
        yield {
            'product': 'Regular Fit Linen Blend Chinos',
            'colors': color_codes
        }

        # Tạo URL cho từng màu để lấy hình ảnh
        base_url = "https://www.marksandspencer.com/regular-fit-linen-blend-chinos/p/clp60716468?color="
        for color in color_codes:
            color_url = f"{base_url}{color}"
            yield scrapy.Request(
                url=color_url,
                callback=self.parse_images,
                meta={'color': color}
            )

    def parse_images(self, response):
        color = response.meta['color']
        images = response.css('.zoomable-image_image__Rin0W::attr(src)').getall()
        images = [img for img in images if img.startswith('https://assets')]

        yield {
            'color': color,
            'images': images,
        }

    def get_style(self, response):
        product_code = response.css('.pdp-template_spacer__yD4kG p.media-0_textXs__ZzHWu::text').getall()
        product_code = ".".join(product_code).replace("Product code: ", "").strip()
        style = response.css('.grid_container__flAnn .grid_col__wFA5R .eco-box_mb__SXq72 .media-0_textSm__Q52Mz+ .media-0_textSm__Q52Mz::text').get()
        style = style.strip() if style else "Not found"

        yield {
            'product_code': product_code,
            'style': style
        }

    def get_detail(self, response):
        sections = response.css('.product-details_spacer__MCm8e .product-details_flexRow__iPTG4 .product-details_dimension__dy_UN::text').getall()
        style = [section.strip() for section in sections]
        composition = response.css('.accordion_right__NrGlT .accordion_details__BNhs0 .product-details_compositionContainer__xgv9c .media-0_textSm__Q52Mz::text').getall()
        composition = [comp.strip() for comp in composition if comp.strip()]

        yield {
            'style': style,
            'composition': composition
        }

    def get_outfits(self, response):
        # Định nghĩa query GraphQL
        query = {
            "query": """
                query {
                  pdpOutfitsForProduct(variantId: "60716467") {
                    __typename
                    ... on PDPOutfitsSuccess {
                      title
                      outfitCtaCopy
                      outfits {
                        id
                        clothingType { slug __typename }
                        aesthetics { name __typename }
                        coreOccasions { slug __typename }
                        imageComposite {
                          images {
                            relativeTop relativeLeft relativeWidth url
                            imageSources { url mediaType __typename }
                            __typename
                          }
                          aspectRatio __typename
                        }
                        slots {
                          title
                          products {
                            id strokeId name brand colour imageUrl variantUrl variantId
                            price { display amount currencyCode __typename }
                            __typename
                          }
                          __typename
                        }
                      }
                    }
                  }
                }
            """,
            "variables": {"variantId": "60716467"},
        }
        
        # Thiết lập headers để mô phỏng yêu cầu từ trình duyệt
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'application/graphql-response+json, application/graphql+json, application/json',
            'Origin': 'https://www.marksandspencer.com',
            'Referer': 'https://www.marksandspencer.com/',
        }
        
        # Gửi yêu cầu POST đến API
        yield scrapy.Request(
            url=self.api_url,
            method='POST',
            body=json.dumps(query),
            headers=headers,
            callback=self.parse_outfits,
            dont_filter=True  # Ngăn chặn lọc trùng lặp hoặc các middleware khác
        )

    # Hàm parse_outfits đã sửa
    def parse_outfits(self, response):
        try:
            # Parse dữ liệu JSON từ phản hồi API
            data = json.loads(response.text)
            outfits = data.get('data', {}).get('pdpOutfitsForProduct', {}).get('outfits', [])
            
            # Ghi log để kiểm tra dữ liệu nhận được
            self.logger.info(f"Outfits data received: {outfits}")
            
            # Nếu không có outfits, trả về dictionary rỗng
            if not outfits:
                self.logger.warning("No outfits found for variantId: 60716467")
                yield {'outfits': {}}
                return
            
            # Chuyển đổi dữ liệu outfits thành dictionary với key là outfit_id
            outfits_by_id = {}
            for outfit in outfits:
                outfit_id = outfit.get('id')
                if outfit_id:
                    outfits_by_id[outfit_id] = outfit
            
            # Trả về kết quả
            yield {
                'outfits': outfits_by_id
            }
        except json.JSONDecodeError as e:
            # Xử lý lỗi nếu JSON không hợp lệ
            self.logger.error(f"Failed to parse JSON response: {e}")
            yield {'outfits': {}}