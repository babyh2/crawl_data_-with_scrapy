import scrapy
import json
import re

class AttributeProductSpider(scrapy.Spider):
    name = "attribute_product"
    allowed_domains = ["marksandspencer.com", "personalised-discovery.marksandspencer.app"]
    api_url = "https://personalised-discovery.marksandspencer.app/graphql/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Đọc file JSON chứa liên kết từ LinkProductsSpider
        self.product_links = self.load_product_links()

    def load_product_links(self):
        """Hàm đọc toàn bộ product_links từ file product_links.json"""
        try:
            with open("link_compelete_0.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                all_links = []
                # Lặp qua cấu trúc tag -> section -> product -> product_links
                for item in data:
                    product_links = item.get("product_links", [])
                    all_links.extend(product_links)
                self.logger.info(f"Đã tải {len(all_links)} liên kết sản phẩm từ product_links.json")
                return all_links
        except FileNotFoundError:
            self.logger.error("Không tìm thấy file product_links.json. Vui lòng chạy LinkProductsSpider trước.")
            return []
        except json.JSONDecodeError:
            self.logger.error("Lỗi khi đọc file product_links.json. File có thể bị hỏng.")
            return []

    def start_requests(self):
        """Tạo yêu cầu cho từng liên kết sản phẩm"""
        for url in self.product_links:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Thu thập thông tin sản phẩm
        for item in self.get_product_info(response):
            yield item
        # Thu thập màu sắc và hình ảnh
        for item in self.parse_colors(response):
            yield item
        # Thu thập kiểu dáng
        for item in self.get_style(response):
            yield item
        # Thu thập chi tiết sản phẩm
        for item in self.get_detail_and_care(response):
            yield item
        # Thu thập outfits dựa trên variantId từ URL
        variant_id = self.get_variant_id(response.url)
        if variant_id:
            for request in self.get_outfits(response, variant_id):
                yield request

    def get_variant_id(self, url):
        """Trích xuất variantId từ URL sản phẩm"""
        match = re.search(r"/p/[^/]+(\d+)(?=\?|$)", url)
        if match:
            return match.group(1)
        self.logger.warning(f"Không thể trích xuất variantId từ URL: {url}")
        return None

    def get_product_info(self, response):
        product_name = response.css("h1.media-0_headingSm__aysOm::text").get()
        product_brand = response.css(".brand-title_title__u6Xx5::text").get()
        product_price = response.css(".product-intro_priceWrapper__XRTSR p.media-0_headingSm__aysOm::text").get()
        yield {
            "product_url": response.url,
            "product_brand": product_brand,
            "product_name": product_name,
            "product_price": product_price,
        }

    def get_detail_and_care(self, response):
        detail = response.css(".product-details_spacer__MCm8e > div")
        result = []

        for item in detail:
            key = item.css(".media-0_strong__aXigV::text").get()
            if key is None:
                continue

            # Trích xuất tất cả text từ các thẻ con trong div
            values = item.css("*::text").getall()
            # Lọc bỏ key và các giá trị trống hoặc không mong muốn (như ký tự "•")
            values = [v.strip() for v in values if v.strip() and v.strip() != key and v.strip() != "•"]

            result.append({key: values})

        yield {
            "product_detail": result
        }

    def get_style(self, response):
        product_code = response.css('.pdp-template_spacer__yD4kG p.media-0_textXs__ZzHWu::text').getall()
        product_code = ".".join(product_code).replace("Product code: ", "").strip()
        style = response.css('.grid_container__flAnn .grid_col__wFA5R .eco-box_mb__SXq72 .media-0_textSm__Q52Mz+ .media-0_textSm__Q52Mz::text').get()
        style = style.strip() if style else "Not found"
        yield {"product_code": product_code, "style": style}

    def parse_colors(self, response):
        color_labels = response.css('.selector_withImage__Ib2VU::attr(aria-label)').getall()
        color_codes = []
        for label in color_labels:
            color = label.replace(" colour option", "").strip()
            color_cleaned = color.replace(" ", "").upper()
            color_codes.append(color_cleaned)
        color_codes = list(set(color_codes))

        base_url = response.url.split("?")[0]
        for color in color_codes:
            color_url = f"{base_url}?color={color}"
            yield scrapy.Request(
                url=color_url,
                callback=self.parse_images,
                meta={'color': color}
            )

    def parse_images(self, response):
        color = response.meta['color']
        images = response.css('.zoomable-image_image__Rin0W::attr(src)').getall()
        images = [img for img in images if img.startswith('https://assets')]
        yield {"color": color, "images": images}

    def get_outfits(self, response, variant_id):
        """Gửi yêu cầu API GraphQL để lấy outfits dựa trên variantId"""
        query = {
            "query": """
                query($variantId: String!) {
                  pdpOutfitsForProduct(variantId: $variantId) {
                    __typename
                    ... on PDPOutfitsSuccess {
                      title
                      outfitCtaCopy
                      outfits {
                        id
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
                    ... on PDPOutfitsError {
                      message
                    }
                  }
                }
            """,
            "variables": {"variantId": variant_id},
        }

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'application/graphql-response+json, application/graphql+json, application/json',
            'Origin': 'https://www.marksandspencer.com',
            'Referer': response.url,
        }

        yield scrapy.Request(
            url=self.api_url,
            method='POST',
            body=json.dumps(query),
            headers=headers,
            callback=self.parse_outfits,
            meta={'variant_id': variant_id},
            dont_filter=True
        )

    import json

    def parse_outfits(self, response):
        variant_id = response.meta['variant_id']
    
        # Kiểm tra mã trạng thái HTTP
        if response.status != 200:
            print(f"Lỗi: Mã trạng thái {response.status} cho variantId {variant_id}")
            return {'outfits': {}, 'error': f'HTTP {response.status}'}
    
        # Kiểm tra nội dung phản hồi
        if not response.text:
            print(f"Lỗi: Phản hồi rỗng cho variantId {variant_id}")
            return {'outfits': {}, 'error': 'Empty API response'}
    
        # Parse JSON an toàn
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"Lỗi: Không thể parse JSON cho variantId {variant_id}: {e}")
            return {'outfits': {}, 'error': f'JSON decode error: {str(e)}'}
    
        # Kiểm tra xem data có tồn tại và có khóa 'data' không
        if not data or 'data' not in data:
            print(f"Lỗi: Cấu trúc JSON không hợp lệ cho variantId {variant_id}")
            return {'outfits': {}, 'error': 'Invalid JSON structure'}
    
        # Truy cập dữ liệu an toàn
        outfits_data = data.get('data', {}).get('pdpOutfitsForProduct', {})
        outfits = outfits_data.get('outfits', [])
    
        print(f"Tìm thấy {len(outfits)} outfits cho variantId {variant_id}")
        return {'outfits': {outfit['id']: outfit for outfit in outfits if 'id' in outfit}, 'error': None}