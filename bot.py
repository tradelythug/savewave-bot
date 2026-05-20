import os
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ── Platform detection ─────────────────────────────────────────────────────────

def detect_platform(url: str) -> str | None:
    if re.search(r"youtube\.com|youtu\.be", url):
        return "youtube"
    if re.search(r"tiktok\.com", url):
        return "tiktok"
    if re.search(r"instagram\.com", url):
        return "instagram"
    return None

# ── Downloaders ────────────────────────────────────────────────────────────────

def fetch_tiktok(url: str) -> dict:
    """Fetch TikTok video info via tikwm.com API (no watermark)."""
    try:
        res = requests.get(
            "https://www.tikwm.com/api/",
            params={"url": url, "hd": 1},
            timeout=15
        )
        data = res.json()
        if data.get("code") != 0 or not data.get("data"):
            return {"error": data.get("msg", "Could not fetch video.")}
        v = data["data"]
        return {
            "title": v.get("title", "TikTok Video")[:200],
            "cover": v.get("cover"),
            "hd": v.get("hdplay") or v.get("play"),
            "sd": v.get("play"),
            "audio": v.get("music"),
            "author": v.get("author", {}).get("nickname", ""),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_youtube_info(url: str) -> dict:
    """Use yt-dlp to fetch YouTube video info and download link."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best",
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen = set()
            for f in reversed(info.get("formats", [])):
                h = f.get("height")
                if h and h not in seen and f.get("url") and f.get("ext") == "mp4":
                    seen.add(h)
                    formats.append({
                        "label": f"{h}p",
                        "url": f["url"],
                        "filesize": f.get("filesize"),
                    })
                    if len(formats) >= 4:
                        break
            return {
                "title": info.get("title", "YouTube Video")[:200],
                "thumbnail": info.get("thumbnail"),
                "formats": formats,
                "duration": info.get("duration"),
                "uploader": info.get("uploader", ""),
            }
    except Exception as e:
        return {"error": str(e)}


def fetch_instagram_info(url: str) -> dict:
    """Use yt-dlp to fetch Instagram video info."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "best",
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in reversed(info.get("formats", [])):
                if f.get("url") and f.get("vcodec") != "none":
                    h = f.get("height") or 0
                    formats.append({
                        "label": f"{h}p" if h else "Best",
                        "url": f["url"],
                    })
                    if len(formats) >= 3:
                        break
            return {
                "title": (info.get("title") or info.get("description") or "Instagram Video")[:200],
                "thumbnail": info.get("thumbnail"),
                "formats": formats,
            }
    except Exception as e:
        return {"error": str(e)}

# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt_size(b) -> str:
    if not b:
        return ""
    mb = b / 1_048_576
    return f" · {mb:.1f} MB"


def fmt_duration(s) -> str:
    if not s:
        return ""
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f" · {h}:{m:02d}:{sec:02d}" if h else f" · {m}:{sec:02d}"

# ── Handlers ───────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to SaveWave Bot!*\n\n"
        "Send me any video link and I'll fetch download options for you.\n\n"
        "✅ *Supported platforms:*\n"
        "• 🎬 YouTube — up to 720p MP4\n"
        "• 🎵 TikTok — HD, no watermark\n"
        "• 📸 Instagram — reels & posts\n\n"
        "Just paste a link and I'll handle the rest!",
        parse_mode=ParseMode.MARKDOWN
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use SaveWave:*\n\n"
        "1. Copy a video URL from YouTube, TikTok or Instagram\n"
        "2. Paste it here and send\n"
        "3. Pick your quality and tap the download link\n\n"
        "⚠️ Instagram posts must be *public*.\n"
        "⚠️ YouTube links open in your browser (Telegram can't send large files directly).",
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_url(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    platform = detect_platform(url)

    if not platform:
        await update.message.reply_text(
            "❌ I didn't recognise that URL.\n"
            "Please send a YouTube, TikTok or Instagram link."
        )
        return

    icons = {"youtube": "🎬", "tiktok": "🎵", "instagram": "📸"}
    thinking = await update.message.reply_text(
        f"{icons[platform]} Fetching your {platform.title()} video… please wait ⏳"
    )

    # ── TikTok ──────────────────────────────────────────────────────────────────
    if platform == "tiktok":
        info = fetch_tiktok(url)
        if "error" in info:
            await thinking.edit_text(f"❌ TikTok error: {info['error']}\n\nTry: https://ssstik.io")
            return

        buttons = []
        if info.get("hd"):
            buttons.append([InlineKeyboardButton("⬇️ HD Video (no watermark)", url=info["hd"])])
        if info.get("sd") and info["sd"] != info.get("hd"):
            buttons.append([InlineKeyboardButton("⬇️ SD Video (no watermark)", url=info["sd"])])
        if info.get("audio"):
            buttons.append([InlineKeyboardButton("🎵 Audio only (MP3)", url=info["audio"])])

        caption = (
            f"🎵 *TikTok — No Watermark*\n\n"
            f"*{info['title']}*\n"
            + (f"👤 {info['author']}\n" if info.get("author") else "")
        )

        if info.get("cover"):
            await thinking.delete()
            await update.message.reply_photo(
                photo=info["cover"],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await thinking.edit_text(
                caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    # ── YouTube ─────────────────────────────────────────────────────────────────
    elif platform == "youtube":
        info = fetch_youtube_info(url)
        if "error" in info:
            await thinking.edit_text(
                f"❌ YouTube error: {info['error']}\n\n"
                f"Try manually: https://yt1s.com/en/youtube-to-mp4?q={requests.utils.quote(url)}"
            )
            return

        buttons = []
        for f in info.get("formats", []):
            label = f"⬇️ {f['label']}{fmt_size(f.get('filesize'))}"
            buttons.append([InlineKeyboardButton(label, url=f["url"])])

        if not buttons:
            await thinking.edit_text("❌ No downloadable formats found. Try: https://yt1s.com")
            return

        caption = (
            f"🎬 *YouTube Video*\n\n"
            f"*{info['title']}*\n"
            + (f"📺 {info['uploader']}" if info.get("uploader") else "")
            + fmt_duration(info.get("duration"))
            + "\n\n_Tap a quality to open/download:_"
        )

        if info.get("thumbnail"):
            await thinking.delete()
            await update.message.reply_photo(
                photo=info["thumbnail"],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await thinking.edit_text(
                caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    # ── Instagram ───────────────────────────────────────────────────────────────
    elif platform == "instagram":
        info = fetch_instagram_info(url)
        if "error" in info:
            await thinking.edit_text(
                f"❌ Instagram error: {info['error']}\n\n"
                "Make sure the post is *public*. Try: https://snapinsta.app",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        buttons = []
        for i, f in enumerate(info.get("formats", [])):
            label = f"⬇️ Download {f['label']}" if f["label"] != "Best" else f"⬇️ Download (option {i+1})"
            buttons.append([InlineKeyboardButton(label, url=f["url"])])

        if not buttons:
            await thinking.edit_text("❌ No video found. Make sure the post is public.")
            return

        caption = (
            f"📸 *Instagram Video*\n\n"
            f"*{info['title']}*\n\n"
            "_Tap to download:_"
        )

        if info.get("thumbnail"):
            await thinking.delete()
            await update.message.reply_photo(
                photo=info["thumbnail"],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await thinking.edit_text(
                caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    print("✅ SaveWave Bot is running…")
    app.run_polling()

if __name__ == "__main__":
    main()
