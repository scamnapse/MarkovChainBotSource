import requests
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urljoin

# Settings
BASE_URL = "https://redlib.perennialte.ch"
SUBREDDIT = "animemes"
OUTPUT_CSV = "ExampleData.csv"
MAX_PAGES = 100  # How many pages of "Next" to click through

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

def get_page_data(url):
    """Fetches a page, returns thread links and the specific pagination link."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        links = []
        main_content = soup.find('main')
        
        # 1. Get Thread Links
        if main_content:
            titles = main_content.find_all(['h1', 'h2'], class_='post_title')
            for title in titles:
                a = title.find('a', href=True)
                if a:
                    # urljoin fixes the "No scheme supplied" error
                    links.append(urljoin(BASE_URL, a['href']))
        
        # 2. Find the "Next" link (main > div > footer > a)
        next_link = None
        if main_content:
            footer = main_content.find('footer')
            if footer:
                # Look for the link that contains 'after='
                next_btn = footer.find('a', href=lambda h: h and 'after=' in h)
                if next_btn:
                    # urljoin combines current page URL with the relative ?after link
                    next_link = urljoin(url, next_btn['href'])

        return list(set(links)), next_link
    except Exception as e:
        print(f"[!] Error fetching {url}: {e}")
        return [], None

def scrape_comments(url):
    """Extracts all text from comment bodies in a thread."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8' # Fix character encoding artifacts
        soup = BeautifulSoup(res.text, 'html.parser')
        
        comments = []
        for body in soup.find_all('div', class_='comment_body'):
            md = body.find('div', class_='md')
            text = md.get_text(strip=True) if md else body.get_text(strip=True)
            
            # Filter out bot noise and removed posts
            if text and "I am a bot" not in text and "[removed]" not in text:
                comments.append(text)
        return comments
    except Exception as e:
        print(f"    [!] Error thread: {e}")
        return []

def run_scrape():
    current_url = f"{BASE_URL}/r/{SUBREDDIT}?sort=hot"
    pages_scraped = 0
    total_comments = 0

    print(f"[*] Starting crawl on r/{SUBREDDIT} (Max Pages: {MAX_PAGES})")
    
    # buffering=1 and 'a' mode ensure data is saved even on Ctrl+C
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8', buffering=1) as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(['content'])

        try:
            while current_url and pages_scraped < MAX_PAGES:
                print(f"\n[*] --- SCRAPING PAGE {pages_scraped + 1} ---")
                thread_links, next_page = get_page_data(current_url)
                
                if not thread_links:
                    print("[!] No threads found. Instance might be down or blocking.")
                    break

                for i, link in enumerate(thread_links):
                    # Display thread ID from the URL for progress tracking
                    t_name = link.split('/')[-2] if '/' in link else "thread"
                    print(f"    [{i+1}/{len(thread_links)}] {t_name[:40]}...")
                    
                    comments = scrape_comments(link)
                    for c in comments:
                        writer.writerow([c])
                        total_comments += 1
                    
                    f.flush() # Force write to disk
                
                pages_scraped += 1
                current_url = next_page
                
                if current_url:
                    print(f"[*] Found next page. Moving to next set of posts...")
                else:
                    print("[*] No more pages found.")

        except KeyboardInterrupt:
            print("\n[!] Ctrl+C detected! Saving and exiting safely...")

    print(f"\n[*] Finished! Total Pages: {pages_scraped} | Total Comments: {total_comments}")

if __name__ == "__main__":
    run_scrape()
