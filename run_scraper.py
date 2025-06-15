# run_scraper.py

from app.routes.reddit_scraper import scrape_and_store_posts
from app.routes.nasa_scraper import fetch_and_store_nasa_fires

if __name__ == "__main__":
    # fetch_and_store_nasa_fires()
    scrape_and_store_posts()
    print("✅ Scraping completed.")
