import concurrent
import os

from dotenv import load_dotenv

from WordPress import WordPressScraper

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

WORDPRESS_WEBSITES = set(os.getenv("WORDPRESS_WEBSITES", "").split(","))


def scrape_website(base_url):
    print(f"Starting scrape: ({base_url})")
    scraper = WordPressScraper(base_url, DATABASE_URL)
    scraper.fetch_pages(max_pages_count=300)  # limit pages per site if needed
    print(f"Finished scrape: {base_url}")


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(scrape_website, WORDPRESS_WEBSITES)
