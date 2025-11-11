import os
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from pymongo import MongoClient


class WordPressScraper:
    def __init__(
            self,
            base_url: str,
            database_url: str,
    ):
        self.base_url: str = base_url
        self.collection_name: str = self._get_website_domain()
        self.seen_post_ids: set = set()
        self.database_client = MongoClient(database_url)
        self.database = self.database_client["scraped"]
        self.collection = self.database[self.collection_name]

        # Ensure "id" is indexed uniquely
        self.collection.create_index("id", unique=True)

        # Initialize seen_post_ids from DB
        self.seen_post_ids = self._get_fetched_post_ids()

    def _get_website_domain(self):
        parsed_url = urlparse(self.base_url)
        return parsed_url.netloc

    def _get_fetched_post_ids(self) -> set:
        """Fetch all existing post IDs from MongoDB to avoid duplicates."""
        ids = self.collection.distinct("id")
        return set(ids)

    def fetch_one_page(
            self,
            page: int,
            results_per_page: int = 100,
    ) -> list | None:

        assert 1 <= results_per_page <= 100, "Results per page must be between 1 and 100"
        assert 0 < page, "Page must be equal or greater than 1"

        response = requests.get(f"{self.base_url}?page={page}&per_page={results_per_page}")
        response.raise_for_status()

        data = response.json()
        return data if len(data) > 0 else None

    def fetch_pages(
            self,
            start_page: int = 1,
            results_per_page: int = 100,
            max_pages_count: int | None = None,
    ):
        current_page = start_page

        while True:
            if max_pages_count is not None and current_page > max_pages_count:
                break

            page_results = self.fetch_one_page(current_page, results_per_page)

            if page_results is None:
                print(f"{self.collection_name} | No results returned for page {current_page}")
                break

            self.save_posts(page_results)
            print(
                f"{self.collection_name} | Page {current_page} saved | Total posts stored: {self.collection.count_documents({})}")

            current_page += 1

    def save_posts(self, posts: list):
        if not posts:
            return

        # Prepare posts with _id set to WordPress id
        docs = []
        for post in posts:
            doc = post.copy()
            doc["_id"] = post["id"]  # set MongoDB primary key
            docs.append(doc)

        try:
            self.collection.insert_many(docs, ordered=False)
        except Exception as e:
            print(f"{self.collection_name} | Skipped duplicated posts")


if __name__ == "__main__":
    load_dotenv()

    BASE_URL = "https://wordpress.org/wp-json/wp/v2/posts"
    DATABASE_URL = os.getenv("DATABASE_URL")

    scraper = WordPressScraper(BASE_URL, DATABASE_URL)
    scraper.fetch_pages(max_pages_count=3)
