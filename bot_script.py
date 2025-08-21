# -*- coding: utf-8 -*-

"""
Barbarians Telegram Kanalı Başvuru Botu
=========================================

Bu bot, Barbarians Telegram kanalına katılmak isteyen kullanıcılar için
bir başvuru süreci yönetir.

İşlevleri:
1.  Kullanıcıdan `/basvuru` komutu ile başvuru alır.
2.  Önceden tanımlanmış soruları kullanıcıya sırayla sorar.
3.  Toplanan cevapları formatlayarak yönetici grubuna gönderir.
4.  Yönetici grubundaki mesaja "Onayla" ve "Reddet" butonları ekler.
5.  Onay durumunda, kullanıcıya tek kullanımlık bir davet linki oluşturur ve gönderir.
6.  Red durumunda, kullanıcıya bir bilgilendirme mesajı gönderir.

Kurulum ve Çalıştırma:
---------------------
1.  Gerekli kütüphaneleri yükleyin:
    pip install python-telegram-bot==13.7 python-dotenv

2.  Bu dosya ile aynı dizinde `.env` adında bir dosya oluşturun ve içine
    aşağıdaki değişkenleri kendi bilgilerinizle doldurun:

    BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    ADMIN_GROUP_ID="-1001234567890"
    TARGET_CHANNEL_ID="-1009876543210"

3.  Değişkenlerin açıklamaları:
    - BOT_TOKEN: Telegram'da @BotFather'dan alacağınız botunuza ait API token'ı.
    - ADMIN_GROUP_ID: Başvuruların düşeceği yönetici grubunun ID'si.
      (Botu gruba ekleyip /info komutu gibi bir komutla ID'yi alabilirsiniz).
    - TARGET_CHANNEL_ID: Onaylanan kullanıcıların davet edileceği ana Barbarians kanalının ID'si.

4.  Botu sunucunuzda çalıştırın:
    python bot_script.py
"""

import logging
import os
from datetime import timedelta
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)

# .env dosyasındaki çevre değişkenlerini yükle
load_dotenv()

# Temel loglama ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# .env dosyasından değişkenleri al
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")

# Sohbet durumlarını (state) tanımlıyoruz.
# Bot bu durumlar arasında geçiş yaparak hangi soruda kaldığını bilecek.
(
    GET_NAME,
    GET_EXPERIENCE,
    GET_MARKETS,
    GET_RISK_MANAGEMENT,
    GET_REASON,
    GET_TWITTER,
) = range(6)

# Başvuru soruları
QUESTIONS = {
    GET_NAME: "Harika, başlayalım. Lütfen adınızı ve soyadınızı yazın.",
    GET_EXPERIENCE: "Piyasalardaki toplam tecrübeniz kaç yıldır?",
    GET_MARKETS: "Hangi piyasalarda aktif olarak işlem yapıyorsunuz? (Örn: Borsa, Kripto, VİOP, Opsiyonlar)",
    GET_RISK_MANAGEMENT: "Risk yönetimi anlayışınızı birkaç cümleyle nasıl özetlersiniz?",
    GET_REASON: "Barbarians topluluğuna neden katılmak istiyorsunuz?",
    GET_TWITTER: "Son olarak, varsa Twitter (X) kullanıcı adınızı yazabilir misiniz? (Yoksa 'yok' yazabilirsiniz)",
}

# --- Başlangıç ve Başvuru Komutları ---

def start_command(update: Update, context: CallbackContext) -> None:
    """/start komutu verildiğinde kullanıcıyı karşılar."""
    user = update.effective_user
    update.message.reply_html(
        f"Merhaba {user.mention_html()},\n\n"
        f"Barbarians başvuru botuna hoş geldin.\n"
        f"Başvuru yapmak için /basvuru komutunu kullanabilirsin."
    )

