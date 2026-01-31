import requests
import io
import discord
from discord.ext import commands
import markovify
import sys
import random
import time
import json
import os

# --- CONFIGURATION ---
TOKEN = 'YOUR_TOKEN_HERE'
MODEL_NAME = 'ExportedMarkovChainModel.json'
STATS_FILE = 'bot_stats.json'
# ---------------------

class CondoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.brain = None
        self.chat_chance = 0.01
        self.start_time = time.time()
        
        # Load persistent stats
        stats = self.load_stats()
        self.messages_seen = stats.get("messages_seen", 0)
        self.responses_sent = stats.get("responses_sent", 0)
        self.random_chats = stats.get("random_chats", 0)

    def load_stats(self):
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        return {"messages_seen": 0, "responses_sent": 0, "random_chats": 0}

    def save_stats(self):
        data = {
            "messages_seen": self.messages_seen,
            "responses_sent": self.responses_sent,
            "random_chats": self.random_chats
        }
        with open(STATS_FILE, 'w') as f:
            json.dump(data, f)

    async def setup_hook(self):
        print("🧠 Loading 1M message brain...")
        try:
            with open(MODEL_NAME, 'r', encoding='utf-8') as f:
                model_json = f.read()
            self.brain = markovify.Text.from_json(model_json)
            print("✅ Brain Loaded!")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            sys.exit(1)

    async def on_message(self, message):
        if message.author.bot:
            return

        self.messages_seen += 1
        if self.messages_seen % 10 == 0:
            self.save_stats()

        await self.process_commands(message)

        if message.content.startswith(self.command_prefix):
            return

        is_pinged = self.user.mentioned_in(message)
        is_reply = False
        if message.reference:
            ref = message.reference.resolved
            if ref and isinstance(ref, discord.Message) and ref.author == self.user:
                is_reply = True

        random_chatter = random.random() < self.chat_chance

        if is_pinged or is_reply or random_chatter:
            clean_content = message.content.replace(f'<@!{self.user.id}>', '').replace(f'<@{self.user.id}>', '').strip()
            words = clean_content.split()
            response = None

            if len(words) >= 2:
                seed = f"{words[-2]} {words[-1]}"
                try: response = self.brain.make_sentence_with_start(seed, strict=False, tries=50)
                except: pass
            if not response and len(words) >= 1:
                seed = words[-1]
                try: response = self.brain.make_sentence_with_start(seed, strict=False, tries=50)
                except: pass
            if not response:
                response = self.brain.make_sentence(tries=50)

            if response:
                if random_chatter and not (is_pinged or is_reply):
                    self.random_chats += 1
                
                self.responses_sent += 1
                self.save_stats() 
                
                async with message.channel.typing():
                    if is_pinged or is_reply:
                        await message.reply(response.lower())
                    else:
                        await message.channel.send(response.lower())

# --- COMMANDS ---
bot = CondoBot()

@bot.command()
async def stats(ctx):
    uptime_seconds = int(time.time() - bot.start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    embed = discord.Embed(title="📊 FernsClubGPT Lifetime Stats", color=discord.Color.green())
    embed.add_field(name="Session Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=False)
    embed.add_field(name="Lifetime Messages Seen", value=f"{bot.messages_seen:,}", inline=True)
    embed.add_field(name="Lifetime Responses", value=f"{bot.responses_sent:,}", inline=True)
    embed.add_field(name="Lifetime Random Chimes", value=f"{bot.random_chats:,}", inline=True)
    embed.set_footer(text=f"Current Chat Chance: {bot.chat_chance * 100}%")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def setchance(ctx, percentage: float):
    bot.chat_chance = percentage / 100
    await ctx.send(f"✅ Random chat chance set to **{percentage}%**")

@bot.command()
async def greentext(ctx):
    """Generates a short story in 4chan greentext style as plain text."""
    # Using raw strings (r"") to avoid SyntaxWarnings with backslashes
    lines = [r"\>be me"]
    num_lines = random.randint(2, 4)
    
    for _ in range(num_lines):
        line = bot.brain.make_short_sentence(100, tries=50)
        if line:
            lines.append(fr"\>{line.lower()}")
    
    reaction = random.choice(["tfw", "mfw", "pic unrelated"])
    lines.append(fr"\>{reaction}")

    await ctx.send("\n".join(lines))

@bot.command(aliases=['generatememe'])
async def meme(ctx):
    templates = [
        "doge", "drake", "chans", "philosoraptor", "fry", 
        "wonka", "success", "blb", "mordor", "harold", 
        "mostinteresting", "grumpycat", "buzz", "yuno",
        "keanu", "awkward", "fine", "disb"
    ]
    template = random.choice(templates)

    # 1. Generate text
    top_raw = bot.brain.make_short_sentence(40) or "I THINK"
    bottom_raw = bot.brain.make_short_sentence(40) or "THEREFORE I MARKOV"

    # 2. Basic filter to avoid API blocks
    # Swaps common filtered words with meme-friendly alternatives
    def filter_text(t):
        bad_words = {"fucking": "hecking", "shit": "stuff", "hell": "heck"}
        words = t.split()
        return " ".join([bad_words.get(w.lower(), w) for w in words])

    top_raw = filter_text(top_raw).strip(".,!?;: ")
    bottom_raw = filter_text(bottom_raw).strip(".,!?;: ")

    # 3. Precise cleaning function for memegen.link
    def clean(t):
        return (t.replace("?", "~q")
                 .replace("/", "~s")
                 .replace("#", "~h")
                 .replace("%", "~p")
                 .replace(".", "~d") 
                 .replace("'", "''")
                 .replace(" ", "_"))

    # 4. Construct the URL
    url = f"https://api.memegen.link/images/{template}/{clean(top_raw)}/{clean(bottom_raw)}.png"

    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            await ctx.send(file=discord.File(fp=image_bytes, filename="meme.png"))
        elif response.status_code == 403:
            await ctx.send("⚠️ The API blocked that specific text. Trying again with new text...")
            await ctx.invoke(bot.get_command('meme')) # Auto-retry
        else:
            print(f"DEBUG: Failed URL -> {url}")
            await ctx.send(f"❌ API Error {response.status_code}. Try again!")
            
    except Exception as e:
        await ctx.send(f"❌ Connection error: {e}")
        
bot.run(TOKEN)
