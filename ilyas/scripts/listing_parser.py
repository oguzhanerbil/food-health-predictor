from bs4 import BeautifulSoup

BASE = "https://world.openfoodfacts.org"


class ListingParser:

    def parse(self, html):
        soup = BeautifulSoup(html, "lxml")

        urls = []

        container = soup.find("ul", id="products_match_all")
        if not container:
            container = soup.find("ul", class_="search_results")

        if not container:
            print("❌ ürün listesi yok")
            return [], None

        for li in container.find_all("li"):
            a = li.find("a", class_="list_product_a", href=True)

            if a and a["href"].startswith("/product/"):
                urls.append(BASE + a["href"])

        next_page = None
        pagination = soup.find("ul", id="pages")

        if pagination:
            next_a = pagination.find("a", rel="next")
            if next_a:
                next_page = BASE + next_a["href"]

        return list(set(urls)), next_page