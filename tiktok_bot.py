#!/usr/bin/env python3
"""
بوت تيلغرام لتحميل مقاطع TikTok بدون علامة مائية
تثبيت المتطلبات:
    pip install pyTelegramBotAPI requests yt-dlp
تشغيل البوت:
    python tiktok_bot.py
"""

import telebot
import yt_dlp
import os
import tempfile
import re

# ضع التوكن هنا
BOT_TOKEN = "8863554950:AAEdzKNpGoqYMkwUSyKJ-l38MAjj1UHbny0"

bot = telebot.TeleBot(BOT_TOKEN)

def is_tiktok_url(url: str) -> bool:
    """التحقق إذا الرابط من TikTok"""
    pattern = r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.+'
    return bool(re.match(pattern, url.strip()))

def download_tiktok(url: str) -> str | None:
    """تحميل مقطع TikTok وإرجاع مسار الملف"""
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        # إزالة العلامة المائية
        'extractor_args': {
            'tiktok': {
                'api_hostname': 'api22-normal-c-useast2a.tiktokv.com',
                'app_version': '20.9.3',
            }
        },
        'http_headers': {
            'User-Agent': 'TikTok 26.2.0 rv:262018 (iPhone; iOS 14.4.2; en_US) Cronet',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # بعض الأحيان الامتداد يختلف
            if not os.path.exists(filename):
                for f in os.listdir(tmp_dir):
                    filename = os.path.join(tmp_dir, f)
                    break
            return filename
    except Exception as e:
        print(f"خطأ في التحميل: {e}")
        return None


# ── أوامر البوت ──────────────────────────────────────────────

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 أهلاً! أنا بوت تحميل TikTok\n\n"
        "📌 كيف تستخدمني:\n"
        "أرسل لي رابط أي مقطع TikTok وسأرسله لك بدون علامة مائية ✅\n\n"
        "مثال:\n"
        "https://www.tiktok.com/@user/video/1234567890\n\n"
        "أو روابط vm.tiktok.com المختصرة 👍"
    )
    bot.reply_to(message, text)


@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    url = message.text.strip()

    if not is_tiktok_url(url):
        bot.reply_to(message, "❌ الرابط غير صحيح!\nأرسل رابط TikTok صحيح مثل:\nhttps://vm.tiktok.com/xxxxx")
        return

    # رسالة انتظار
    wait_msg = bot.reply_to(message, "⏳ جاري تحميل المقطع، انتظر لحظة...")

    file_path = download_tiktok(url)

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)

        # تيلغرام يقبل حتى 50MB
        if file_size > 50 * 1024 * 1024:
            bot.edit_message_text(
                "❌ حجم المقطع أكبر من 50MB، تيلغرام لا يدعم إرسال ملفات بهذا الحجم.",
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

        # حذف الملف المؤقت
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


# ── تشغيل البوت ──────────────────────────────────────────────

if __name__ == '__main__':
    print("✅ البوت شغّال... اضغط Ctrl+C لإيقافه")
    bot.infinity_polling()
