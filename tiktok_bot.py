#!/usr/bin/env python3
"""
بوت تيلغرام لتحميل مقاطع TikTok بدون علامة مائية
"""

import telebot
import yt_dlp
import os
import tempfile
import re

BOT_TOKEN = "8863554950:AAGwwGbfBeIOorvhB5ntJ7rluMclFzSBSJ0"

bot = telebot.TeleBot(BOT_TOKEN)

def is_tiktok_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.+'
    return bool(re.match(pattern, url.strip()))

def download_tiktok(url: str) -> str | None:
    tmp_dir = tempfile.mkdtemp()

    ydl_opts = {
        'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://www.tiktok.com/',
        },
        'extractor_args': {
            'tiktok': {
                'app_name': 'trill',
                'app_version': '34.1.2',
                'manifest_app_version': '2023401020',
            }
        },
        'cookiefile': None,
        'geo_bypass': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # تأكد من وجود الملف
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


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 أهلاً! أنا بوت تحميل TikTok\n\n"
        "📌 أرسل لي رابط أي مقطع TikTok وسأرسله بدون علامة مائية ✅\n\n"
        "يدعم:\n"
        "• https://www.tiktok.com/@user/video/...\n"
        "• https://vm.tiktok.com/xxxxx\n"
        "• https://vt.tiktok.com/xxxxx"
    )
    bot.reply_to(message, text)


@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    url = message.text.strip()

    if not is_tiktok_url(url):
        bot.reply_to(message, "❌ الرابط غير صحيح!\nأرسل رابط TikTok صحيح.")
        return

    wait_msg = bot.reply_to(message, "⏳ جاري تحميل المقطع، انتظر لحظة...")

    file_path = download_tiktok(url)

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            bot.edit_message_text(
                "❌ حجم المقطع أكبر من 50MB.",
                chat_id=message.chat.id,
                message_id=wait_msg.message_id
            )
        else:
            with open(file_path, 'rb') as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption="✅ تم التحميل بدون علامة مائية",
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
