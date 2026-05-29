#!/usr/bin/env python3
"""
بوت تيلغرام لتحميل مقاطع من TikTok, Instagram, X, YouTube, Facebook
مع خيارات الجودة
"""

import telebot
import yt_dlp
import os
import tempfile
import re
import requests

BOT_TOKEN = "8863554950:AAGwwGbfBeIOorvhB5ntJ7rluMclFzSBSJ0"

bot = telebot.TeleBot(BOT_TOKEN)

# تخزين مؤقت للروابط
pending_urls = {}

SUPPORTED_SITES = {
    'tiktok':    r'(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)',
    'instagram': r'(instagram\.com|instagr\.am)',
    'twitter':   r'(twitter\.com|x\.com|t\.co)',
    'youtube':   r'(youtube\.com|youtu\.be)',
    'facebook':  r'(facebook\.com|fb\.com|fb\.watch)',
    'snapchat':  r'(snapchat\.com)',
}

ICONS = {
    'tiktok': '🎵', 'instagram': '📸', 'twitter': '🐦',
    'youtube': '▶️', 'facebook': '📘', 'snapchat': '👻'
}

def detect_site(url: str) -> str | None:
    for site, pattern in SUPPORTED_SITES.items():
        if re.search(pattern, url):
            return site
    return None

# ── TikTok ────────────────────────────────────────────────

def download_tiktok(url: str, quality: str = 'high') -> tuple:
    try:
        r = requests.get(
            f"https://tikwm.com/api/?url={url}&hd=1",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://tikwm.com/"}
        )
        data = r.json()
        if data.get("code") != 0:
            return None, 'video'

        media_data = data["data"]

        # صور Slideshow
        images = media_data.get("images") or media_data.get("image_post_info")
        if images and isinstance(images, list):
            tmp_dir = tempfile.mkdtemp()
            image_paths = []
            for i, img_url in enumerate(images[:10]):
                img_path = os.path.join(tmp_dir, f"image_{i}.jpg")
                vr = requests.get(img_url, timeout=30, stream=True,
                                  headers={"User-Agent": "Mozilla/5.0"})
                with open(img_path, "wb") as f:
                    for chunk in vr.iter_content(chunk_size=8192):
                        f.write(chunk)
                if os.path.getsize(img_path) > 0:
                    image_paths.append(img_path)
            if image_paths:
                return image_paths, 'images'

        # صوت فقط
        if quality == 'audio':
            audio_url = media_data.get("music")
            if audio_url:
                tmp_dir = tempfile.mkdtemp()
                file_path = os.path.join(tmp_dir, "audio.mp3")
                vr = requests.get(audio_url, timeout=60, stream=True,
                                  headers={"User-Agent": "Mozilla/5.0"})
                with open(file_path, "wb") as f:
                    for chunk in vr.iter_content(chunk_size=8192):
                        f.write(chunk)
                if os.path.getsize(file_path) > 0:
                    return file_path, 'audio'

        # فيديو - عالي أو متوسط
        video_url = media_data.get("play") if quality == 'high' else media_data.get("wmplay") or media_data.get("play")
        if not video_url:
            return None, 'video'

        tmp_dir = tempfile.mkdtemp()
        file_path = os.path.join(tmp_dir, "video.mp4")
        vr = requests.get(video_url, timeout=60, stream=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        with open(file_path, "wb") as f:
            for chunk in vr.iter_content(chunk_size=8192):
                f.write(chunk)
        if os.path.getsize(file_path) > 0:
            return file_path, 'video'

    except Exception as e:
        print(f"TikTok خطأ: {e}")
    return None, 'video'

# ── Instagram ─────────────────────────────────────────────

def download_instagram(url: str, quality: str = 'high') -> tuple:
    try:
        match = re.search(r'/(p|reel|tv)/([A-Za-z0-9_-]+)', url)
        if not match:
            return None, 'video'
        shortcode = match.group(2)
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            "X-IG-App-ID": "936619743392459",
        }
        r = requests.get(f'https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis',
                         headers=headers, timeout=15)
        data = r.json()
        video_url = None
        try:
            media = data["graphql"]["shortcode_media"]
            if media.get("is_video"):
                video_url = media["video_url"]
        except Exception:
            pass

        if video_url:
            tmp_dir = tempfile.mkdtemp()
            ext = "mp3" if quality == 'audio' else "mp4"
            file_path = os.path.join(tmp_dir, f"video.{ext}")
            vr = requests.get(video_url, headers=headers, timeout=60, stream=True)
            with open(file_path, "wb") as f:
                for chunk in vr.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.getsize(file_path) > 0:
                return file_path, 'audio' if quality == 'audio' else 'video'
    except Exception as e:
        print(f"Instagram خطأ: {e}")

    return download_ytdlp(url, quality)

# ── yt-dlp للمواقع الأخرى ─────────────────────────────────

