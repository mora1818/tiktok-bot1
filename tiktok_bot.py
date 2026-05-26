#!/usr/bin/env python3
"""
بوت تيلغرام لتحميل مقاطع TikTok بدون علامة مائية
"""

import telebot
import os
import tempfile
import re
import requests

BOT_TOKEN = "8863554950:AAG-xCKnYs0duvP_b0suc66luPQdvvi0kiM"

bot = telebot.TeleBot(BOT_TOKEN)

def is_tiktok_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.+'
    return bool(re.match(pattern, url.strip()))

def download_via_snaptik(url: str) -> str | None:
    """تحميل عبر snaptik API"""
    try:
        api = "https://snaptik.app/abc2.php"
        r = requests.post(api, data={"url": url}, timeout=20)
        data = r.json()
        video_url = data.get("data", {}).get("download_url") or data.get("url")
        if video_url:
            tmp_dir = tempfile.mkdtemp()
            file_path = os.path.join(tmp_dir, "video.mp4")
            vr = requests.get(video_url, timeout=30, stream=True)
            with open(file_path, "wb") as f:
                for chunk in vr.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.getsize(file_path) > 0:
                return file_path
    except Exception as e:
        print(f"snaptik خطأ: {e}")
    return None

def download_via_ssstik(url: str) -> str | None:
    """تحميل عبر ssstik"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://ssstik.io/",
        }
        r = requests.post(
            "https://ssstik.io/abc?url=dl",
            data={"id": url, "locale": "en", "tt": ""},
            headers=headers,
            timeout=20
        )
        # استخراج رابط التحميل من HTML
        match = re.search(r'href="(https://[^"]+\.mp4[^"]*)"', r.text)
        if match:
            video_url = match.group(1)
            tmp_dir = tempfile.mkdtemp()
            file_path = os.path.join(tmp_dir, "video.mp4")
            vr = requests.get(video_url, headers=headers, timeout=30, stream=True)
            with open(file_path, "wb") as f:
                for chunk in vr.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.getsize(file_path) > 0:
                return file_path
    except Exception as e:
        print(f"ssstik خطأ: {e}")
    return None

def download_via_musicaldown(url: str) -> str | None:
    """تحميل عبر musicaldown"""
    try:
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://musicaldown.com/"}
        # الحصول على token
        page = session.get("https://musicaldown.com/en", headers=headers, timeout=15)
        token_match = re.search(r'name="([a-z]+)"\s+value="([^"]+)"', page.text)
        if not token_match:
            return None
        token_name = token_match.group(1)
        token_value = token_match.group(2)
        # إرسال الطلب
        r = session.post(
            "https://musicaldown.com/download",
            data={token_name: token_value, "link": url, "submit": ""},
            headers=headers,
            timeout=20
        )
        match = re.search(r'href="(https://[^"]+\.mp4[^"]*)"', r.text)
        if match:
            video_url = match.group(1)
            tmp_dir = tempfile.mkdtemp()
            file_path = os.path.join(tmp_dir, "video.mp4")
            vr = session.get(video_url, headers=headers, timeout=30, stream=True)
            with open(file_path, "wb") as f:
                for chunk in vr.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.getsize(file_path) > 0:
                return file_path
    except Exception as e:
        print(f"musicaldown خطأ: {e}")
    return None

def download_tiktok(url: str) -> str | None:
    """يحاول عدة مواقع للتحميل"""
    for func in [download_via_ssstik, download_via_musicaldown, download_via_snaptik]:
        result = func(url)
        if result:
            return result
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
