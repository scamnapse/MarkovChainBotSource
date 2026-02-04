import nodriver as uc
import csv
import re
import asyncio
import json
import random
import hashlib
import os

# ================= Settings =================
BASE_URL = "https://soyjak.st"
BOARD = "soy"
OUTPUT_CSV = "SoyjakStSoyScrape.csv"
MIN_TEXT_LENGTH = 15
# ============================================

def find_browser():
    """Locates Brave or Edge if Chrome isn't the default."""
    paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        # Add your custom path here if the above don't work
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def clean_text(text):
    if not text: return ""
    # Remove board quotes
    text = re.sub(r'>>\d+', '', text)
    # Strip HTML tags just in case
    text = re.sub(r'<[^>]+>', '', text)
    # Fix HTML entities
    text = text.replace('&quot;', '"').replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def run_harvest():
    seen_posts = set()
    
    # FIX: Provide the path to nodriver
    browser_path = find_browser()
    if browser_path:
        print(f"[*] Found browser at: {browser_path}")
        browser = await uc.start(browser_executable_path=browser_path)
    else:
        # Try default start if no custom path found
        print("[!] Custom browser not found, trying default Chrome path...")
        browser = await uc.start()
    
    tab = await browser.get(f"{BASE_URL}/{BOARD}/catalog.json")
    
    print("[*] Waiting for browser to load site...")
    await asyncio.sleep(5)
    
    content = await tab.get_content()
    thread_ids = []

    try:
        json_str = re.search(r'\[.*\]', content, re.DOTALL).group()
        catalog_data = json.loads(json_str)
        
        for page in catalog_data:
            for t in page.get('threads', []):
                if t.get('sticky') == 1:
                    continue
                tid = t.get('no')
                if tid:
                    thread_ids.append(tid)
    except Exception as e:
        print(f"[!] Catalog Error: {e}")
        return

    thread_ids = list(dict.fromkeys(thread_ids))
    print(f"[*] Found {len(thread_ids)} unique threads. Starting extraction...")

    total_saved = 0
    duplicates_skipped = 0

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8', buffering=1) as f:
        writer = csv.writer(f)
        writer.writerow(['text'])

        for i, t_id in enumerate(thread_ids):
            target_url = f"{BASE_URL}/{BOARD}/thread/{t_id}.json"
            try:
                await tab.get(target_url)
                await asyncio.sleep(0.05)
                
                raw_page = await tab.get_content()
                json_match = re.search(r'\{.*\}', raw_page, re.DOTALL)
                
                if json_match:
                    data = json.loads(json_match.group())
                    posts = data.get('posts', [])
                    
                    thread_count = 0
                    for post in posts:
                        # Use the clean 'nomarkup' field you found
                        raw_msg = post.get('___body_nomarkup') or post.get('com', '')
                        cleaned = clean_text(raw_msg)
                        
                        if len(cleaned) >= MIN_TEXT_LENGTH:
                            post_hash = hashlib.md5(cleaned.encode('utf-8')).hexdigest()
                            
                            if post_hash not in seen_posts:
                                writer.writerow([cleaned])
                                seen_posts.add(post_hash)
                                total_saved += 1
                                thread_count += 1
                            else:
                                duplicates_skipped += 1
                    
                    print(f"    [{i+1}/{len(thread_ids)}] Thread {t_id}: Saved {thread_count} new posts.")
            
            except Exception as e:
                print(f"    [!] Error on thread {t_id}: {e}")
                continue

    print("-" * 30)
    print(f"[+] Harvest Complete! Unique Posts: {total_saved} (Skipped {duplicates_skipped} dupes)")
    browser.stop()

if __name__ == "__main__":
    uc.loop().run_until_complete(run_harvest())