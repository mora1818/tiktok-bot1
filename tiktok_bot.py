#!/usr/bin/env python3
"""
بوت تيلغرام لتحميل مقاطع TikTok بدون علامة مائية
"""

import telebot
import yt_dlp
import os
import tempfile
import re
import requests

BOT_TOKEN = "8863554950:AAG-xCKnYs0duvP_b0suc66luPQdvvi0kiM"

bot = telebot.TeleBot(BOT_TOKEN)

def is_tiktok_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.+'
    return bool(re.match(pattern, url.strip()))

def download_via_api(url: str) -> str | None:
    """تحميل عبر API مجاني بدون علامة مائية"""
    try:
        api_url = f"https://tikwm.com/api/?url={url}&hd=1"
        r = requests.get(api_url, timeout=15)
        data = r.json()
        if data.get("code") == 0:
            video_url = data["data"].get("play") or data["data"].get("wmplay")
            if video_url:
                tmp_dir = tempfile.mkdtemp()
                file_path = os.path.join(tmp_dir, "video.mp4")
                video_data = requests.get(video_url, timeout=30)
                with open(file_path, "wb") as f:
                    f.write(video_data.content)
                return file_path
    except Exception as e:
        print(f"API خطأ: {e}")
    return None

def download_via_ytdlp(url: str) -> str | None:
    """تحميل عبر yt-dlp كخيار احتياطي"""
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, '%(id)s.%(ext)s')

    configs = [
        # محاولة 1: بدون علامة مائية
        {
            'outtmpl': output_path,
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'tiktok': {'webpage_download': True}},
        },
        # محاولة 2: إعدادات مختلفة
        {
            'outtmpl': output_path,
            'format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        },
    ]

    for opts in configs:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if not os.path.exists(filename):
                    for f in os.listdir(tmp_dir):
                        filename = os.path.join(tmp_dir, f)
                        break
                if os.path.exists(filename):
                    return filename
        except Exception as e:
            print(f"yt-dlp خطأ: {e}")
            continue
    return None

def download_tiktok(url: str) -> str | None:
    """يحاول عدة طرق للتحميل"""
    # الطريقة الأولى: API مجاني
    result = download_via_api(url)
    if result:
        return result
    # الطريقة الثانية: yt-dlp
    return download_via_ytdlp(url)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 أهلاً! أنا بوت تحميل TikTok\n\n"
        "📌 كيف تستخدمني:\n"
        "أرسل لي رابط أي مقطع TikTok وسأرسله لك بدون علامة مائية ✅\n\n"
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
                "❌ حجم المقطع أكبر من 50MB، تيلغرام لا يدعم إرساله.",
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
