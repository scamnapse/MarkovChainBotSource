import ijson
import markovify
import re
import json
import gc
import sys

INPUT_JSON = 'FileNameForMessagesFromDiscordChatExporter.json'
MODEL_NAME = 'name_hereGPT.json'
BATCH_SIZE = 50000  # Number of messages to process before merging

def clean_text(text):
    if not text: return None
    text = re.sub(r'<@!?\d+>|<@&\d+>|http\S+', '', text).strip()
    return text if len(text) > 1 else None

def run_training():
    combined_model = None
    batch = []
    count = 0

    print(f"Reading {INPUT_JSON}...")
    try:
        with open(INPUT_JSON, 'rb') as f:
            parser = ijson.items(f, 'messages.item')
            
            for msg in parser:
                if msg.get('type') == "Default":
                    content = clean_text(msg.get('content'))
                    if content:
                        batch.append(content)
                        count += 1

                if len(batch) >= BATCH_SIZE:
                    new_model = markovify.Text(batch, state_size=2, retain_original=False)
                    combined_model = markovify.combine([combined_model, new_model]) if combined_model else new_model
                    batch = [] 
                    gc.collect() 
                    print(f"Progress: {count} messages merged...")

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected! Attempting emergency save...")
    
    # This block runs whether the loop finished naturally OR was interrupted
    if batch:
        print(f"Merging final {len(batch)} messages...")
        new_model = markovify.Text(batch, state_size=2, retain_original=False)
        combined_model = markovify.combine([combined_model, new_model]) if combined_model else new_model

    if combined_model:
        print("Compiling and saving model. Do not close the window...")
        combined_model.compile(inplace=True) 
        with open(MODEL_NAME, 'w') as f:
            f.write(combined_model.to_json())
        print(f"Successfully saved {count} messages to {MODEL_NAME}")
    else:
        print("No data was processed.")

if __name__ == "__main__":
    run_training()
