import os, requests, feedparser
from google import genai
feed = feedparser.parse("https://news.google.com/rss/search?q=AI&hl=en-IN&gl=IN&ceid=IN:en")
heads = "\n".join(e.title for e in feed.entries[:15])
ai = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
msg = ai.models.generate_content(model="gemini-3.8-flash",
  contents="From these headlines, pick the top 3 AI news stories. Write each as one clear sentence in plain, professional English only (no Hinglish or other languages). Number them 1 to 3 with no extra commentary:\n" + heads).text
requests.post(f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
  data={"chat_id": os.environ["TG_CHAT"], "text": "☀️ " + msg})
