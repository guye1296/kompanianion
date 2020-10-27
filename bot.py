import telebot
import tenbis


def _read_secret(secret_file_name) -> str:
    try:
        with open(secret_file_name) as key_file:
            return key_file.read()
    except OSError as e:
        raise RuntimeError(str(e))


bot = telebot.TeleBot(_read_secret("api_key.secret"), parse_mode=None)
_session = tenbis.Session(_read_secret("office_location.secret"))


@bot.message_handler(commands=['random'])
def get_random_restaurant(message):
    choice = _session.get_random_restaurant()
    bot.reply_to(message, f"Name:\t{choice.name}\nUrl:\t{choice.url}")


@bot.message_handler(commands=['help', 'start'])
def usage(message):
    bot.reply_to(message, "Usage: `/random`: select a random restaurant")

