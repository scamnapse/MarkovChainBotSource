import py8chan
import csv
import re
import time
from multiprocessing import Pool, cpu_count

# Settings
BOARD_NAME = 'v'  # Example: 'v', 'pdx', or 'qresearch'
OUTPUT_CSV = "8kunVData.csv"
MIN_POST_LENGTH = 10

def clean_8kun_text(text):
    if not text: return ""
    # Strip Vichan-specific HTML artifacts
    text = re.sub(r'<br\s*/?>', ' ', text) # Convert breaks to spaces
    text = re.sub(r'<[^>]*>', '', text)    # Strip all other HTML
    text = text.replace('&quot;', '"').replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    # Strip >>ID links and URLs
    text = re.sub(r'>>\d+', '', text)
    text = re.sub(r'http\S+', '', text)
    return text.strip()

def scrape_8kun_thread(t_id):
    try:
        # 8kun uses py8chan for Vichan-based API handling
        board = py8chan.Board(BOARD_NAME)
        thread = board.get_thread(t_id)
        if not thread: return []
        
        posts = []
        for post in thread.all_posts:
            # .comment matches the 'com' or 'comment' field in Vichan
            cleaned = clean_8kun_text(post.comment)
            if cleaned and len(cleaned) > MIN_POST_LENGTH:
                posts.append(cleaned)
        return posts
    except Exception:
        return []

def run_8kun_scrape():
    n_cores = cpu_count()
    board = py8chan.Board(BOARD_NAME)
    
    print(f"[*] Fetching active threads from 8kun /{BOARD_NAME}/...")
    # 8kun doesn't always have a reliable public archive.json like 4chan
    # but get_all_thread_ids() will pull everything currently in the catalog.
    all_ids = board.get_all_thread_ids()
    total_threads = len(all_ids)
    
    print(f"[*] Using {n_cores} workers for {total_threads} threads...")

    total_saved = 0
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['text'])

        with Pool(processes=n_cores) as pool:
            for i, post_list in enumerate(pool.imap_unordered(scrape_8kun_thread, all_ids)):
                for p_text in post_list:
                    writer.writerow([p_text])
                    total_saved += 1
                
                if i % 5 == 0:
                    print(f"    Progress: {i}/{total_threads} | Posts: {total_saved}", end='\r')

    print(f"\n\n[*] Success! {total_saved} lines saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    run_8kun_scrape()