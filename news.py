import os, requests, feedparser
from google import genai
feed = feedparser.parse("https://news.google.com/rss/search?q=AI&hl=en-IN&gl=IN&ceid=IN:en")
heads = "\n".join(e.title for e in feed.entries[:15])
ai = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
msg = ai.models.generate_content(model="gemini-2.5-flash",
  contents="In headlines se top 3 AI news, Hinglish mein, 1 line each:\n" + heads).text
requests.post(f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
  data={"chat_id": os.environ["TG_CHAT"], "text": "☀️ " + msg})
