import telebot
import tenbis
import logging


def _read_secret(secret_file_name) -> str:
    try:
        with open(secret_file_name) as key_file:
            return key_file.read()
    except OSError as e:
        raise RuntimeError(str(e))


bot = telebot.TeleBot(_read_secret("api_key.secret"), parse_mode=None)
_tenbis_session = tenbis.Session(_read_secret("office_location.secret"))


class Session:
    """
    A session to a bot given a chat id
    """
    def __init__(self, chat_id):
        self._chat_id = chat_id
        self._next = self._route

    def handle(self, message: telebot.types.Message):
        logging.info(f"{self._chat_id}: {message.text}")
        return self._next(message)

    def _route(self, message: telebot.types.Message):
        if message.text == '/usage':
            return self._usage(message)
        elif message.text == '/start':
            return self._usage(message)
        elif message.text == '/help':
            return self._usage(message)
        elif message.text == '/random':
            return self._random(message)
        elif message.text == '/search':
            return self._prompt_search(message)

    def _send_restaurant_description(self, restaurant: tenbis.Restaurant):
        try:
            bot.send_photo(self._chat_id, photo=restaurant.photo_url, caption=str(restaurant))
        except telebot.apihelper.ApiTelegramException:
            logging.error(f"URL {restaurant.photo_url} not valid :(")
            bot.send_message(self._chat_id, str(restaurant))


    def _prompt_search(self, message: telebot.types.Message):
        bot.send_message(self._chat_id, "Type part of the restaurant to search for...")
        self._next = self._search

    def _search(self, message: telebot.types.Message):
        query = message.text
        result = _tenbis_session.search_restaurant(query)
        if result is None:
            bot.send_message(self._chat_id, f"Could not find any restaurant containing:\t{query}")
        else:
            self._send_restaurant_description(result)

        self._next = self._route

    def _random(self, message: telebot.types.Message):
        choice = _tenbis_session.get_random_restaurant()
        self._send_restaurant_description(choice)

    @staticmethod
    def _usage(self, message: telebot.types.Message):
        bot.reply_to(message, "Usage:\n"
                              "/random : select a random restaurant\n"
                              "/search : search a restaurant\n"
                              "/help | /usage : show this message\n"
                     )


# TODO: terminate session after inactivity
_sessions = {}


@bot.message_handler()
def route_message(message: telebot.types.Message):
    # add to existing list of user sessions
    try:
        session = _sessions[message.chat.id]
    except KeyError:
        logging.info(f"Creating session {message.chat.id}")
        session = Session(message.chat.id)
        _sessions[message.chat.id] = session

    return session.handle(message)
