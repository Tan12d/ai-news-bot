import os, time, requests, feedparser
from google import genai
from google.genai import types

# Tried in order until one works (these were all listed as available for this key).
MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"]

feed = feedparser.parse("https://news.google.com/rss/search?q=AI&hl=en-IN&gl=IN&ceid=IN:en")
heads = "\n".join(e.title for e in feed.entries[:15])

ai = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=60_000),  # 60s per call so it never hangs
)

prompt = ("From these headlines, pick the top 3 AI news stories. Write each as one clear "
          "sentence in plain, professional English only (no Hinglish or other languages). "
          "Number them 1 to 3 with no extra commentary:\n" + heads)

msg = None
for model in MODELS:
    for attempt in range(1, 4):
        try:
            msg = ai.models.generate_content(model=model, contents=prompt).text.strip()
            print(f"OK with {model} (attempt {attempt})")
            break
        except Exception as e:
            print(f"{model} attempt {attempt} failed: {str(e)[:90]}")
            if attempt < 3:
                time.sleep(10 * attempt)
    if msg:
        break

if not msg:
    raise SystemExit("All models failed")

r = requests.post(f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
                  data={"chat_id": os.environ["TG_CHAT"], "text": "☀️ " + msg})
print("Telegram:", r.status_code)
r.raise_for_status()
