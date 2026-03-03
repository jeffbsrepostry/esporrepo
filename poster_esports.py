import os
import json
import io
import requests
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

PANDASCORE_TOKEN = os.environ.get("PANDASCORE_TOKEN")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

STATE_FILE = "state.json"
TEMPLATE_PATH = "sablno.png"

MAX_DELAY_MINUTES = 10  # maç bittikten en fazla 10 dk içinde at

LEFT_CENTER = (270, 435)
RIGHT_CENTER = (755, 435)
LOGO_SIZE = 360
SCORE_POS = (512, 770)

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"posted": []}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def download_image(url):
    if not url:
        return None
    r = requests.get(url)
    return Image.open(io.BytesIO(r.content)).convert("RGBA")

def circle_crop(img):
    img = img.resize((LOGO_SIZE, LOGO_SIZE))
    mask = Image.new("L", (LOGO_SIZE, LOGO_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, LOGO_SIZE, LOGO_SIZE), fill=255)
    output = Image.new("RGBA", (LOGO_SIZE, LOGO_SIZE))
    output.paste(img, (0, 0), mask)
    return output

def send_to_telegram(photo_bytes, caption):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    files = {"photo": ("result.png", photo_bytes)}
    data = {"chat_id": TG_CHAT_ID, "caption": caption}
    requests.post(url, data=data, files=files)

def get_matches():
    headers = {"Authorization": f"Bearer {PANDASCORE_TOKEN}"}
    params = {
        "sort": "-end_at",
        "per_page": 5,
        "filter[status]": "finished"
    }
    r = requests.get("https://api.pandascore.co/matches", headers=headers, params=params)
    return r.json()

def main():
    state = load_state()
    posted = state.get("posted", [])

    matches = get_matches()

    for match in matches:
        match_id = str(match["id"])

        if match_id in posted:
            continue

        end_time = match.get("end_at")
        if not end_time:
            continue

        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        if now - end_dt > timedelta(minutes=MAX_DELAY_MINUTES):
            continue

        opponents = match.get("opponents", [])
        if len(opponents) < 2:
            continue

        t1 = opponents[0]["opponent"]
        t2 = opponents[1]["opponent"]

        results = match.get("results", [])
        if len(results) < 2:
            continue

        s1 = results[0]["score"]
        s2 = results[1]["score"]

        logo1 = circle_crop(download_image(t1.get("image_url")))
        logo2 = circle_crop(download_image(t2.get("image_url")))

        base = Image.open(TEMPLATE_PATH).convert("RGBA")

        base.paste(logo1, (LEFT_CENTER[0]-LOGO_SIZE//2, LEFT_CENTER[1]-LOGO_SIZE//2), logo1)
        base.paste(logo2, (RIGHT_CENTER[0]-LOGO_SIZE//2, RIGHT_CENTER[1]-LOGO_SIZE//2), logo2)

        draw = ImageDraw.Draw(base)
        font = ImageFont.load_default()
        score_text = f"{s1} - {s2}"
        draw.text(SCORE_POS, score_text, fill="white")

        output = io.BytesIO()
        base.convert("RGB").save(output, format="PNG")

        caption = f"🎮 {t1['name']} {s1}-{s2} {t2['name']}\n#espor"

        send_to_telegram(output.getvalue(), caption)

        posted.append(match_id)
        state["posted"] = posted
        save_state(state)

        break

if __name__ == "__main__":
    main()
