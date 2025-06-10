
# run_scraper.py

from app.routes.reddit_scraper import scrape_and_store_posts

if __name__== "__main__":
    scrape_and_store_posts()
    print("✅ Scraping completed.")