def basvuru_command(update: Update, context: CallbackContext) -> int:
    """/basvuru komutu ile başvuru sürecini başlatır."""
    update.message.reply_text("Barbarians başvuru sürecine hoş geldiniz.")
    update.message.reply_text(QUESTIONS[GET_NAME])
    # user_data sözlüğünü temizle, eski başvurudan veri kalmasın
    context.user_data.clear()
    return GET_NAME

# --- Soru-Cevap Fonksiyonları ---

def get_answer(update: Update, context: CallbackContext, current_state: int, next_state: int) -> int:
    """Kullanıcının cevabını alır, kaydeder ve bir sonraki soruyu sorar."""
    answer = update.message.text
    context.user_data[current_state] = answer
    
    # Bir sonraki soruyu sor
    update.message.reply_text(QUESTIONS[next_state])
    return next_state

def get_name(update: Update, context: CallbackContext) -> int:
    return get_answer(update, context, GET_NAME, GET_EXPERIENCE)

def get_experience(update: Update, context: CallbackContext) -> int:
    return get_answer(update, context, GET_EXPERIENCE, GET_MARKETS)

def get_markets(update: Update, context: CallbackContext) -> int:
    return get_answer(update, context, GET_MARKETS, GET_RISK_MANAGEMENT)

def get_risk_management(update: Update, context: CallbackContext) -> int:
    return get_answer(update, context, GET_RISK_MANAGEMENT, GET_REASON)

def get_reason(update: Update, context: CallbackContext) -> int:
    return get_answer(update, context, GET_REASON, GET_TWITTER)

