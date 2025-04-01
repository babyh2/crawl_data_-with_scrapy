from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import time
import json


class MarkCrawler:
    def __init__(self):
        options = Options()
        # Add options as needed
        # options.add_argument("--headless")
        options.add_argument("--window-size=900,900")
        self.driver = webdriver.Chrome(options=options)
        
    def accept_cookies(self):
        try:
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            
            accept_button.click()
            time.sleep(2)
            
        except TimeoutException:
            print("Warning: Cookie accept button not found")
            try:
                # Alternative selector if the first one fails
                accept_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".onetrust-pc-dark-filter"))
                )
                accept_button.click()
                time.sleep(1)
            except TimeoutException:
                print("Warning: Alternative cookie button not found either")

    def get_product_info(self):
        try:
            info_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".product-intro_slot__MH6jv"))
            )

            brand_title = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".eco-box_mb__SXq72 p.media-0_textSm__Q52Mz"))
            )

            product_title = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".product-intro_slot__MH6jv h1.media-0_headingSm__aysOm"))
            )

            price = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".product-intro_priceWrapper__XRTSR p.media-0_headingSm__aysOm"))
            )
            return {
                "brand_title": brand_title.text,
                "product_title": product_title.text,
                "price": price.text
            }
        except NoSuchElementException as e:
            print(f"Error getting product info: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_product_info: {e}")
            return None

    def extract_text(self, elements):
        return [el.text.strip() for el in elements if el.text.strip()]

    def get_detail(self): 
        details_id = self.driver.find_element(By.ID, "accordion-Details-&-care")
        if not details_id.get_attribute("open"):
            self.driver.execute_script("arguments[0].setAttribute('open', 'true')", details_id)
            time.sleep(2)

        detail = details_id.find_element(By.CLASS_NAME, "accordion_body__sPtbq")
        sections = detail.find_element(By.CLASS_NAME, "eco-box_mb__SXq72")
        section = sections.find_elements(By.CLASS_NAME, "product-details_flexRow__rJgEo")
        composition = detail.find_element(By.CLASS_NAME, "product-details_compositionContainer__41Y7n")

        style = []
        for a in section:
            try:
                temp = a.find_element(By.CLASS_NAME, "product-details_dimension__nPlAW").text
                style.append(temp)
            except Exception as e:
                print(f"Lỗi khi lấy thông tin chi tiết: {e}")
                continue
        
        return {
            "style": style,
            "Composition": self.extract_text(composition.find_elements(By.CSS_SELECTOR, ".media-0_body__yf6Z_")),
        }

    def get_color_variants(self):
        link_photo = []
        try:
            # First find the color selector container
            color_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".colour-selector-container_wrapper__1SuSN"))
            )
            
            # Find all color options
            color_options = color_container.find_elements(By.CSS_SELECTOR, "label.selector_withImage__Ib2VU")
            
            for color in color_options:
                try:
                    # Get color name before clicking
                    color_name = color.get_attribute("aria-label").replace(" colour option", "")
                    
                    # Scroll and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", color)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", color)
                    time.sleep(2)  # Wait for images to load
                    
                    # Get images after color is selected
                    gallery = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".image-gallery_slide__010sj"))
                    )
                    
                    photos = []
                    for photo in gallery:
                        try:
                            img = WebDriverWait(photo, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".product-imagery-gallery_clickableImage__2kzyJ img"))
                            )
                            src = img.get_attribute("src")
                            if src and src not in photos:
                                photos.append(src)
                        except Exception as e:
                            print(f"Error getting photo for {color_name}: {e}")
                            continue

                    if photos:  # Only add if we got photos
                        link_photo.append({
                            "color": color_name,
                            "photos": photos
                        })

                except Exception as e:
                    print(f"Error processing color {color_name if 'color_name' in locals() else 'unknown'}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in color variants: {e}")
        
        return link_photo
    
    def get_style(self):
        try:
            # Get product code
            product_code_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".sticky-grid_stickyBottom__BrklJ p.media-0_textXs__ZzHWu"))
            )
            product_code = product_code_element.text.replace("Product code: ", "").strip()

            # Get style description
            style_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#product-info .eco-box_mb__SXq72 .media-0_textSm__Q52Mz+ .media-0_textSm__Q52Mz"))
            )
            
            return {
                "product_code": product_code,
                "style": style_element.text.strip()
            }
        
        except NoSuchElementException as e:
            print(f"Error getting style: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_style: {e}")
            return None
    
    def click_next_page(self):
        f_button = self.driver.find_element(By.CSS_SELECTOR, ".pdp-outfits-carousel_pdpOutfitsCarouselWrapper__F7sY3 .carousel_root__bmbkv")
        in_button = f_button.find_element(By.CLASS_NAME, "pagination_trigger__YEwyN")
        in_button.click()
        time.sleep(2)

    def get_outfit(self):
        try:
            ways_to_style = self.driver.find_element(By.CSS_SELECTOR, ".pdp-outfits-carousel_pdpOutfitsCarouselWrapper__F7sY3 .carousel_root__bmbkv")
            ways = ways_to_style.find_elements(By.CLASS_NAME, "outfit-card_cardLink__hcOTj")
            outfits = []
            for outfit in ways:
                try:
                    if not outfit.is_displayed() or not outfit.is_enabled():
                        print("🔄 Way bị che, nhấn nút Next trước...")
                        self.click_next_page()  # Nhấn nút "Next"
                        time.sleep(1)  # Đợi trang cập nhật
                    self.driver.execute_script("arguments[0].scrollIntoView();", outfit)
                    time.sleep(1)
                    outfit.click()
                    
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "modal_modalContent__vI854")))
                    all_info = self.driver.find_element(By.CLASS_NAME, "modal_modalContent__vI854")

                    titles = all_info.find_elements(By.CLASS_NAME, "media-0_headingSm__aysOm")
                    contents = all_info.find_elements(By.CSS_SELECTOR, "ul.eco-box_ecoBox__50nux.eco-box_gap__B80YD.eco-box_gapPolyfill__zyYBi.listUnstyled.carousel_slides__n_k7Q")
                    
                    for i in range(len(titles)):
                        if i == 0:
                            pass
                        else:
                            title = titles[i].text
                            datas = contents[i-1].find_elements(By.CSS_SELECTOR, "a.product-card_cardWrapper__GVSTY")
                            links = []
                            for data in datas:
                                link = data.get_attribute("href")
                                links.append(link)
                            outfits.append({"title": title, "links": links})
                    
                    close_button = self.driver.find_element(By.CSS_SELECTOR, ".modal_modalMaxContentArea__PtCHY .modal_modalCloseButton__8qzIY")
                    close_button.click()
                    time.sleep(1)

                except Exception as e:
                    print(f"❌ Lỗi outfit: {e}")
                    time.sleep(2)
                    continue

            return outfits

        except Exception as e:
            print(f"❌Lỗi khi lấy outfit: {e}")
            return []

    def crawl(self, url):
        self.driver.get(url)
        
        # Handle cookies first
        self.accept_cookies()
        
        # Get all data
        product_info = self.get_product_info()
        style = self.get_style()
        color_variants = self.get_color_variants()
        detail = self.get_detail()
        fashion = self.get_outfit()
        
        # Combine all data
        result = {
            "product_info": product_info,
            "style": style,
            "color_variants": color_variants,
            "detail": detail,
            "fashion": fashion
        }
        
        self.driver.quit()
        return result


def main():
    url = "https://www.marksandspencer.com/bomber-jacket-with-stormwear/p/clp60716820?color=LIGHTBROWN#intid=pid_pg1pip48g4r2c1%7Cprodflag_plp_ts_CBS_6"
    crawler = MarkCrawler()
    result = crawler.crawl(url)
    
    # Print or save the result
    print(json.dumps(result, indent=4))
    
    # Optionally save to file
    with open("product_data_02.json", "w") as f:
        json.dump(result, f, indent=4)


if __name__ == "__main__":
    main()
