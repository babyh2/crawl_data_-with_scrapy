import scrapy
import json

class MarksAndSpencerSpider(scrapy.Spider):
    name = 'marks_and_spencer_spider'
    start_urls = ['https://personalised-discovery.marksandspencer.app/graphql/']

    def start_requests(self):
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
                        clothingType {
                          slug
                          __typename
                        }
                        aesthetics {
                          name
                          __typename
                        }
                        coreOccasions {
                          slug
                          __typename
                        }
                        imageComposite {
                          images {
                            relativeTop
                            relativeLeft
                            relativeWidth
                            url
                            imageSources {
                              url
                              mediaType
                              __typename
                            }
                            __typename
                          }
                          aspectRatio
                          __typename
                        }
                        slots {
                          title
                          products {
                            id
                            strokeId
                            name
                            brand
                            colour
                            imageUrl
                            variantUrl
                            variantId
                            price {
                              display
                              amount
                              currencyCode
                              __typename
                            }
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
        self.log(f"Yêu cầu gửi đi: {query}")
        # Headers để giả lập yêu cầu từ trình duyệt
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'application/graphql-response+json, application/graphql+json, application/json',
            'Origin': 'https://www.marksandspencer.com',
            'Referer': 'https://www.marksandspencer.com/',
        }

        # Gửi yêu cầu POST đến API
        yield scrapy.Request(
            url=self.start_urls[0],
            method='POST',
            body=json.dumps(query),
            headers=headers,
            callback=self.parse_response
        )

    def parse_response(self, response):
        # Chuyển đổi phản hồi JSON thành dictionary
        data = json.loads(response.text)
        self.log(f"Phản hồi từ API: {data}")
        # Lấy danh sách outfits từ phản hồi
        outfits = data.get('data', {}).get('pdpOutfitsForProduct', {}).get('outfits', [])

        # Tạo dictionary để lưu outfits theo id
        outfits_by_id = {}

        # Tách từng outfit theo id
        for outfit in outfits:
            outfit_id = outfit.get('id')
            if outfit_id:
                outfits_by_id[outfit_id] = outfit

        # Lưu vào file JSON
        with open('marks_and_spencer_outfits_s7.json', 'w', encoding='utf-8') as f:
            json.dump(outfits_by_id, f, ensure_ascii=False, indent=4)

        self.log('Dữ liệu đã được lưu vào marks_and_spencer_outfits.json')