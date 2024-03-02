import json
import os
from typing import Annotated
import pandas as pd

from dotenv import load_dotenv
from fastapi import FastAPI, Body
from openai import OpenAI

from amazon.amazon_product import get_top_amazon_reviews

load_dotenv()
app = FastAPI()

openai_client = OpenAI(
    # Getting OpenAI key from environment for security
    api_key=os.environ.get("OPENAI_API_KEY"),
)
import logging

logger = logging.getLogger(__name__)


class ReviewFetchError(Exception):
    pass


@app.get("/product/{product_id}/analyze/")
def analyze_product_by_product_id(product_id: str, fetch_from_amazon="false", ):
    product_reviews = []
    if fetch_from_amazon.lower() == "true":
        # Optional param to fetch top review from amazon
        try:
            logger.info(f"Getting top amazon review for product {product_id=}")
            product_reviews = get_top_amazon_reviews(asin=product_id)
            logger.info(f"Received top amazon review for product {product_id=} {product_reviews=}")
            if not product_reviews:
                raise Exception("Failed to fetch reviews from amazon")
        except ReviewFetchError:
            return {"message": f"Failed to fetch reviews from amazon"}
    else:
        # TODO save csv files to database and fetch from database for faster reads
        try:
            # read csv
            data = pd.read_csv(f"csv_files/{product_id.upper()}_product_reviews.csv")
            # Convert the DataFrame to a Dictionary
            product_reviews = data.to_dict(orient='records')
        except ReviewFetchError:
            return {"message": f"Failed to fetch reviews file for {product_id=}"}

    if not product_reviews:
        return {"message": f"Failed to fetch reviews for {product_id=}"}

    analysis_keys = [
        "total count of reviews",
        "average rating out of 5",
        "overall customer experience out of 5",
        "overall customer expectation out of 5",
        "likelihood of repurchase out of 5",
        "likelihood of referring product to friends or family out of 5",
        "value of money out of 5",
        "list of common things in reviews",
        "brand reputation",
        "comparisons to competitors",
        "list of areas of improvement in product",
    ]

    chat_completion = openai_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Process following product review data json list as e-commerce expert."
                           f"Strictly return me json of "
                           f"product analysis combined of all the reviews. {product_reviews}."
                           f"Please consider following keys {analysis_keys}."
            }
        ],
        model="gpt-3.5-turbo",  # TODO Use latest GPT model
        response_format={"type": "json_object"}
    )
    chat_response_json = json.loads(chat_completion.choices[0].message.content)
    # TODO save analysis response in database to avoid recalculation
    return {"product_id": product_id,
            "analysis": chat_response_json,
            "product_reviews": product_reviews, }
