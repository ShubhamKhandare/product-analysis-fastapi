import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def get_top_amazon_reviews(asin) -> list:
    # TODO handle the crawling and dynamic cookie
    url = f"https://www.amazon.com/product-reviews/{asin}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/58.0.3029.110 Safari/537.3",
        'Cookie': 'i18n-prefs=USD; session-id=142-2504817-9597741; session-id-time=2082787201l; sp-cdn="L5Z9:IN"'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    reviews = []
    for customer_review_section in soup.find_all("div", class_="a-section review aok-relative"):
        review_text = customer_review_section.find("span", class_="a-size-base review-text review-text-content").find(
            "span").text.strip()
        stars = customer_review_section.find("i").text.strip()
        review_type = "positive"
        try:
            stars = float(stars[0:3])
            if stars < 3:
                review_type = "negative"
        except Exception as e:
            logger.warning(f"Failed to detect the review type {e}")

        reviews.append({
            "stars": stars,
            "review": review_text,
            "type": review_type
        })
    return reviews