def download_ytdlp(url: str, quality: str = 'high') -> tuple:
    tmp_dir = tempfile.mkdtemp()

    if quality == 'audio':
        ydl_opts = {
            'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            'quiet': True,
            'no_warnings': True,
        }
    elif quality == 'medium':
        ydl_opts = {
            'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
            'format': 'best[height<=480][ext=mp4]/best[height<=480]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }
    else:  # high
        ydl_opts = {
            'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }

    ydl_opts['geo_bypass'] = True
    ydl_opts['http_headers'] = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # mp3 بعد المعالجة
            if quality == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            if not os.path.exists(filename):
                for f in os.listdir(tmp_dir):
                    full = os.path.join(tmp_dir, f)
                    if os.path.getsize(full) > 0:
                        return full, 'audio' if quality == 'audio' else 'video'
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename, 'audio' if quality == 'audio' else 'video'
    except Exception as e:
        print(f"yt-dlp خطأ: {e}")
    return None, 'video'

# ── التحميل الرئيسي ───────────────────────────────────────

def download(url: str, site: str, quality: str = 'high') -> tuple:
    if site == 'tiktok':
        result, media_type = download_tiktok(url, quality)
        if result:
            return result, media_type
    if site == 'instagram':
        return download_instagram(url, quality)
    return download_ytdlp(url, quality)

# ── إرسال الملف ───────────────────────────────────────────

def send_file(message, file_path, media_type, site):
    icon = ICONS.get(site, '')
    caption = f"{icon} تم التحميل بنجاح ✅"

    if media_type == 'images' and isinstance(file_path, list):
        media_group = []
        for i, img in enumerate(file_path):
            with open(img, 'rb') as f:
                media_group.append(
                    telebot.types.InputMediaPhoto(f.read(), caption=caption if i == 0 else "")
                )
        bot.send_media_group(message.chat.id, media_group)
        for img in file_path:
            os.remove(img)

    elif media_type == 'audio' and isinstance(file_path, str):
        with open(file_path, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, caption=caption)
        os.remove(file_path)

    elif isinstance(file_path, str) and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            bot.send_message(message.chat.id, "❌ حجم الملف أكبر من 50MB.")
        else:
            with open(file_path, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=caption, supports_streaming=True)
        os.remove(file_path)

# ── أوامر البوت ───────────────────────────────────────────

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 أهلاً! أنا بوت تحميل الفيديوهات\n\n"
        "📌 أرسل رابط من:\n"
        "✅ TikTok | ✅ Instagram | ✅ YouTube\n"
        "✅ X (Twitter) | ✅ Facebook | ✅ Snapchat\n\n"
        "وسأعطيك خيارات الجودة 🎯"
    )
    bot.reply_to(message, text)


@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    url = message.text.strip()
    site = detect_site(url)

    if not site:
        bot.reply_to(message, "❌ الرابط غير مدعوم!")
        return

    # حفظ الرابط مؤقتاً
    pending_urls[message.chat.id] = {'url': url, 'site': site}

    # أزرار الجودة
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🔥 أعلى جودة", callback_data="quality_high"),
        telebot.types.InlineKeyboardButton("⚡ جودة متوسطة", callback_data="quality_medium"),
    )
    markup.row(
        telebot.types.InlineKeyboardButton("🎵 صوت فقط MP3", callback_data="quality_audio"),
    )

    bot.reply_to(message, f"{ICONS.get(site,'')} اختر جودة التحميل:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("quality_"))
def handle_quality(call):
    quality = call.data.replace("quality_", "")
    chat_id = call.message.chat.id

    if chat_id not in pending_urls:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الرابط، أرسله مرة ثانية")
        return

    url = pending_urls[chat_id]['url']
    site = pending_urls[chat_id]['site']
    del pending_urls[chat_id]

    quality_names = {'high': 'أعلى جودة 🔥', 'medium': 'جودة متوسطة ⚡', 'audio': 'صوت فقط 🎵'}
    bot.edit_message_text(
        f"⏳ جاري التحميل بـ {quality_names.get(quality, '')}...",
        chat_id=chat_id,
        message_id=call.message.message_id
    )

    file_path, media_type = download(url, site, quality)

    if file_path:
        bot.delete_message(chat_id, call.message.message_id)
        send_file(call.message, file_path, media_type, site)
    else:
        bot.edit_message_text(
            "❌ فشل التحميل! تأكد من:\n"
            "• أن الرابط صحيح\n"
            "• أن الحساب غير خاص\n"
            "• حاول مرة ثانية",
            chat_id=chat_id,
            message_id=call.message.message_id
        )

    bot.answer_callback_query(call.id)


if __name__ == '__main__':
    print("✅ البوت شغّال... اضغط Ctrl+C لإيقافه")
    bot.infinity_polling(skip_pending=True)
