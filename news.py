import os, requests, feedparser
from google import genai
from google.genai import types

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
TEXT_MODEL = "gemini-3.8-flash"
# Tried in order; the first one that returns an image wins.
IMAGE_MODELS = ["gemini-3.1-flash-image", "gemini-2.5-flash-image"]

feed = feedparser.parse("https://news.google.com/rss/search?q=AI&hl=en-IN&gl=IN&ceid=IN:en")
heads = "\n".join(e.title for e in feed.entries[:15])

ai = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=60_000),  # 60s per call, so it can never hang
)

msg = ai.models.generate_content(
    model=TEXT_MODEL,
    contents=(
        "From these headlines, pick the top 3 AI news stories. "
        "Write each as one clear sentence in plain, professional English. "
        "Number them 1 to 3. No Hinglish, no extra commentary.\n\n" + heads
    ),
).text.strip()

image = None
for name in IMAGE_MODELS:
    try:
        resp = ai.models.generate_content(
            model=name,
            contents=(
                "Create a clean, modern editorial illustration (no text, no logos) "
                "that represents today's top AI news:\n" + msg
            ),
        )
        for part in resp.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                image = part.inline_data.data
                break
        if image:
            print("Image generated with", name)
            break
    except Exception as e:
        print(f"Image model {name} failed: {e}")

caption = "☀️ Today's top AI news\n\n" + msg
base = f"https://api.telegram.org/bot{TOKEN}"

if image:
    r = requests.post(f"{base}/sendPhoto",
                      data={"chat_id": CHAT, "caption": caption[:1024]},
                      files={"photo": ("news.png", image)})
else:
    print("No image available, sending text only")
    r = requests.post(f"{base}/sendMessage", data={"chat_id": CHAT, "text": caption})

print("Telegram:", r.status_code, r.text[:200])
r.raise_for_status()
