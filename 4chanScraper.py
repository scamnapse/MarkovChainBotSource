import basc_py4chan
import requests
import csv
import time
import re
from multiprocessing import Pool, cpu_count

# Settings
BOARD_NAME = 'g'
OUTPUT_CSV = "4chan_G_Markov_Data.csv"
ARCHIVE_LIMIT = 5000  # Set to None to scrape the entire archive
MIN_POST_LENGTH = 10 # Filters out "lol", "this", or just numbers

def clean_text(text):
    if not text: return ""
    # Strip HTML artifacts
    text = text.replace('&quot;', '"').replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    # Strip URLs and >>ID links
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'>>\d+', '', text)
    # Remove excessive newlines
    text = re.sub(r'\n+', ' ', text)
    text = text.replace('>', '')
    
    return text.strip()

def get_manual_archive_ids(board_name):
    url = f"https://a.4cdn.org/{board_name}/archive.json"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200: return res.json()
    except: pass
    return []

def scrape_thread_worker(t_id):
    """Worker function: Each CPU core runs this independently."""
    try:
        # Each process needs its own Board instance to be thread-safe
        board = basc_py4chan.Board(BOARD_NAME)
        thread = board.get_thread(t_id)
        if not thread: return []
        
        posts = []
        for post in thread.all_posts:
            cleaned = clean_text(post.text_comment)
            if cleaned and len(cleaned) > MIN_POST_LENGTH:
                posts.append(cleaned)
        return posts
    except:
        return []

def run_scrape():
    # Define process count here to ensure it's in scope
    n_cores = cpu_count()
    board = basc_py4chan.Board(BOARD_NAME)
    
    print(f"[*] Gathering IDs from /{BOARD_NAME}/...")
    live_ids = board.get_all_thread_ids()
    arch_ids = get_manual_archive_ids(BOARD_NAME)
    
    if ARCHIVE_LIMIT:
        arch_ids = arch_ids[:ARCHIVE_LIMIT]
    
    all_target_ids = list(set(live_ids + arch_ids))
    total_threads = len(all_target_ids)
    
    print(f"[*] Launching {n_cores} workers for {total_threads} threads...")

    total_saved = 0
    # Use 'w' to overwrite. Use 'a' if you want to keep appending.
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8', buffering=1) as f:
        writer = csv.writer(f)
        writer.writerow(['text'])

        with Pool(processes=n_cores) as pool:
            # imap_unordered is the most efficient way to stream data back
            for i, post_list in enumerate(pool.imap_unordered(scrape_thread_worker, all_target_ids)):
                for p_text in post_list:
                    writer.writerow([p_text])
                    total_saved += 1
                
                # Update progress every 5 threads
                if i % 5 == 0:
                    print(f"    Progress: {i}/{total_threads} threads | Lines: {total_saved}    ", end='\r')

    print(f"\n\n[*] Success! Saved {total_saved} lines to {OUTPUT_CSV}")

if __name__ == "__main__":
    # This is mandatory for multiprocessing on Windows
    try:
        run_scrape()
    except KeyboardInterrupt:
        print("\n[!] Manual stop. Data saved.")
    except Exception as e:
        print(f"\n[!] Error: {e}")