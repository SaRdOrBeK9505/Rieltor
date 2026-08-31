from django.core.management.base import BaseCommand
from bot.views import start_bot


class Command(BaseCommand):
    help = 'Start Telegram bot'

    def handle(self, *args, **options):
        self.stdout.write('Starting Telegram bot...')
        try:
            start_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Bot stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error starting bot: {e}'))
