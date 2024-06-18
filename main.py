import httpx
from selectolax.parser import HTMLParser
import time
from urllib.parse import urljoin
from dataclasses import dataclass, asdict
import json
from rich import print


@dataclass
class Item:
    name: str | None
    price: str | None
    rating: float | None


def get_html(url, **kwargs):

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    if kwargs.get("page"):
        resp = httpx.get(
            url + str(kwargs.get("page")), headers=headers, follow_redirects=True
        )
    else:
        resp = httpx.get(url, headers=headers, follow_redirects=True)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(
            f"Error Response {exc.response.status_code} while requesting {exc.request.url!r}. Page Limit exceeded."
        )
        return False
    html = HTMLParser(resp.text)
    return html


def extract_text(html, selector):
    try:
        text = html.css_first(selector).text()
        clean_text = clean_data(text)
        return clean_text
    except AttributeError:
        return None


def parse_page(html: HTMLParser):
    products = html.css("li.VcGDfKKy_dvNbxUqm29K")

    for product in products:
        yield urljoin("https://www.rei.com", product.css_first("a").attributes["href"])


def parse_item_page(html: HTMLParser):
    new_item = Item(
        name=extract_text(html, "h1#product-page-title"),
        price=extract_text(html, "span.price-value"),
        rating=extract_text(html, "span.cdr-rating__number_15-0-0"),
    )
    return asdict(new_item)


def export_to_json(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)


def clean_data(value):
    chars_to_remove = ["$"]
    for char in chars_to_remove:
        if char in value:
            value = value.replace(char, "")
    return value.strip()


def main():
    products = []
    base_url = "https://www.rei.com/c/mens-climbing-shoes?page="
    for x in range(1, 10):
        print(f"Gathering page: {x}")
        html = get_html(base_url, page=x)
        if html is False:
            break
        product_urls = parse_page(html)
        for urls in product_urls:
            print(urls)
            html = get_html(urls)
            products.append(parse_item_page(html))
            time.sleep(0.5)
    export_to_json(products)


if __name__ == "__main__":
    main()
