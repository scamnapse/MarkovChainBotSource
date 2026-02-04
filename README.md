# Markov Chain Bot - Scamnapse Softworks
Full source code release, do whatever you want with this, make sure to credit me though if you use this.

# How to use this?
Install Python 3.13, ALWAYS MAKE SURE ADD TO PATH IS SET - This assumes you are using Windows.
Once Python is installed, run this command to install everything you need to run these
```
pip install markovify discord.py csv ijson requests beautifulsoup4 urllib
```
Once you have everything installed, edit the discord trainer script to point to your json file, you can get this by using Discord-Chat-Exporter and exporting it in JSON format.
For example:
```py
INPUT_JSON = 'YourJSONFromDiscordChatExporter.json'
MODEL_NAME = 'OutputName.json'
```
Then just run the script and it will export a markov chain model!
Next for the Discord bot edit this line:
```py
TOKEN = 'YOUR_BOT_TOKEN'
MODEL_NAME = 'OutputModelName.json'
```
YOUR_BOT_TOKEN is well, your bot token
MODEL_NAME is the exported model from the script.

# How do i scrape Reddit with this?
Open the RedditScraper.py file, and edit the lines corresponding to the subreddit to scrape and the output file name.
```py
SUBREDDIT = "animemes"
OUTPUT_CSV = "RedditExampleData.csv"
MAX_PAGES = 100
```
For example the configuration above scrapes 100 pages from r/Animemes.
Run the script, let it scrape the data, You can change the redlib instance used, I just used the one set since it doesnt have much against scraping/botting as of right now,
Once it is done scraping you will have 100 pages from r/Animemes (or the other subreddit you chose) scraped into a .csv file.
Next edit the reddit trainer file and look for a line like this:
```py
INPUT_CSV = 'RedditExampleData.csv'
MODEL_NAME = 'ExampleGPT.json'
```
You will edit it to point to your CSV and change the output file name.
once it is done training you can edit the bot's source file to point to the outputted JSON and you have a markov chain trained off of Reddit!

# How do i scrape 4chan with this?
Install basc-py4chan for scraping 4chan
```py
pip install basc-py4chan
```
mostly the same as reddit, except for 4chanScraper.py you change the board instead of the subreddit, default is /g/ as of right now.
# How do i scrape 8kun with this?
Install py8chan
```py
pip install py8chan
```
mostly the same as 4chan/reddit, /v/ is set as the default board for scraping as of now.
# How do i scrape Soyjak Party with this?
Install nodriver
```py
pip install nodriver
```
Install brave, this is also needed for scraping the sharty since they have some anti bot protection.
Run the soyjakpartyscraper.py file. /soy/ is the default board to scrape. edit the file to change the board.

# Will I add support for X site?
Likely not, you can make your own modules for scraping anyways.
Also if you have anny generally decent suggestions for sites to write scrapers for then make a PR and it (might) be added
If you want to know the interest in sites to write scrapers for then it's below listed from most interested (top) to least interested (bottom):
```
4chan ️✅ (Added)
8kun/8chan ✅ (Added)
The Sharty/Soyjak Party ✅ (Added)
Quora (Possible, debating)
Old Yahoo Answers archives (Possible, debating)
Twitter/X (Possible, debating)
YouTube comments (Possible, debatable and not likely.)
Genius/AZLyrics (Possible, likely going to just scrape a whole band's lyrics from every song they have made, unlikely to be made though.)
Roblox chat messages (Possible, this will likely just log every chat to a .csv and you can train off that, also unlikely.)
Old Miiverse archives (Possible, but unlikely)
Swedishwin/The Swinny (Possible, but unlikely)
The Jassy/Jaksoy (Possible, but VERY unlikely since i'd have to go onto that hellscape of a site to get the general HTML structure and I want to avoid scraping images for this site especially.)
Rule34.xxx comments (Possible, VERY unlikely to be added unless if i am REALLY fucking bored and want to write such a thing)
Pornhub Comments (Possible, again same as rule34.xxx and again i dont wanna touch porn sites for comment scraping, also there would only be like 2-3 really funny/idiotic comments per video/post and i'd personally just train off of those, same with rule34.xxx)
Any other porn site (XVideos, XNXX, Realbooru, etc) (Possible, again same as rule34.xxx and again i dont wanna touch porn sites for comment scraping, also there would only be like 2-3 really funny/idiotic comments per video/post and i'd personally just train off of those selected comments, same with rule34.xxx)
```
