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
            "🏠 <b>Ko'chmas mulk botiga xush kelibsiz!</b>\n\n"
            "Kvartira ma'lumotlarini olish uchun kvartira ID sini kiriting.\n\n"
            "📝 <b>Foydalanish:</b>\n"
            "1. Kvartira ID sini yuboring (masalan: 18)\n"
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

    async def handle_listing_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle listing ID input"""
        try:
            listing_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Xatolik!</b> Iltimos, faqat raqam kiriting (masalan: 18)",
                parse_mode='HTML'
            )
            return

        await update.message.reply_text("🔍 Ma'lumotlar qidirilmoqda...")

        listing = await self.get_listing_by_id(listing_id)

        if not listing:
            await update.message.reply_text(
                f"❌ <b>Kvartira topilmadi!</b> ID: {listing_id}\n\n"
                "Iltimos, to'g'ri ID ni kiriting.",
                parse_mode='HTML'
            )
            return

        # Format listing information with modern HTML styling
        property_type_emoji = "🏢" if listing.property_type == 'novostroyka' else "🏠"
        deal_type_emoji = "💰" if listing.deal_type == 'sale' else "🔑"
        owner_name = listing.owner.full_name if listing.owner.full_name else "Ko'rsatilmagan"
        
        # Status badges - matching design colors
        deal_status = "🔴 SOTUVDA" if listing.deal_type == 'sale' else "🟢 IJARAGA"
        property_status = f"� {listing.get_property_type_display().upper()}"
        
        # Helper for default values
        def get_display(value):
            return value if value else "Ko'rsatilmagan"
        
        # Create modern card-style message based on design
        message = (
            f"{deal_status} • {property_status}\n\n"
            f"💵 <b>${listing.price:,.2f}</b>\n"
            f"<code>${listing.price_per_sqm:,.2f}/m²</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 <b>Tuman:</b> {listing.district.name}\n"
            f"🏠 <b>Manzil:</b> {get_display(listing.address)}\n"
            f"🏛️ <b>Yaqinida:</b> {get_display(listing.nearby)}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏠 <b>Xonalar:</b> {listing.rooms_count} xona\n"
            f"🏢 <b>Qavat:</b> {listing.floor}/{listing.total_floors}-qavat\n"
            f"📐 <b>Maydon:</b> {listing.total_area} m²\n"
            f"🏗️ <b>Uy turi:</b> {listing.get_property_type_display()}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <b>Qo'shimcha:</b> {get_display(listing.amenities)}\n\n"
            f"📅 <b>Ro'yxatdan o'tgan:</b> {listing.registered_at.strftime('%Y-%m-%d')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📞 <b>Telefon:</b> <code>+{listing.owner.phone_number}</code>"
        )

        # Send images with caption first
        images = listing.images.all()
        if images.exists():
            first_image = images.first()
            if first_image and first_image.image:
                try:
                    await update.message.reply_photo(
                        photo=first_image.image.url,
                        caption=message,
                        parse_mode='HTML'
                    )
                    
                    # Send remaining images
                    for image in images[1:]:
                        if image.image:
                            try:
                                await update.message.reply_photo(photo=image.image.url)
                            except Exception as e:
                                logger.error(f"Error sending image: {e}")
                except Exception as e:
                    logger.error(f"Error sending first image: {e}")
                    # Fallback to text message if image fails
                    await update.message.reply_text(message, parse_mode='HTML')
                    
                    # Send all images separately
                    for image in images:
                        if image.image:
                            try:
                                await update.message.reply_photo(photo=image.image.url)
                            except Exception as e:
                                logger.error(f"Error sending image: {e}")
        else:
            await update.message.reply_text(message, parse_mode='HTML')

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
            await query.message.reply_text(f"📞 <b>Telefon raqam:</b> <code>{phone_number}</code>", parse_mode='HTML')

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
