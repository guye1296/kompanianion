import logging
from bot import bot


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Kompanianion starting...")
    bot.polling()
