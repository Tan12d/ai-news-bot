import os, time, requests, feedparser
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


def generate(model, contents, tries=4):
    """Call Gemini, retrying temporary errors (503 high demand, 429 rate limit)."""
    for i in range(tries):
        try:
            return ai.models.generate_content(model=model, contents=contents)
        except Exception as e:
            if i == tries - 1:
                raise
            wait = 15 * (i + 1)
            print(f"{model} failed ({str(e)[:80]}); retrying in {wait}s")
            time.sleep(wait)

def text_candidates():
    """Preferred model first, then other Flash text models your key can use."""
    names = [TEXT_MODEL]
    try:
        skip = ("image", "tts", "live", "audio", "embed", "native", "thinking", "robotics")
        extra = sorted(
            (m.name.removeprefix("models/") for m in ai.models.list()
             if "flash" in m.name and not any(k in m.name for k in skip)),
            reverse=True,
        )
        names += [n for n in extra if n != TEXT_MODEL][:3]
    except Exception as e:
        print("Could not list models:", str(e)[:100])
    return names


prompt = (
    "From these headlines, pick the top 3 AI news stories. "
    "Write each as one clear sentence in plain, professional English. "
    "Number them 1 to 3. No Hinglish, no extra commentary.

" + heads
)

msg = None
for name in text_candidates():
    try:
        msg = generate(name, prompt, tries=2).text.strip()
        print("Text generated with", name)
        break
    except Exception as e:
        print(f"Text model {name} failed: {str(e)[:100]}")
if not msg:
    raise SystemExit("All text models failed")

image = None
for name in IMAGE_MODELS:
    try:
        resp = generate(
            name,
            tries=2,
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
