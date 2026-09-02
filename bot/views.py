import os
import io
import logging
from asgiref.sync import sync_to_async
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from django.conf import settings
from listings.models import Listing, ListingImage

logger = logging.getLogger('telegram_bot')


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
            "🏠 <b>Добро пожаловать в бот недвижимости!</b>\n\n"
            "Введите ID объявления, чтобы получить подробную информацию.\n\n"
            "📝 <b>Как использовать:</b>\n"
            "1. Отправьте ID объявления (например: 34858)\n"
            "2. Бот покажет полную информацию и фото\n\n"
            "❓ Нажмите /help для справки"
        )

        await update.message.reply_text(
            welcome_message,
            parse_mode='HTML'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🆘 <b>Справка</b>\n\n"
            "📌 <b>Доступные команды:</b>\n"
            "/start - Начать\n"
            "/help - Справка\n\n"
            "📌 <b>Информация об объекте:</b>\n"
            "Отправьте ID объявления и получите:\n"
            "• Фотографии (сетка)\n"
            "• Район\n"
            "• Количество комнат\n"
            "• Этаж\n"
            "• Площадь\n"
            "• Цена\n"
            "• Номер телефона\n"
            "• Кто добавил объект\n\n"
            "❓ Вопросы? Свяжитесь с администратором"
        )

        await update.message.reply_text(
            help_message,
            parse_mode='HTML'
        )

    @sync_to_async
    def get_listing_by_id(self, listing_id):
        """Get listing by ID from database"""
        try:
            listing = Listing.objects.select_related(
                'district', 'owner', 'created_by'
            ).prefetch_related('images').get(id=listing_id)
            return listing
        except Listing.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return None

    @sync_to_async
    def _read_image_bytes(self, img):
        """Читать файл из Spaces (boto3)"""
        with img.image.open('rb') as f:
            data = f.read()
        bio = io.BytesIO(data)
        bio.name = img.image.name.split('/')[-1] or 'image.jpg'
        return bio

    @staticmethod
    def _get_display(value):
        return value if value else "Не указано"

    def _get_operator_info(self, listing):
        """
        Получить информацию оператора/администратора
        (всегда идёт последней строкой в карточке — рис. образец)
        """
        if not listing.created_by:
            return "👤 <b>Добавил:</b> Не указано"

        user = listing.created_by

        if user.first_name and user.last_name:
            full_name = f"{user.first_name} {user.last_name}"
        elif user.first_name:
            full_name = user.first_name
        else:
            full_name = user.username

        # Если это администратор (проверить по role полю)
        if hasattr(user, 'role') and user.role == 'admin':
            return f"👨‍💼 <b>АДМИНИСТРАТОР:</b> {full_name}"
        else:
            return f"👤 <b>Оператор:</b> {full_name}"

    def build_listing_message(self, listing):
        """
        Собрать текст карточки объявления в стиле образца:
        🔥🔥 Продаётся срочно 🔥🔥
        🏠 ТИП
        📌 Район / Адрес / Ориентир
        ✅ Комнат / Этаж / Этажность / Площадь
        💰 Цена
        📞 Моб
        и в самом конце — кто добавил (оператор/админ)
        """
        get_display = self._get_display

        deal_status = "Продаётся срочно" if listing.deal_type == 'sale' else "Сдаётся срочно"
        property_status = listing.get_property_type_display().upper()

        lines = [
            f"🔥🔥{deal_status}🔥🔥",
            "",
            f"🏠 ТИП- {property_status}",
            "",
            f"📌 Район: {listing.district.name}",
            f"📌 Адрес: {get_display(listing.address)}",
            f"📌 Ориентир: {get_display(listing.nearby)}",
            "",
            f"✅ Комнат- {listing.rooms_count}",
            f"✅ Этаж - {listing.floor}",
            f"✅ Этажность- {listing.total_floors}",
            f"✅ Площадь: {listing.total_area} м²",
        ]

        # Amenities (agar bo'lsa, ✅ uslubida qo'shiladi)
        amenity_lines = [line.strip() for line in (listing.amenities or "").splitlines() if line.strip()]
        if amenity_lines:
            lines.append("")
            lines.append(f"✅ Особенности: {amenity_lines[0]}")
            if len(amenity_lines) > 1:
                lines.append(f"✅ Условия: {', '.join(amenity_lines[1:])}")

        lines += [
            "",
            f"💰 Цена: {listing.price:,.0f}$",
        ]

        if listing.price_per_sqm:
            lines.append(f"💵 {listing.price_per_sqm:,.2f}$/м²")

        phone = listing.owner.phone_number if listing.owner else "Не указано"
        lines += [
            "",
            f"📞 Моб : <code>+{phone}</code>",
            "",
            f"📅 Добавлено: {listing.created_at.strftime('%d.%m.%Y')}",
            "",
            self._get_operator_info(listing),
        ]

        return "\n".join(lines)

    def build_continuation_caption(self, listing, batch_start, batch_end):
        """
        Краткий заголовок для следующих групп фото (2+),
        тот же набор иконок, в конце — оператор/админ
        """
        phone = listing.owner.phone_number if listing.owner else "Не указано"
        operator_info = self._get_operator_info(listing)

        lines = [
            f"🆔 ID {listing.id} — фото ({batch_start}-{batch_end})",
            "",
            f"💰 Цена: {listing.price:,.0f}$",
            f"📌 Район: {listing.district.name}",
            f"📞 Моб : <code>+{phone}</code>",
            "",
            operator_info,
        ]
        return "\n".join(lines)

    async def send_listing_with_images_and_info(self, update: Update, listing):
        """
        Отправить информацию и фото объявления
        """
        images = [img for img in listing.images.all() if img.image]
        text = self.build_listing_message(listing)

        logger.info(f"Listing {listing.id}: найдено {len(images)} фото")

        # Если нет фото, отправить только текст
        if not images:
            await update.message.reply_text(text, parse_mode='HTML')
            return

        # Отправить фото батчами по 10 (лимит Telegram)
        for batch_start in range(0, len(images), 10):
            batch = images[batch_start:batch_start + 10]
            media = []

            for idx, img in enumerate(batch):
                file_bytes = await self._read_image_bytes(img)

                if batch_start == 0 and idx == 0:
                    # Первая фото первой группы -> полная карточка
                    media.append(InputMediaPhoto(
                        media=file_bytes,
                        caption=text,
                        parse_mode='HTML'
                    ))
                elif idx == 0:
                    # Первая фото следующих групп -> краткий заголовок
                    continuation_caption = self.build_continuation_caption(
                        listing, batch_start + 1, batch_start + len(batch)
                    )
                    media.append(InputMediaPhoto(
                        media=file_bytes,
                        caption=continuation_caption,
                        parse_mode='HTML'
                    ))
                else:
                    media.append(InputMediaPhoto(media=file_bytes))

            try:
                await update.message.reply_media_group(media=media)
                logger.info(
                    f"Listing {listing.id}: группа фото отправлена "
                    f"({batch_start + 1}-{batch_start + len(batch)})"
                )
            except Exception as e:
                logger.exception(f"Error sending media group: {e}")
                # Fallback: текст + фото отдельно
                if batch_start == 0:
                    await update.message.reply_text(text, parse_mode='HTML')
                else:
                    continuation_caption = self.build_continuation_caption(
                        listing, batch_start + 1, batch_start + len(batch)
                    )
                    await update.message.reply_text(continuation_caption, parse_mode='HTML')

                for img in batch:
                    try:
                        file_bytes = await self._read_image_bytes(img)
                        await update.message.reply_photo(photo=file_bytes)
                    except Exception as e2:
                        logger.exception(f"Error sending image: {e2}")

    async def handle_listing_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle listing ID input"""
        try:
            listing_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Ошибка!</b> Пожалуйста, введите только номер (например: 34858)",
                parse_mode='HTML'
            )
            return

        listing = await self.get_listing_by_id(listing_id)

        if not listing:
            await update.message.reply_text(
                f"❌ <b>Объявление не найдено!</b> ID: {listing_id}\n\n"
                "Пожалуйста, проверьте ID.\n\n"
                "Если у вас есть вопросы, свяжитесь с администратором.",
                parse_mode='HTML'
            )
            return

        # Фото + Текст = одно сообщение
        await self.send_listing_with_images_and_info(update, listing)

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries (button clicks)"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith('copy_phone_'):
            phone_number = query.data.replace('copy_phone_', '')
            await query.message.reply_text(f"📞 <b>Номер телефона:</b> <code>{phone_number}</code>", parse_mode='HTML')

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