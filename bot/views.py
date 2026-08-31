import os
import logging
from asgiref.sync import sync_to_async
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_listing_id))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🏠 *Ko'chmas mulk botiga xush kelibsiz!*\n\n"
            "Kvartira ma'lumotlarini olish uchun kvartira ID sini kiriting.\n\n"
            "📝 *Foydalanish:*\n"
            "1. Kvartira ID sini yuboring (masalan: 18)\n"
            "2. Bot sizga to'liq ma'lumot va rasmlarni chiqaradi\n\n"
            "❓ Yordam uchun /help buyrug'ini bosing"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🆘 *Yordam*\n\n"
            "📌 *Mavjud buyruqlar:*\n"
            "/start - Botni boshlash\n"
            "/help - Yordam\n\n"
            "📌 *Kvartira ma'lumotlari:*\n"
            "Kvartira ID sini yuboring va bot sizga quyidagilarni chiqaradi:\n"
            "• Tuman\n"
            "• Xonalar soni\n"
            "• Qavat\n"
            "• Umumiy maydon\n"
            "• Narx\n"
            "• Telefon raqam\n"
            "• Rasmlar\n\n"
            "❓ Savollar uchun admin bilan bog'laning"
        )
        
        await update.message.reply_text(
            help_message,
            parse_mode='Markdown'
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

    async def handle_listing_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle listing ID input"""
        try:
            listing_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text(
                "❌ *Xatolik!* Iltimos, faqat raqam kiriting (masalan: 18)",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_text("🔍 Ma'lumotlar qidirilmoqda...")

        listing = await self.get_listing_by_id(listing_id)

        if not listing:
            await update.message.reply_text(
                f"❌ *Kvartira topilmadi!* ID: {listing_id}\n\n"
                "Iltimos, to'g'ri ID ni kiriting.",
                parse_mode='Markdown'
            )
            return

        # Format listing information
        property_type_emoji = "🏢" if listing.property_type == 'novostroyka' else "🏠"
        deal_type_emoji = "💰" if listing.deal_type == 'sale' else "🔑"
        
        message = (
            f"{property_type_emoji} *{listing.get_property_type_display()}*\n\n"
            f"📍 *Tuman:* {listing.district.name}\n"
            f"🏠 *Xonalar:* {listing.rooms_count}\n"
            f"🏢 *Qavat:* {listing.floor}/{listing.total_floors}\n"
            f"📐 *Maydon:* {listing.total_area} m²\n"
            f"{deal_type_emoji} *Tur:* {listing.get_deal_type_display()}\n"
            f"💵 *Narx:* ${listing.price:,.2f}\n"
            f"📊 *Narx m²:* ${listing.price_per_sqm:,.2f}\n"
            f"📞 *Telefon:* {listing.owner.phone_number}\n"
            f"👤 *Egasi:* {listing.owner.full_name or 'Ko\'rsatilmagan'}\n"
            f"📅 *Ro'yxatdan o'tgan:* {listing.registered_at.strftime('%d.%m.%Y')}\n\n"
            f"📸 *Rasmlar:* {listing.images.count()} ta"
        )

        # Send listing info
        await update.message.reply_text(message, parse_mode='Markdown')

        # Send images
        images = listing.images.all()
        if images.exists():
            await update.message.reply_text("📸 *Rasmlar:*", parse_mode='Markdown')
            
            # Send images in groups of up to 10
            for i in range(0, len(images), 10):
                image_group = images[i:i+10]
                media_group = []
                
                for image in image_group:
                    if image.image:
                        media_group.append(image.image.url)
                
                # Send images one by one (Telegram media groups have limitations)
                for image in image_group:
                    if image.image:
                        try:
                            await update.message.reply_photo(photo=image.image.url)
                        except Exception as e:
                            logger.error(f"Error sending image: {e}")
                            await update.message.reply_text(f"⚠️ Rasm yuborishda xatolik: {image.id}")
        else:
            await update.message.reply_text("📭 *Rasmlar yo'q*", parse_mode='Markdown')

        # Add contact button
        keyboard = [
            [InlineKeyboardButton("📞 Telefon raqamni nusxalash", callback_data=f"copy_phone_{listing.owner.phone_number}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📞 Telefon raqamni nusxalash uchun tugmani bosing",
            reply_markup=reply_markup
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries (button clicks)"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('copy_phone_'):
            phone_number = query.data.replace('copy_phone_', '')
            await query.message.reply_text(f"📞 *Telefon raqam:* `{phone_number}`", parse_mode='Markdown')

    def run(self):
        """Run the bot"""
        if not self.token:
            logger.error("Cannot run bot: TELEGRAM_BOT_TOKEN not set")
            return

        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Add callback query handler
        from telegram.ext import CallbackQueryHandler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))

        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# Bot instance
bot_instance = None

def start_bot():
    """Start the bot (call this from management command or celery)"""
    global bot_instance
    bot_instance = TelegramBot()
    bot_instance.run()
