#!/usr/bin/env python3
"""
بوت تيلغرام لتحميل مقاطع من TikTok, Instagram, X, YouTube, Facebook
"""

import telebot
import yt_dlp
import os
import tempfile
import re
import requests

BOT_TOKEN = "8863554950:AAGwwGbfBeIOorvhB5ntJ7rluMclFzSBSJ0"

bot = telebot.TeleBot(BOT_TOKEN)

# ── التعرف على المواقع ─────────────────────────────────────

SUPPORTED_SITES = {
    'tiktok':    r'(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)',
    'instagram': r'(instagram\.com|instagr\.am)',
    'twitter':   r'(twitter\.com|x\.com|t\.co)',
    'youtube':   r'(youtube\.com|youtu\.be)',
    'facebook':  r'(facebook\.com|fb\.com|fb\.watch)',
    'snapchat':  r'(snapchat\.com)',
}

def detect_site(url: str) -> str | None:
    for site, pattern in SUPPORTED_SITES.items():
        if re.search(pattern, url):
            return site
    return None

# ── تحميل TikTok عبر tikwm.com ────────────────────────────

def download_tiktok(url: str) -> str | None:
    try:
        r = requests.get(
            f"https://tikwm.com/api/?url={url}&hd=1",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://tikwm.com/"}
        )
        data = r.json()
        if data.get("code") != 0:
            return None
        video_url = data["data"].get("play")
        if not video_url:
            return None
        tmp_dir = tempfile.mkdtemp()
        file_path = os.path.join(tmp_dir, "video.mp4")
        vr = requests.get(video_url, timeout=60, stream=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        with open(file_path, "wb") as f:
            for chunk in vr.iter_content(chunk_size=8192):
                f.write(chunk)
        if os.path.getsize(file_path) > 0:
            return file_path
    except Exception as e:
        print(f"TikTok خطأ: {e}")
    return None

# ── تحميل بقية المواقع عبر yt-dlp ────────────────────────

def download_ytdlp(url: str) -> str | None:
    tmp_dir = tempfile.mkdtemp()
    ydl_opts = {
        'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        },
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                for f in os.listdir(tmp_dir):
                    full = os.path.join(tmp_dir, f)
                    if os.path.getsize(full) > 0:
                        return full
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
    except Exception as e:
        print(f"yt-dlp خطأ: {e}")
    return None

# ── الدالة الرئيسية للتحميل ───────────────────────────────

def download(url: str, site: str) -> str | None:
    if site == 'tiktok':
        result = download_tiktok(url)
        if result:
            return result
    return download_ytdlp(url)


# ── أوامر البوت ───────────────────────────────────────────

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 أهلاً! أنا بوت تحميل الفيديوهات\n\n"
        "📌 أرسل لي رابط من أي موقع وسأحمّله لك:\n\n"
        "✅ TikTok\n"
        "✅ Instagram\n"
        "✅ X (Twitter)\n"
        "✅ YouTube\n"
        "✅ Facebook\n"
        "✅ Snapchat (عام فقط)\n\n"
        "فقط أرسل الرابط وانتظر! 🚀"
    )
    bot.reply_to(message, text)


@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    url = message.text.strip()
    site = detect_site(url)

    if not site:
        bot.reply_to(
            message,
            "❌ الرابط غير مدعوم!\n\n"
            "المواقع المدعومة:\n"
            "• TikTok\n• Instagram\n• X (Twitter)\n• YouTube\n• Facebook\n• Snapchat"
        )
        return

    icons = {
        'tiktok': '🎵', 'instagram': '📸', 'twitter': '🐦',
        'youtube': '▶️', 'facebook': '📘', 'snapchat': '👻'
    }
    wait_msg = bot.reply_to(message, f"⏳ جاري تحميل المقطع من {icons.get(site,'')} انتظر...")

    file_path = download(url, site)

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            bot.edit_message_text(
                "❌ حجم المقطع أكبر من 50MB، تيلغرام لا يدعم إرساله.",
                chat_id=message.chat.id,
                message_id=wait_msg.message_id
            )
        else:
            with open(file_path, 'rb') as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption=f"{icons.get(site,'')} تم التحميل بنجاح ✅",
                    supports_streaming=True
                )
            bot.delete_message(message.chat.id, wait_msg.message_id)
        os.remove(file_path)
    else:
        bot.edit_message_text(
            "❌ فشل التحميل! تأكد من:\n"
            "• أن الرابط صحيح\n"
            "• أن الحساب غير خاص (Private)\n"
            "• حاول مرة ثانية",
            chat_id=message.chat.id,
            message_id=wait_msg.message_id
        )


if __name__ == '__main__':
    print("✅ البوت شغّال... اضغط Ctrl+C لإيقافه")
    bot.infinity_polling()