def get_twitter_and_process(update: Update, context: CallbackContext) -> int:
    """Son cevabı alır ve başvuruyu admin grubuna gönderir."""
    context.user_data[GET_TWITTER] = update.message.text
    user = update.effective_user
    
    update.message.reply_text(
        "Teşekkürler! Başvurunuz alındı ve değerlendirilmek üzere ekibimize iletildi. "
        "En kısa sürede size geri dönüş yapacağız."
    )

    # Başvuru özetini oluştur
    summary = (
        f"🚨 **Yeni Başvuru Geldi** 🚨\n\n"
        f"**Başvuran:** {user.first_name} {user.last_name or ''} (@{user.username})\n"
        f"**Kullanıcı ID:** `{user.id}`\n\n"
        f"--- Cevaplar ---\n"
        f"**Ad Soyad:** {context.user_data.get(GET_NAME, 'N/A')}\n"
        f"**Tecrübe:** {context.user_data.get(GET_EXPERIENCE, 'N/A')} yıl\n"
        f"**Piyasalar:** {context.user_data.get(GET_MARKETS, 'N/A')}\n"
        f"**Risk Yönetimi:** {context.user_data.get(GET_RISK_MANAGEMENT, 'N/A')}\n"
        f"**Katılma Nedeni:** {context.user_data.get(GET_REASON, 'N/A')}\n"
        f"**Twitter:** {context.user_data.get(GET_TWITTER, 'N/A')}\n"
    )

    # Onay/Red butonlarını oluştur
    keyboard = [
        [
            InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{user.id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Admin grubuna gönder
    try:
        context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=summary,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Admin grubuna mesaj gönderilemedi: {e}")
        # Geliştiriciye veya size bir hata mesajı gönderebilir
        # context.bot.send_message(chat_id=YOUR_OWN_ID, text=f"Hata: {e}")

    # Sohbeti sonlandır
    return ConversationHandler.END

# --- Yönetici Buton İşlemleri ---

def button_callback_handler(update: Update, context: CallbackContext) -> None:
    """Yönetici grubundaki butonlara basıldığında çalışır."""
    query = update.callback_query
    query.answer()  # Butona basıldığında "loading" animasyonunu durdurur

    # Callback verisini ayrıştır: "action_userid" formatında
    action, user_id_str = query.data.split("_")
    user_id = int(user_id_str)

    # Orijinal başvuru mesajını düzenle
    original_message = query.message.text
    admin_user = query.from_user
    
    if action == "approve":
        try:
            # Tek kullanımlık, 1 gün geçerli davet linki oluştur
            expire_date = (query.message.date + timedelta(days=1))
            invite_link = context.bot.create_chat_invite_link(
                chat_id=TARGET_CHANNEL_ID,
                member_limit=1,
                expire_date=expire_date
            )
            
            # Kullanıcıya onay mesajı ve linki gönder
            context.bot.send_message(
                chat_id=user_id,
                text="Tebrikler! Barbarians topluluğuna başvurunuz onaylandı.\n\n"
                     "Aşağıdaki linke tıklayarak kanala katılabilirsiniz. "
                     "Bu link tek kullanımlıktır ve 24 saat sonra geçersiz olacaktır."
            )
            context.bot.send_message(chat_id=user_id, text=invite_link.invite_link)

            # Admin grubundaki mesajı güncelle
            query.edit_message_text(
                text=original_message + f"\n\n--- \n✅ **Onaylandı** (İşlemi yapan: @{admin_user.username})",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Kullanıcı onaylanırken hata oluştu (ID: {user_id}): {e}")
            query.edit_message_text(
                text=original_message + f"\n\n--- \n⚠️ **Hata!** Link oluşturulamadı. Botun kanalda yönetici olduğundan ve 'üye davet etme' yetkisi olduğundan emin olun.",
                parse_mode='Markdown'
            )

    elif action == "reject":
        try:
            # Kullanıcıya ret mesajı gönder
            context.bot.send_message(
                chat_id=user_id,
                text="İlginiz için teşekkür ederiz. Başvurunuz bu dönem için maalesef olumlu değerlendirilmemiştir.\n\n"
                     "Gelecekteki alımlarda tekrar görüşmek dileğiyle."
            )
            # Admin grubundaki mesajı güncelle
            query.edit_message_text(
                text=original_message + f"\n\n--- \n❌ **Reddedildi** (İşlemi yapan: @{admin_user.username})",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Kullanıcı reddedilirken hata oluştu (ID: {user_id}): {e}")
            query.edit_message_text(
                text=original_message + f"\n\n--- \n⚠️ **Hata!** Kullanıcıya ret mesajı gönderilemedi.",
                parse_mode='Markdown'
            )

# --- İptal Komutu ---

def cancel_command(update: Update, context: CallbackContext) -> int:
    """Başvuru sürecini iptal eder."""
    update.message.reply_text("Başvuru işlemi iptal edildi.")
    context.user_data.clear()
    return ConversationHandler.END

# --- Ana Bot Kurulumu ---

def main() -> None:
    """Botu başlatır ve çalışır durumda tutar."""
    if not all([BOT_TOKEN, ADMIN_GROUP_ID, TARGET_CHANNEL_ID]):
        logger.error(".env dosyasında gerekli değişkenler eksik! Lütfen kontrol edin.")
        return

    # KOD DÜZELTMESİ: Updater'ı başlatırken use_context=True parametresi eklendi.
    # Bu, kütüphanenin modern özelliklerinin doğru çalışması için gereklidir.
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Sohbet yöneticisini (ConversationHandler) oluşturuyoruz
    # Bu yapı, botun kullanıcıyla adım adım sohbet etmesini sağlar.
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('basvuru', basvuru_command)],
        states={
            GET_NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            GET_EXPERIENCE: [MessageHandler(Filters.text & ~Filters.command, get_experience)],
            GET_MARKETS: [MessageHandler(Filters.text & ~Filters.command, get_markets)],
            GET_RISK_MANAGEMENT: [MessageHandler(Filters.text & ~Filters.command, get_risk_management)],
            GET_REASON: [MessageHandler(Filters.text & ~Filters.command, get_reason)],
            GET_TWITTER: [MessageHandler(Filters.text & ~Filters.command, get_twitter_and_process)],
        },
        fallbacks=[CommandHandler('iptal', cancel_command)],
    )

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))

    # Botu başlat
    updater.start_polling()
    logger.info("Bot çalışmaya başladı...")

    # Botu durdurana kadar (Ctrl+C) çalışır
    updater.idle()

if __name__ == '__main__':
    main()
