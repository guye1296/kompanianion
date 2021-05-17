import tenbis
import config
import logging
import message_handlers
from telegram.ext import Updater, MessageHandler


class Bot:
    # TODO: terminate session after inactivity
    _tenbis_session = tenbis.Session(config.TENBIS_OFFICE_LOCATION)
    _sessions = {}
    _updater = Updater(token=config.API_TOKEN, use_context=True)

    def __init__(self):
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

