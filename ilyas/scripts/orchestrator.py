import time


class ScraperOrchestrator:

    def __init__(self, http, listing_parser, product_parser, max_pages=2):
        self.http = http
        self.listing_parser = listing_parser
        self.product_parser = product_parser
        self.max_pages = max_pages

    def scrape(self, start_url):
        url = start_url
        page = 0

        while url and page < self.max_pages:

            print("📄", url)

            html = self.http.get(url, wait_for="#products_match_all")
            if not html:
                break

            product_urls, next_page = self.listing_parser.parse(html)

            for p in product_urls:
                try:
                    # 🔥 ARTIK HTML YOK
                    product = self.product_parser.parse(p)

                    if product:
                        yield product

                except Exception as e:
                    print("❌ hata:", e)
                    continue

                time.sleep(1)

            url = next_page
            page += 1