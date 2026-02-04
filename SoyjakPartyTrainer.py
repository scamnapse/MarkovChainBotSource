import csv
import markovify
import re
import gc
import sys
import html

# Settings
INPUT_CSV = 'SoyjakStSoyScrape.csv' # Matches your uploaded file
MODEL_NAME = 'SoyjakPartySoyGPT.json'
BATCH_SIZE = 50000 

def clean_text(text):
    """Refined cleaner optimized for 4chan /g/ data."""
    if not text: 
        return None
    
    # 1. Decode HTML entities (converts &gt; to >, &quot; to ", etc.)
    text = html.unescape(text)
    
    # 2. Strip thread ID links (e.g., >>12345678)
    text = re.sub(r'>>\d+', '', text)
    
    # 3. Handle Greentext
    # We remove the '>' so the model treats it as a normal sentence structure
    text = text.replace('>', '') 
    
    # 4. Strip URLs (they break Markov chains by creating unique tokens)
    text = re.sub(r'http\S+', '', text)
    
    # 5. Normalize whitespace and remove technical junk characters
    text = re.sub(r'[*_~`#]', '', text)
    text = " ".join(text.split()).strip()
    
    # 6. ASCII only for model consistency
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Filter for substantial sentences (4chan has a lot of short 'bump' posts)
    return text if len(text) > 20 else None

def run_training():
    combined_model = None
    batch = []
    total_count = 0

    print(f"[*] Reading {INPUT_CSV}...")
    
    try:
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            # FIXED: Now uses DictReader to access the 'text' column correctly
            reader = csv.DictReader(f)
            
            for row in reader:
                cleaned = clean_text(row.get('text', ''))
                if cleaned:
                    batch.append(cleaned)
                    total_count += 1

                if len(batch) >= BATCH_SIZE:
                    print(f"    [+] Merging batch at {total_count} lines...")
                    # state_size=2 for more randomness, 3 for better grammar
                    new_model = markovify.Text(batch, state_size=2, retain_original=False)
                    
                    if combined_model:
                        combined_model = markovify.combine([combined_model, new_model])
                    else:
                        combined_model = new_model
                    
                    batch = [] 
                    gc.collect()

    except KeyboardInterrupt:
        print("\n[!] Training interrupted! Processing what we have...")
    except FileNotFoundError:
        print(f"[!] Error: {INPUT_CSV} not found.")
        sys.exit(1)

    # Merge final batch
    if batch:
        print(f"    [+] Merging final {len(batch)} lines...")
        new_model = markovify.Text(batch, state_size=2, retain_original=False)
        combined_model = markovify.combine([combined_model, new_model]) if combined_model else new_model

    if combined_model:
        print(f"[*] Compiling and saving {MODEL_NAME}...")
        combined_model.compile(inplace=True) 
        
        with open(MODEL_NAME, 'w') as f:
            f.write(combined_model.to_json())
        
        print(f"[*] Success! Total lines processed: {total_count}")
        
        print("\n" + "="*30 + "\nSAMPLE OUTPUT:")
        for _ in range(5):
            # tries=100 helps if the model is picky about start words
            print("GPT:", combined_model.make_sentence(tries=100) or "...")
        print("="*30)

if __name__ == "__main__":
    run_training()