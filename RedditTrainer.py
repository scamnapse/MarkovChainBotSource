import csv
import markovify
import re
import gc
import sys

# Settings
INPUT_CSV = 'ExampleDataName.csv'
MODEL_NAME = 'name_hereGPT.json'
BATCH_SIZE = 50000  # Number of rows to process before merging models

def clean_text(text):
    """Refined cleaner for Reddit/Redlib data."""
    if not text: 
        return None
    
    # 1. Skip Bot messages and removed content
    junk_patterns = [
        "I am a bot", 
        "automatically removed", 
        "[removed]", 
        "[deleted]",
        "Hi! Thank-you for your comment"
    ]
    if any(pattern in text for pattern in junk_patterns):
        return None

    # 2. Fix encoding artifacts (e.g., â€™ -> ')
    # PyPy/CPython handle this well via 'ignore' to keep the text clean
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # 3. Strip Markdown/Links/User tags
    text = re.sub(r'http\S+|/u/\S+|/r/\S+', '', text)
    text = re.sub(r'[*_~>`#]', '', text)
    
    # 4. Normalize whitespace
    text = " ".join(text.split()).strip()
    
    # Only keep substantial sentences (filter out "Lol", "This", etc.)
    return text if len(text) > 20 else None

def run_training():
    combined_model = None
    batch = []
    total_count = 0

    print(f"[*] Reading {INPUT_CSV}...")
    
    try:
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            # Using DictReader to handle the "content" column
            reader = csv.DictReader(f)
            
            for row in reader:
                cleaned = clean_text(row.get('content', ''))
                if cleaned:
                    batch.append(cleaned)
                    total_count += 1

                # When batch is full, create a mini-model and merge it
                if len(batch) >= BATCH_SIZE:
                    print(f"    [+] Merging batch at {total_count} lines...")
                    
                    # state_size=2 for chaos/funny, state_size=3 for better logic
                    new_model = markovify.Text(batch, state_size=2, retain_original=False)
                    
                    if combined_model:
                        combined_model = markovify.combine([combined_model, new_model])
                    else:
                        combined_model = new_model
                    
                    batch = [] 
                    gc.collect() # Clear memory

    except KeyboardInterrupt:
        print("\n[!] Training interrupted! Processing what we have...")
    except FileNotFoundError:
        print(f"[!] Error: {INPUT_CSV} not found. Run the scraper first!")
        sys.exit(1)

    # Merge the final remaining batch
    if batch:
        print(f"    [+] Merging final {len(batch)} lines...")
        new_model = markovify.Text(batch, state_size=2, retain_original=False)
        combined_model = markovify.combine([combined_model, new_model]) if combined_model else new_model

    if combined_model:
        print("[*] Compiling and saving AtheismGPT model. This may take a minute...")
        combined_model.compile(inplace=True) 
        
        with open(MODEL_NAME, 'w') as f:
            f.write(combined_model.to_json())
        
        print(f"[*] Success! Saved model to {MODEL_NAME}")
        print(f"[*] Total lines processed: {total_count}")
        
        # Test generation
        print("\n" + "="*30)
        print("SAMPLE OUTPUT:")
        for _ in range(5):
            print("GPT:", combined_model.make_sentence() or "Model too small for sentence generation.")
        print("="*30)
    else:
        print("[!] No data was successfully processed. Check your CSV.")

if __name__ == "__main__":
    run_training()
