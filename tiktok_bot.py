#!/usr/bin/env python3
"""
بوت تيلغرام لتحميل مقاطع TikTok بدون علامة مائية
"""

import telebot
import os
import tempfile
import re
import requests

BOT_TOKEN = "8863554950:AAGwwGbfBeIOorvhB5ntJ7rluMclFzSBSJ0"

bot = telebot.TeleBot(BOT_TOKEN)

def is_tiktok_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.+'
    return bool(re.match(pattern, url.strip()))

def download_tiktok(url: str) -> str | None:
    try:
        # جلب معلومات الفيديو
        api_url = f"https://tikwm.com/api/?url={url}&hd=1"
        r = requests.get(api_url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://tikwm.com/"
        })
        data = r.json()

        if data.get("code") != 0:
            print(f"API خطأ: {data.get('msg')}")
            return None

        # رابط بدون علامة مائية
        video_url = data["data"].get("play")
        if not video_url:
            print("ما في رابط تحميل")
            return None

        # تحميل الفيديو
        tmp_dir = tempfile.mkdtemp()
        file_path = os.path.join(tmp_dir, "video.mp4")

        vr = requests.get(video_url, timeout=60, stream=True, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://tikwm.com/"
        })
        vr.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in vr.iter_content(chunk_size=8192):
                f.write(chunk)

        if os.path.getsize(file_path) > 0:
            return file_path

    except Exception as e:
        print(f"خطأ: {e}")

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
