import os
import logging
from asgiref.sync import sync_to_async
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from django.conf import settings
from listings.models import Listing, ListingImage

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not found in settings")
            return

        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_listing_id))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🏠 <b>Ko'chmas mulk botiga xush kelibsiz!</b>\n\n"
            "Kvartira ma'lumotlarini olish uchun kvartira ID sini kiriting.\n\n"
            "📝 <b>Foydalanish:</b>\n"
            "1. Kvartira ID sini yuboring (masalan: 34858)\n"
            "2. Bot sizga to'liq ma'lumot va rasmlarni chiqaradi\n\n"
            "❓ Yordam uchun /help buyrug'ini bosing"
        )

        await update.message.reply_text(
            welcome_message,
            parse_mode='HTML'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🆘 <b>Yordam</b>\n\n"
            "📌 <b>Mavjud buyruqlar:</b>\n"
            "/start - Botni boshlash\n"
            "/help - Yordam\n\n"
            "📌 <b>Kvartira ma'lumotlari:</b>\n"
            "Kvartira ID sini yuboring va bot sizga quyidagilarni chiqaradi:\n"
            "• Rasmlar (grid-da)\n"
            "• Tuman\n"
            "• Xonalar soni\n"
            "• Qavat\n"
            "• Umumiy maydon\n"
            "• Narx\n"
            "• Telefon raqam\n\n"
            "❓ Savollar uchun admin bilan bog'laning"
        )

        await update.message.reply_text(
            help_message,
            parse_mode='HTML'
        )

    @sync_to_async
    def get_listing_by_id(self, listing_id):
        """Get listing by ID from database"""
        try:
            listing = Listing.objects.select_related('district', 'owner').prefetch_related('images').get(id=listing_id)
            return listing
        except Listing.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return None

    @staticmethod
    def _get_display(value):
        return value if value else "Ko'rsatilmagan"

    def build_listing_message(self, listing):
        """Build a detailed HTML card text for a listing"""
        get_display = self._get_display

        deal_status = "SOTUVDA" if listing.deal_type == 'sale' else "IJARAGA"
        property_status = listing.get_property_type_display().upper()

        lines = [
            f"<b>🆔 ID {listing.id}</b>",
            "",
            f"<b>{deal_status} • {property_status}</b>",
            "",
            f"<b>💰 ${listing.price:,.0f}</b>",
            f"<b>💵 ${listing.price_per_sqm:,.2f}/m²</b>",
            "",
            f"<b>📍 Rajon:</b> {listing.district.name}",
            f"<b>📌 Manzil:</b> {get_display(listing.address)}",
            f"<b>🚇 Yaqinida:</b> {get_display(listing.nearby)}",
            "",
            f"<b>🏠 Xonalar:</b> {listing.rooms_count} xona",
            f"<b>🏢 Qavat:</b> {listing.floor}/{listing.total_floors}",
            f"<b>📐 Maydon:</b> {listing.total_area} m²",
            f"<b>🏗️ Tur:</b> {property_status}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        # Amenities
        amenity_lines = [line.strip() for line in (listing.amenities or "").splitlines() if line.strip()]
        if amenity_lines:
            lines.append("")
            lines.append(f"<b>✨ Qo'shimcha:</b> {amenity_lines[0]}")
            if len(amenity_lines) > 1:
                lines.append(f"<b>🎯 Sharoitlar:</b> {', '.join(amenity_lines[1:])}")
        else:
            lines.append("")
            lines.append(f"<b>✨ Qo'shimcha:</b> {get_display(listing.amenities)}")

        lines += [
            "",
            f"<b>📅 Ro'yxatdan o'tgan:</b> {listing.registered_at.strftime('%d.%m.%Y')}",
            "",
            f"<b>📞 Telefon:</b> <code>+{listing.owner.phone_number if listing.owner else 'Ko\'rsatilmagan'}</code>",
        ]

        return "\n".join(lines)

    async def send_listing_with_images_and_info(self, update: Update, listing):
        """
        Send listing IMAGES + TEXT as ONE MESSAGE
        Images in batches (max 10 per batch), caption attached to first image
        """
        images = [img for img in listing.images.all() if img.image]
        text = self.build_listing_message(listing)

        logger.info(f"Listing {listing.id}: found {len(images)} image(s)")

        # Agar rasmlar yo'qsa, faqat text jo'nat
        if not images:
            await update.message.reply_text(text, parse_mode='HTML')
            return

        # Rasmlarni maksimum 10 ta batch-da jo'nat (Telegram limit)
        # Har batch = bitta habar
        for batch_start in range(0, len(images), 10):
            batch = images[batch_start:batch_start + 10]
            media = []

            for idx, img in enumerate(batch):
                # BIRINCHI RASM + CAPTION (text)
                if batch_start == 0 and idx == 0:
                    media.append(InputMediaPhoto(
                        media=img.image.url,
                        caption=text,
                        parse_mode='HTML'
                    ))
                # QOLGAN RASMLAR - caption yo'q
                else:
                    media.append(InputMediaPhoto(media=img.image.url))

            try:
                await update.message.reply_media_group(media=media)
            except Exception as e:
                logger.error(f"Error sending media group: {e}")
                # Fallback: text + rasmlar alohida
                if batch_start == 0:
                    await update.message.reply_text(text, parse_mode='HTML')
                for img in batch:
                    try:
                        await update.message.reply_photo(photo=img.image.url)
                    except Exception as e2:
                        logger.error(f"Error sending image: {e2}")

    async def handle_listing_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle listing ID input"""
        try:
            listing_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Xatolik!</b> Iltimos, faqat raqam kiriting (masalan: 34858)",
                parse_mode='HTML'
            )
            return

        listing = await self.get_listing_by_id(listing_id)

        if not listing:
            await update.message.reply_text(
                f"❌ <b>Kvartira topilmadi!</b> ID: {listing_id}\n\n"
                "Iltimos, to'g'ri ID ni kiriting.\n\n"
                "Agar sizda savollar bo'lsa, iltimos, admin bilan bog'laning.",
                parse_mode='HTML'
            )
            return

        # Rasmlar + Text = BIR HABAR
        await self.send_listing_with_images_and_info(update, listing)

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries (button clicks)"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith('copy_phone_'):
            phone_number = query.data.replace('copy_phone_', '')
            await query.message.reply_text(f"📞 <b>Telefon raqam:</b> <code>{phone_number}</code>", parse_mode='HTML')

    def run(self):
        """Run the bot"""
        if not self.token:
            logger.error("Cannot run bot: TELEGRAM_BOT_TOKEN not set")
            return

        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# Bot instance
bot_instance = None

def start_bot():
    """Start the bot (call this from management command or celery)"""
    global bot_instance
    bot_instance = TelegramBot()
    bot_instance.run()