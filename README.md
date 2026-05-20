# 🌊 SaveWave Telegram Bot

Download YouTube, TikTok (no watermark), and Instagram videos right inside Telegram.

---

## ⚡ Setup Guide (Beginner Friendly)

### Step 1 — Get your Bot Token (2 minutes)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name: e.g. `SaveWave`
4. Choose a username: e.g. `savewave_dl_bot` (must end in `bot`)
5. BotFather gives you a token like: `7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxx`
6. Copy it — you'll need it in Step 3

---

### Step 2 — Deploy to Railway (free, no PC needed)

1. Go to **https://railway.app** and sign up with GitHub (free)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Upload this folder to a GitHub repo first:
   - Go to **https://github.com/new** → create a repo called `savewave-bot`
   - Upload all files from this folder
4. Back in Railway, select your repo → it auto-detects Python
5. Go to **Variables** tab → click **"New Variable"**:
   - Name: `BOT_TOKEN`
   - Value: *(paste your token from Step 1)*
6. Click **Deploy** — done! ✅

---

### Step 3 — Test your bot

Open Telegram → search for your bot username → send `/start`

Try sending:
- Any TikTok link → get HD video without watermark
- Any YouTube link → get quality options
- Any public Instagram reel/post → get download link

---

## 🖥️ Running Locally (optional)

If you want to run it on your own PC:

```bash
# Install Python 3.11+ first from https://python.org

# Install dependencies
pip install -r requirements.txt

# Set your token (Windows)
set BOT_TOKEN=your_token_here

# Set your token (Mac/Linux)
export BOT_TOKEN=your_token_here

# Run the bot
python bot.py
```

---

## 📋 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | How to use the bot |
| *(any URL)* | Auto-detects platform and fetches download links |

---

## ⚠️ Notes

- **TikTok**: Uses tikwm.com API — watermark-free HD + SD + audio
- **YouTube**: Uses yt-dlp — up to 720p MP4, links open in browser
- **Instagram**: Uses yt-dlp — post must be **public**
- Railway free tier gives you **500 hours/month** (enough for a personal bot)

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot doesn't respond | Check BOT_TOKEN is set correctly |
| YouTube fails | The video may be age-restricted or region-blocked |
| Instagram fails | Make sure the account/post is public |
| TikTok fails | Try again — tikwm.com occasionally rate-limits |
