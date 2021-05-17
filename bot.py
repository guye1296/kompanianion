import config
import message_handlers
from telegram.ext import Updater


class Bot:
    def __init__(self):
        self._updater = Updater(token=config.API_TOKEN, use_context=True)
        self._updater.dispatcher.add_handler(message_handlers.pick_restaurant_handler())
        self._updater.dispatcher.add_handler(message_handlers.help_handler())

    def run(self):
        self._updater.start_webhook(
            listen=config.WEBHOOK_LISTEN,
            port=config.WEBHOOK_PORT,
            url_path=config.API_TOKEN,
            webhook_url=f"{config.WEBHOOK_URL_BASE}/{config.API_TOKEN}"
        )
        self._updater.idle()

